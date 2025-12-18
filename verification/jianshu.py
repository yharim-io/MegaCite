import re
import time
import json
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class JianshuVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for Jianshu login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                main_page = context.new_page()

                try:
                    main_page.goto("https://www.jianshu.com/sign_in")
                    print("[*] Please log in within 120 seconds...")

                    deadline = time.time() + 120
                    while time.time() < deadline:
                        for page in list(context.pages):
                            try:
                                if page.is_closed(): continue
                                url = page.url
                                if "jianshu.com" in url and "sign_in" not in url and "about:blank" not in url and "callback" not in url:
                                    print(f"[*] Detected login success on page: {url}")
                                    page.wait_for_timeout(3000)
                                    cookies = context.cookies()
                                    if cookies:
                                        save_cookies(0, "jianshu", cookies)
                                        print(f"[+] Login successful! Saved {len(cookies)} cookies.")
                                        try: page.close()
                                        except Exception: pass
                                        return True
                            except Exception:
                                pass
                        main_page.wait_for_timeout(500)
                    return False
                finally:
                    try: context.close(); browser.close()
                    except Exception: pass
        except Exception:
            return False

    def check_ownership(self, url: str, user_id: int) -> bool:
        cookies_list = load_cookies(user_id, "jianshu")
        if not cookies_list: return False
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                context.add_cookies(cookies_list)
                page = context.new_page()
                try:
                    page.goto("https://www.jianshu.com/writer", timeout=20000)
                    page.wait_for_load_state("domcontentloaded")
                    if "sign_in" in page.url: return False
                        
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(2000)

                    if page.locator('a:has-text("编辑文章")').count() > 0: return True
                    if page.locator('a[href*="/writer#/notebooks"]').count() > 0: return True

                    next_data_loc = page.locator('#__NEXT_DATA__')
                    if next_data_loc.count() > 0:
                        try:
                            json_text = next_data_loc.first.inner_text()
                            data = json.loads(json_text)
                            note_id = data.get('props', {}).get('pageProps', {}).get('note', {}).get('id')
                            if note_id:
                                api_url = f"https://www.jianshu.com/author/notes/{note_id}/content"
                                if context.request.get(api_url).status == 200: return True
                        except Exception: pass
                    return False
                finally:
                    browser.close()
        except Exception:
            return False