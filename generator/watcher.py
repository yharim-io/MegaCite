import time
from dao.factory import create_connection
from dao.reference_dao import MySQLPostReferenceDAO
from generator.builder import StaticSiteGenerator

class DBWatcher:
    """
    后台轮询监听器。
    """
    def __init__(self, generator: StaticSiteGenerator):
        self.gen = generator
        self.running = False
        self._snapshot = {} 

    def _get_current_state(self):
        state = {}
        conn = create_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT cid, owner_id, title, context, description, date, category FROM posts")
                rows = cur.fetchall()
                for r in rows:
                    cid, owner_id = r[0], r[1]
                    data_map = {
                        "cid": cid, "owner_id": owner_id, 
                        "title": r[2], "context": r[3], 
                        "description": r[4], "date": str(r[5]), 
                        "category": r[6]
                    }
                    # 简单哈希签名用于检测变更
                    sig = hash(tuple(data_map.values()))
                    state[cid] = {"owner_id": owner_id, "data": data_map, "signature": sig}
        finally:
            conn.close()
        return state

    def _get_username(self, user_id):
        conn = create_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
                row = cur.fetchone()
                return row[0] if row else "unknown"
        finally:
            conn.close()

    def _scan(self):
        new_state = self._get_current_state()
        
        # 待更新任务集合：cid -> info
        tasks = {}
        affected_users = set()

        # 1. 扫描变更
        for cid, info in new_state.items():
            old_info = self._snapshot.get(cid)
            
            # 检测到直接变更 (新增 或 内容变化)
            if not old_info or old_info["signature"] != info["signature"]:
                tasks[cid] = info
                
                # --- 级联更新逻辑 ---
                if old_info:
                    old_data = old_info["data"]
                    new_data = info["data"]
                    if old_data["title"] != new_data["title"] or old_data["category"] != new_data["category"]:
                        print(f"[Watcher] Cascade Trigger: {cid} changed URL structure.")
                        conn = create_connection()
                        try:
                            ref_dao = MySQLPostReferenceDAO(conn)
                            referencing_cids = ref_dao.get_referencing_posts(cid)
                            
                            for ref_cid in referencing_cids:
                                if ref_cid in new_state and ref_cid not in tasks:
                                    print(f"[Watcher] Cascade Update: Adding {ref_cid} to tasks.")
                                    tasks[ref_cid] = new_state[ref_cid]
                        finally:
                            conn.close()

        # 2. 扫描删除 (物理删除 + 内存映射清理)
        for cid, info in self._snapshot.items():
            if cid not in new_state:
                self.gen.remove_post_file(cid)
                affected_users.add(info["owner_id"])

        # 2.5 [新增] 清理旧文件
        # 在更新 URL 映射之前，必须先根据旧的元数据删除旧文件。
        # 否则一旦映射更新，就找不到旧文件的路径了。
        if tasks:
            for cid in tasks:
                # 只处理更新的情况 (old -> new)，新增文章没有旧文件
                if cid in self._snapshot:
                    old_data = self._snapshot[cid]["data"]
                    new_data = tasks[cid]["data"]
                    
                    old_title = old_data.get("title", "untitled")
                    old_cat = old_data.get("category", "default")
                    new_title = new_data.get("title", "untitled")
                    new_cat = new_data.get("category", "default")

                    # 只有当路径关键信息变更时才执行物理删除
                    if old_title != new_title or old_cat != new_cat:
                        username = self._get_username(self._snapshot[cid]["owner_id"])
                        self.gen.remove_post_file_by_meta(username, old_cat, old_title)

        # 3. 预先更新所有变更文章的 URL 映射 (解决时序问题)
        if tasks:
            print(f"[Watcher] Pre-updating URL mappings for {len(tasks)} tasks...")
            for cid, info in tasks.items():
                username = self._get_username(info["owner_id"])
                data = info["data"]
                self.gen.url_mgr.register_mapping(
                    data["cid"], 
                    username, 
                    data.get("category", "default"), 
                    data.get("title", "untitled")
                )

        # 4. 执行生成 (覆盖写入新文件)
        for cid, info in tasks.items():
            username = self._get_username(info["owner_id"])
            self.gen.sync_post_file(info["data"], username)
            affected_users.add(info["owner_id"])

        # 5. 更新索引
        for uid in affected_users:
            self.gen.sync_user_index(uid)

        self._snapshot = new_state

    def start(self, interval=3):
        self.gen.init_output_dir()
        self.running = True
        print(f"[*] DB Watcher started. Polling every {interval}s...")
        while self.running:
            try:
                self._scan()
            except Exception as e:
                print(f"[Watcher Error] {e}")
            time.sleep(interval)

    def stop(self):
        self.running = False