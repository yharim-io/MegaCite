#!/usr/bin/env python3
"""
本地验证客户端 - 在用户本地启动浏览器进行第三方平台登录
启动方式：python -m verification.local_client <session_id> <platform>
"""
import sys
import time
import requests
import argparse
from typing import Optional
from pathlib import Path
from playwright.sync_api import sync_playwright

# 平台配置
PLATFORM_URLS = {
    'csdn': 'https://passport.csdn.net/login',
    'yuque': 'https://www.yuque.com/login',
    'jianshu': 'https://www.jianshu.com/sign_in',
    'juejin': 'https://juejin.cn/user/login',
    'cnblogs': 'https://account.cnblogs.com/signin',
}

PLATFORM_SUCCESS_CHECKS = {
    'csdn': lambda url: 'passport.csdn.net' not in url,
    'yuque': lambda url: 'login' not in url and 'yuque.com' in url,
    'jianshu': lambda url: 'jianshu.com' in url and 'sign_in' not in url,
    'juejin': lambda url: 'juejin.cn' in url,
    'cnblogs': lambda url: 'cnblogs.com' in url and 'signin' not in url,
}

PLATFORM_EXTRA_ACTIONS = {
    'csdn': lambda page: page.goto("https://www.csdn.net") if page else None,
}


class LocalVerificationClient:
    """本地验证客户端"""
    
    def __init__(self, session_id: str, platform: str, server_url: str = "http://localhost:8000"):
        self.session_id = session_id
        self.platform = platform.lower()
        self.server_url = server_url
        self.login_url = PLATFORM_URLS.get(platform.lower())
        
        if not self.login_url:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def run(self) -> bool:
        """启动浏览器进行验证"""
        print(f"[*] Starting verification for {self.platform}...")
        print(f"[*] Session ID: {self.session_id}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                
                try:
                    # 打开登录页面
                    print(f"[*] Opening {self.login_url}...")
                    page.goto(self.login_url)
                    print("[*] Please log in within 180 seconds...")
                    
                    # 等待登录成功
                    timeout_ms = 180000
                    wait_func = PLATFORM_SUCCESS_CHECKS.get(self.platform)
                    
                    if wait_func:
                        page.wait_for_url(wait_func, timeout=timeout_ms)
                    else:
                        # 默认等待 URL 变化
                        page.wait_for_load_state("networkidle", timeout=timeout_ms)
                    
                    print("[*] Login detected!")
                    
                    # 执行平台特定的额外操作（如同步 Cookie）
                    extra_action = PLATFORM_EXTRA_ACTIONS.get(self.platform)
                    if extra_action:
                        print("[*] Performing platform-specific actions...")
                        extra_action(page)
                        page.wait_for_load_state("networkidle")
                    
                    time.sleep(2)
                    
                    # 获取 Cookies
                    cookies = context.cookies()
                    if cookies:
                        print(f"[+] Captured {len(cookies)} cookies")
                        
                        # 发送 Cookies 到服务器
                        if self._send_cookies_to_server(cookies):
                            print(f"[+] Cookies sent successfully!")
                            return True
                        else:
                            print("[-] Failed to send cookies to server")
                            return False
                    else:
                        print("[-] No cookies found after login")
                        return False
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"[-] Login failed: {error_msg}")
                    self._report_error_to_server(error_msg)
                    return False
                finally:
                    browser.close()
        
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                print("[-] Error: Playwright browsers are not installed.")
                print("[-] Please run: playwright install")
            else:
                print(f"[-] Client error: {e}")
            return False
    
    def _send_cookies_to_server(self, cookies: list) -> bool:
        """将 Cookies 发送到服务器"""
        try:
            url = f"{self.server_url}/api/auth/save_cookies"
            payload = {
                "session_id": self.session_id,
                "cookies": cookies,
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"[-] Failed to send cookies: {e}")
            return False
    
    def _report_error_to_server(self, error_msg: str) -> bool:
        """报告错误到服务器"""
        try:
            url = f"{self.server_url}/api/auth/save_error"
            payload = {
                "session_id": self.session_id,
                "error": error_msg,
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"[-] Failed to report error: {e}")
            return False


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="MegaCite Local Verification Client",
        epilog="启动本地浏览器进行第三方平台验证"
    )
    parser.add_argument('session_id', help='验证会话 ID')
    parser.add_argument('platform', help='平台名称 (csdn, yuque, jianshu, juejin, cnblogs)')
    parser.add_argument('--server', default='http://localhost:8000', 
                       help='服务器地址 (默认: http://localhost:8000)')
    
    args = parser.parse_args()
    
    try:
        client = LocalVerificationClient(args.session_id, args.platform, args.server)
        success = client.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
