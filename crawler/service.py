from datetime import date
from core.auth import verify_token
from core.post import post_create, post_update
from crawler.fetcher import fetch_html
from crawler.converter import convert_html_to_markdown
from verification import manager as verify_manager

def migrate_post_from_url(token: str, url: str, progress_callback=None) -> str:
    def report(msg):
        print(msg)
        if progress_callback: progress_callback(msg)

    # 1. 先验证 Token 获取 User ID (用于加载隔离的 Cookie)
    user_id = verify_token(token)

    # 2. 执行所有权验证
    report(f"[*] Verifying ownership for {url}...")
    if not verify_manager.verify_url_owner(url, user_id):
        raise PermissionError(
            "Ownership verification failed.\n"
            "Possible reasons:\n"
            "  1. You are not the author of this post.\n"
            "  2. Your local cookie has expired (Try re-binding in Settings).\n"
            "  3. Platform protection blocked the probe."
        )
    report(f"[+] Ownership confirmed.")

    # 3. 获取源码
    report(f"[*] Fetching content from {url}...")
    # [修复] 传递 user_id
    html = fetch_html(url, user_id)
    if not html:
        raise ValueError("Failed to fetch content.")

    # 4. AI 转换
    report(f"[*] Analyzing and converting with AI...")
    data = convert_html_to_markdown(html)
    report(f"[+] Content converted successfully.")

    # 5. 创建文章
    report(f"[*] Creating post in database...")
    cid = post_create(token)
    
    # 6. 更新字段
    try:
        title = data.get("title", f"Imported-{cid}")
        cat = "Imported"
        desc = data.get("description", "Imported from URL")
        dt = str(date.today())
        context = data.get("context", "")

        post_update(token, cid, "title", title)
        post_update(token, cid, "category", cat)
        post_update(token, cid, "description", desc)
        post_update(token, cid, "date", dt)
        post_update(token, cid, "context", context)
        
        report(f"[+] Migration complete! CID: {cid}")
        return cid
    except Exception as e:
        report(f"[-] Warning: Partial update failed: {e}")
        return cid