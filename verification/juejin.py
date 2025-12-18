import re
import time
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class JuejinVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for Juejin login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                main_page = context.new_page()
                try:
                    main_page.goto("https://juejin.cn/login")
                    print("[*] Please log in within 120 seconds...")
                    deadline = time.time() + 120
                    while time.time() < deadline:
                        for page in list(context.pages):
                            try:
                                if page.is_closed(): continue
                                url = page.url
                                if "juejin.cn" in url and "login" not in url:
                                    cookies = context.cookies()
                                    if any(c['name'] == 'sessionid' for c in cookies):
                                        page.wait_for_timeout(2000)
                                        save_cookies(0, "juejin", context.cookies())
                                        try: page.close()
                                        except Exception: pass
                                        return True
                            except Exception: pass
                        main_page.wait_for_timeout(500)
                    return False
                finally:
                    try: context.close(); browser.close()
                    except Exception: pass
        except Exception: return False

    def check_ownership(self, url: str, user_id: int) -> bool:
        cookies_list = load_cookies(user_id, "juejin")
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
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    if page.locator(".login-button").is_visible(): return False

                    ids = page.evaluate("""() => {
                        try {
                            if (window.__NUXT__ && window.__NUXT__.state) {
                                const state = window.__NUXT__.state;
                                let currentUserId = state.user?.authUser?.user_id || state.auth?.user?.user_id;
                                let authorId = state.view?.column?.entry?.author_user_info?.user_id || state.view?.content?.author_user_info?.user_id;
                                return { current: currentUserId, author: authorId };
                            }
                        } catch (e) {}
                        return {};
                    }""")
                    
                    c_uid, a_uid = str(ids.get('current', '')), str(ids.get('author', ''))
                    if c_uid and a_uid and c_uid != 'None' and a_uid != 'None':
                        return c_uid == a_uid

                    if page.locator(".edit-btn").is_visible() or page.locator("a:has-text('编辑')").count() > 0:
                        return True
                    return False
                finally:
                    browser.close()
        except Exception: return False