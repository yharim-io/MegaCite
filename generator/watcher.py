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
            # [新增] 包含 is_public
            with conn.cursor() as cur:
                cur.execute("SELECT cid, owner_id, title, context, description, date, category, is_public FROM posts")
                rows = cur.fetchall()
                for r in rows:
                    cid, owner_id = r[0], r[1]
                    data_map = {
                        "cid": cid, "owner_id": owner_id, 
                        "title": r[2], "context": r[3], 
                        "description": r[4], "date": str(r[5]), 
                        "category": r[6], "is_public": bool(r[7])
                    }
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
        
        tasks = {}
        affected_users = set()

        for cid, info in new_state.items():
            old_info = self._snapshot.get(cid)
            
            if not old_info or old_info["signature"] != info["signature"]:
                tasks[cid] = info
                
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

        for cid, info in self._snapshot.items():
            if cid not in new_state:
                self.gen.remove_post_file(cid)
                affected_users.add(info["owner_id"])

        if tasks:
            for cid in tasks:
                if cid in self._snapshot:
                    old_data = self._snapshot[cid]["data"]
                    new_data = tasks[cid]["data"]
                    
                    old_title = old_data.get("title", "untitled")
                    old_cat = old_data.get("category", "default")
                    new_title = new_data.get("title", "untitled")
                    new_cat = new_data.get("category", "default")

                    if old_title != new_title or old_cat != new_cat:
                        username = self._get_username(self._snapshot[cid]["owner_id"])
                        self.gen.remove_post_file_by_meta(username, old_cat, old_title)

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

        for cid, info in tasks.items():
            username = self._get_username(info["owner_id"])
            self.gen.sync_post_file(info["data"], username)
            affected_users.add(info["owner_id"])

        for uid in affected_users:
            self.gen.sync_user_index(uid)

        # [新增] 只要有变动，就尝试更新广场 (简单粗暴策略)
        if tasks or affected_users:
            self.gen.sync_playground()

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