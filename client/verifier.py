"""
MegaCite 客户端应用 - 独立可执行程序
在本地启动 HTTP 服务器，监听来自远程服务器的验证请求
启动: python client/verifier.py --server http://remote-server.com:8000 --port 9999
"""
import sys
import os
import json
import threading
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verification import manager as verify_manager
from client.cookie_store import load_cookies


class VerificationHandler(BaseHTTPRequestHandler):
    """处理来自远程服务器的验证请求"""
    
    # 共享的服务器实例引用
    app_server = None

    def _send_cors_headers(self):
        """发送 CORS 响应头，允许浏览器跨域访问"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/verify':
            self._handle_verify()
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
    
    def _handle_verify(self):
        """处理验证请求"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            session_id = data.get('session_id')
            platform = data.get('platform')
            server_url = data.get('server_url', 'http://localhost:8000')
            
            if not session_id or not platform:
                self.send_response(400)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Missing session_id or platform"}).encode())
                return
            
            print(f"[*] Received verification request")
            print(f"    Session ID: {session_id}")
            print(f"    Platform: {platform}")
            print(f"    Server: {server_url}")
            
            # 在后台线程执行验证
            thread = threading.Thread(
                target=self._execute_verification,
                args=(session_id, platform, server_url),
                daemon=True
            )
            thread.start()
            
            # 立即返回响应
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode())
        
        except Exception as e:
            print(f"[-] Error handling verify request: {e}")
            self.send_response(500)
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
    
    @staticmethod
    def _execute_verification(session_id: str, platform: str, server_url: str):
        """执行验证流程（在后台线程中运行）"""
        try:
            platform = platform.lower()
            print(f"\n[*] Starting verification for {platform}")
            
            # 使用已有的验证器登录
            print(f"[*] Launching browser for {platform}...")
            if not verify_manager.login_platform(platform):
                print(f"[-] Login failed for {platform}")
                VerificationHandler._report_error(session_id, server_url, "Login failed")
                return
            
            print(f"[+] Login successful for {platform}")
            
            # [关键修复] 获取本地保存的 Cookies，本地客户端默认 User ID 为 0
            cookies = load_cookies(0, platform)
            
            if not cookies:
                print(f"[-] No cookies found after login")
                VerificationHandler._report_error(session_id, server_url, "No cookies found")
                return
            
            print(f"[+] Loaded {len(cookies)} cookies")
            
            # 发送 Cookies 到远程服务器
            VerificationHandler._send_cookies(session_id, cookies, server_url)
        
        except Exception as e:
            print(f"[-] Verification error: {e}")
            VerificationHandler._report_error(session_id, server_url, str(e))
    
    @staticmethod
    def _send_cookies(session_id: str, cookies: list, server_url: str):
        """发送 Cookies 到远程服务器"""
        try:
            url = f"{server_url.rstrip('/')}/api/auth/save_cookies"
            payload = {
                "session_id": session_id,
                "cookies": cookies,
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"[+] Cookies sent successfully to {server_url}")
            else:
                print(f"[-] Server returned {response.status_code}")
                VerificationHandler._report_error(session_id, server_url, f"Server returned {response.status_code}")
        except Exception as e:
            print(f"[-] Failed to send cookies: {e}")
            VerificationHandler._report_error(session_id, server_url, f"Send cookies failed: {str(e)}")
    
    @staticmethod
    def _report_error(session_id: str, server_url: str, error_msg: str):
        """报告错误到远程服务器"""
        try:
            url = f"{server_url.rstrip('/')}/api/auth/save_error"
            payload = {
                "session_id": session_id,
                "error": error_msg,
            }
            requests.post(url, json=payload, timeout=10)
            print(f"[+] Error reported to server")
        except Exception as e:
            print(f"[-] Failed to report error: {e}")
    
    def log_message(self, format, *args):
        """抑制默认的请求日志"""
        return


class VerificationServer:
    """本地验证服务器"""
    
    def __init__(self, host='127.0.0.1', port=9999, server_url='http://localhost:8000'):
        self.host = host
        self.port = port
        self.server_url = server_url
        self.http_server = None
        self.thread = None
    
    def start(self):
        """启动服务器"""
        VerificationHandler.app_server = self
        self.http_server = HTTPServer((self.host, self.port), VerificationHandler)
        
        print(f"\n{'='*60}")
        print(f"MegaCite Client Verifier")
        print(f"{'='*60}")
        print(f"[+] Starting HTTP server on {self.host}:{self.port}")
        print(f"[+] Remote server: {self.server_url}")
        print(f"[+] Listening for verification requests...")
        print(f"{'='*60}\n")
        
        # 在后台线程运行
        self.thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止服务器"""
        if self.http_server:
            self.http_server.shutdown()
            print("[*] Server stopped")
    
    def join(self):
        """等待服务器线程"""
        if self.thread:
            self.thread.join()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="MegaCite Client Verifier - 客户端应用程序",
        prog="python client/verifier.py"
    )
    parser.add_argument(
        '--server',
        default='http://localhost:8000',
        help='远程服务器地址 (默认: http://localhost:8000)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9999,
        help='本地监听端口 (默认: 9999)'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='本地监听地址 (默认: 127.0.0.1)'
    )
    
    args = parser.parse_args()
    
    try:
        server = VerificationServer(
            host=args.host,
            port=args.port,
            server_url=args.server
        )
        server.start()
        server.join()  # 永久运行
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        server.stop()
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()