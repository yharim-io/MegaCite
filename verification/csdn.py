import re
import time
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class CSDNVerifier(PlatformVerifier):
    def login(self) -> bool:
        # 仅本地客户端使用，无需 user_id
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                page.goto("https://passport.csdn.net/login")
                page.wait_for_url(lambda u: "passport.csdn.net" not in u, timeout=120000)
                page.goto("https://www.csdn.net")
                page.wait_for_load_state("networkidle")
                cookies = context.cookies()
                
                # [修复] 必须将 Cookie 保存到本地，verifier 客户端才能读取到
                # 本地客户端默认使用 user_id=0
                if cookies:
                    save_cookies(0, "csdn", cookies)
                
                browser.close()
                return cookies
        except Exception as e:
            print(f"[-] Login failed: {e}")
            return False

    def check_ownership(self, url: str, user_id: int) -> bool:
        # [修改] 使用 user_id 加载 Cookie
        cookies_list = load_cookies(user_id, "csdn")
        if not cookies_list:
            print("[-] No CSDN cookies found.")
            return False

        match = re.search(r"/article/details/(\d+)", url)
        if not match: return False
        article_id = match.group(1)
        probe_url = f"https://editor.csdn.net/md/?articleId={article_id}"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                context.add_cookies(cookies_list)
                page = context.new_page()
                page.goto(probe_url, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2) 
                final_url = page.url
                browser.close()
                
                if "editor.csdn.net" in final_url or "mp.csdn.net" in final_url:
                    if "passport.csdn.net" not in final_url:
                        return True
                return False
        except Exception as e:
            print(f"[-] Probe failed: {e}")
            return False