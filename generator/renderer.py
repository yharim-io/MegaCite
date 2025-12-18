import os
import markdown
from core.url_manager import URLManager
from generator.markdown_extensions import CiteReferenceExtension
from generator.content_updater import update_post_content_in_db, update_post_references_in_db

class HTMLRenderer:
    """渲染 HTML 内容 - VitePress 风格"""

    def __init__(self):
        self.url_mgr = URLManager()
        
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        template_dir = os.path.join(project_root, "templates")

        # 加载基础模版
        with open(os.path.join(template_dir, "base.html"), "r", encoding="utf-8") as f:
            self.template_base = f.read()

        # 加载模版片段
        with open(os.path.join(template_dir, "index.html"), "r", encoding="utf-8") as f:
            self.template_index = f.read()
    
        with open(os.path.join(template_dir, "post.html"), "r", encoding="utf-8") as f:
            self.template_post = f.read()

        home_path = os.path.join(template_dir, "home.html")
        if os.path.exists(home_path):
            with open(home_path, "r", encoding="utf-8") as f:
                self.template_home = f.read()
        else:
            self.template_home = "<main><h1>Welcome</h1></main>"

        settings_path = os.path.join(template_dir, "settings.html")
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                self.template_settings = f.read()
        else:
            self.template_settings = "<main><h1>Settings</h1></main>"

        editor_path = os.path.join(template_dir, "editor.html")
        if os.path.exists(editor_path):
            with open(editor_path, "r", encoding="utf-8") as f:
                self.template_editor = f.read()
        else:
            self.template_editor = "<h1>Editor Template Missing</h1>"

    def _render_full(self, 
                     content: str, 
                     page_title: str, 
                     nav_console_active: str = "",
                     nav_settings_active: str = "",
                     meta_extra: str = "",
                     modal_extra: str = "") -> str:
        """
        组装最终页面
        """
        return self.template_base.format(
            content=content,
            page_title=page_title,
            nav_console_active=nav_console_active,
            nav_settings_active=nav_settings_active,
            meta_extra=meta_extra,
            modal_extra=modal_extra
        )

    def render_landing_page(self) -> str:
        # 首页：MegaCite - 构建你的数字花园
        return self._render_full(
            content=self.template_home,
            page_title="MegaCite - 构建你的数字花园"
        )

    def render_settings_page(self) -> str:
        return self._render_full(
            content=self.template_settings,
            page_title="用户设置",
            nav_settings_active="active"
        )
        
    def render_editor_page(self) -> str:
        return self.template_editor

    def render_admin_stub(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Admin Dashboard</title><link href="/style.css" rel="stylesheet"></head>
        <body style="padding: 40px; text-align:center;">
            <h1>Admin Dashboard</h1>
            <p>Welcome, Admin.</p>
            <a href="/" class="action-btn brand">Back Home</a>
        </body>
        </html>
        """

    def render_user_index(self, username: str, categorized_posts: dict) -> str:
        parts = []
        for category in sorted(categorized_posts.keys()):
            posts = categorized_posts[category]
            items = []
            for p in posts:
                item_html = f"""
                <div class="post-item-container">
                    <a href="{p['filename']}" class="post-item-link">
                        <div class="post-item-title">{p['title']}</div>
                        <div class="post-item-meta">
                            <span>{p['date']}</span>
                        </div>
                    </a>
                    <button class="btn-delete-post" data-cid="{p['cid']}" title="删除文章" style="display:none;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
                """
                items.append(item_html)
            
            list_html = "\n".join(items) if items else "<div class='grey-text'>暂无内容</div>"
            
            section_html = f"""
            <div class="section">
                <h3 class="post-section-title">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-folder"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    {category}
                </h3>
                <div class="post-list">
                    {list_html}
                </div>
            </div>
            """
            parts.append(section_html)
        
        content_list_html = "\n".join(parts) or "<p style='text-align:center;color:var(--vp-c-text-3)'>空空如也</p>"

        fragment_html = self.template_index.format(
            username=username,
            content_list=content_list_html
        )

        return self._render_full(
            content=fragment_html,
            page_title=f"{username} 的知识库",
            nav_console_active="active",
            meta_extra=f'<meta name="page-owner" content="{username}">',
            modal_extra=""
        )

    def render_post(self, post_data: dict, author_name: str, cid: str) -> str:
        raw_content = str(post_data.get("context", "") or "")
        desc_text = post_data.get("description", "")
        
        if desc_text and desc_text.strip():
            description_html = f"""
            <div class="custom-block info">
                <p class="custom-block-title">摘要</p>
                <p>{desc_text}</p>
            </div>
            """
        else:
            description_html = ""
        
        found_refs = set()
        def processor_callback(old_str, new_str, target_cid):
            if target_cid: found_refs.add(target_cid)
            if old_str and new_str:
                update_post_content_in_db(cid, old_str, new_str)

        md = markdown.Markdown(extensions=[
            'fenced_code', 'tables', 'toc',
            CiteReferenceExtension(url_mgr=self.url_mgr, db_callback=processor_callback)
        ])
        content = md.convert(raw_content)

        update_post_references_in_db(cid, found_refs)
        
        title = post_data.get("title", "Untitled")
        
        fragment_html = self.template_post.format(
            title=title,
            date=post_data.get("date", ""),
            author=author_name,
            category=post_data.get("category", "default") or "default",
            cid=cid,
            content_body=content,
            description_block=description_html
        )
        
        return self._render_full(
            content=fragment_html,
            page_title=f"{title} - {author_name}",
            meta_extra=f'<meta name="post-cid" content="{cid}">\n<meta name="post-author" content="{author_name}">'
        )