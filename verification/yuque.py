import time
from playwright.sync_api import sync_playwright
from client.cookie_store import load_cookies, save_cookies
from verification.interface import PlatformVerifier

class YuqueVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for Yuque login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                try:
                    page.goto("https://www.yuque.com/login")
                    print("[*] Please log in within 120 seconds...")
                    page.wait_for_url(lambda u: "login" not in u and "yuque.com" in u, timeout=120000)
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)

                    cookies = context.cookies()
                    if cookies:
                        # 本地客户端登录，默认 user_id=0
                        save_cookies(0, "yuque", cookies)
                        print(f"[+] Login successful! Saved {len(cookies)} cookies.")
                        return True
                    return False
                finally:
                    browser.close()
        except Exception as e:
            print(f"[-] Login failed: {e}")
            return False

    def check_ownership(self, url: str, user_id: int) -> bool:
        cookies_list = load_cookies(user_id, "yuque")
        if not cookies_list:
            return False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                context.add_cookies(cookies_list)
                page = context.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(2000)

                if page.locator('button:has-text("编辑")').count() > 0 or \
                   page.locator('a:has-text("编辑")').count() > 0 or \
                   page.locator('[aria-label="编辑"]').count() > 0:
                    browser.close()
                    return True
                
                browser.close()
                return False
        except Exception:
            return False