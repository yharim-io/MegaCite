import re
import time
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class CNBlogsVerifier(PlatformVerifier):
    def login(self) -> bool:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                try:
                    page.goto("https://account.cnblogs.com/signin")
                    page.wait_for_url(lambda u: "account.cnblogs.com/signin" not in u and "cnblogs.com" in u, timeout=120000)
                    page.goto("https://www.cnblogs.com/")
                    time.sleep(2) 
                    cookies = context.cookies()
                    if cookies:
                        save_cookies(0, "cnblogs", cookies)
                        return True
                    return False
                finally:
                    browser.close()
        except Exception: return False

    def check_ownership(self, url: str, user_id: int) -> bool:
        cookies_list = load_cookies(user_id, "cnblogs")
        if not cookies_list: return False
        
        match = re.search(r"/p/(\d+)", url)
        if not match: match = re.search(r"(\d+)(?:\.html)?$", url)
        if not match: return False
        post_id = match.group(1)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                context.add_cookies(cookies_list)
                page = context.new_page()
                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    is_owner = page.evaluate("() => { return typeof isBlogOwner !== 'undefined' && isBlogOwner === true; }")
                    if is_owner: return True
                    
                    if page.locator(f'a[href*="postid={post_id}"]').count() > 0:
                        return True
                    return False
                finally:
                    browser.close()
        except Exception: return False