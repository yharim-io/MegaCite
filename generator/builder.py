import os
import shutil
from collections import defaultdict
from core.url_manager import URLManager
from generator.renderer import HTMLRenderer
from dao.factory import create_connection

class StaticSiteGenerator:
    def __init__(self, base_dir="public"):
        self.base_dir = base_dir
        self.url_mgr = URLManager()
        self.renderer = HTMLRenderer()

    def init_output_dir(self):
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
            print(f"[Gen] Cleaned output directory: {self.base_dir}")
            
        os.makedirs(self.base_dir)
            
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        assets_dir = os.path.join(project_root, "assets")
        
        if os.path.exists(assets_dir):
            try:
                shutil.copytree(assets_dir, self.base_dir, dirs_exist_ok=True)
                print(f"[Gen] Assets copied from {assets_dir}")
            except Exception as e:
                print(f"[Gen] Error copying assets: {e}")
        else:
            print(f"[Warning] Assets directory not found: {assets_dir}")

        self.sync_landing_page()
        self.sync_static_pages()

    def sync_landing_page(self):
        html = self.renderer.render_landing_page()
        path = self._get_abs_path("index.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Gen] Landing Page generated: {path}")

    def sync_static_pages(self):
        # Settings
        html = self.renderer.render_settings_page()
        path = self._get_abs_path("settings.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
            
        # [新增] Editor
        html_editor = self.renderer.render_editor_page()
        path_editor = self._get_abs_path("edit.html")
        with open(path_editor, "w", encoding="utf-8") as f:
            f.write(html_editor)
            
        # Admin stub
        admin_dir = self._get_abs_path("admin")
        os.makedirs(admin_dir, exist_ok=True)
        html_admin = self.renderer.render_admin_stub()
        with open(os.path.join(admin_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_admin)

    def _get_abs_path(self, rel_path: str) -> str:
        return os.path.join(self.base_dir, rel_path)

    def remove_post_file_by_meta(self, username: str, category: str, title: str):
        s_cat = self.url_mgr.safe_title(category or "default")
        s_title = self.url_mgr.safe_title(title or "untitled")
        rel_prefix = f"{username}/{s_cat}/{s_title}"
        full_path = self._get_abs_path(rel_prefix + ".html")
        
        if os.path.exists(full_path):
            os.remove(full_path)
            try:
                parent_dir = os.path.dirname(full_path)
                if not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except OSError:
                pass

    def sync_post_file(self, post_data: dict, author_name: str):
        cid = post_data["cid"]
        title = post_data["title"] or "untitled"
        category = post_data.get("category") or "default"
        
        rel_prefix = self.url_mgr.register_mapping(cid, author_name, category, title)
        filename = rel_prefix + ".html"
        full_path = self._get_abs_path(filename)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        html = self.renderer.render_post(post_data, author_name, cid)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"[Gen] Generated: {full_path}")

    def sync_user_index(self, user_id: int):
        conn = create_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
                row = cur.fetchone()
                if not row: return
                username = row[0]

            with conn.cursor() as cur:
                cur.execute("SELECT cid, title, category, date FROM posts WHERE owner_id=%s ORDER BY date DESC", (user_id,))
                rows = cur.fetchall()

            categorized = defaultdict(list)
            for r in rows:
                p_cid, p_title = r[0], r[1] or "untitled"
                p_cat = r[2] or "default"
                p_date = r[3]
                
                rel_prefix = self.url_mgr.register_mapping(p_cid, username, p_cat, p_title)
                link_href = f"/{rel_prefix}.html"
                
                categorized[p_cat].append({
                    "cid": p_cid,
                    "title": p_title, 
                    "filename": link_href,
                    "date": str(p_date)
                })
            
            html = self.renderer.render_user_index(username, categorized)
            index_path = self._get_abs_path(f"{username}/index.html")
            
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            print(f"[Gen] Index Updated: {index_path}")

        finally:
            conn.close()

    def remove_post_file(self, cid: str):
        rel_prefix = self.url_mgr.remove_mapping(cid)
        if rel_prefix:
            full_path = self._get_abs_path(rel_prefix + ".html")
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"[Gen] Deleted: {full_path}")
            
            # 尝试清理空目录
            try:
                parent_dir = os.path.dirname(full_path)
                if not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except OSError:
                pass