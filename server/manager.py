import socketserver
import http.server
import http.cookies
import os
import threading
import json
import urllib.parse
from generator.builder import StaticSiteGenerator
from generator.watcher import DBWatcher
from dao.factory import create_connection
from core.auth import verify_token
from verification import manager as verify_manager

# 导入新的 Handler
from server.api.auth_handler import handle_auth_routes
from server.api.post_handler import handle_post_routes
from server.api.handlers.interact import handle_interact_routes

PID_FILE = "server.pid"
WEB_ROOT = "public"

SERVER_GEN = None

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.abspath(WEB_ROOT), **kwargs)
    
    def log_message(self, format, *args):
        pass 

    def _check_auth_cookie(self):
        if "Cookie" not in self.headers: return False
        try:
            cookie = http.cookies.SimpleCookie(self.headers["Cookie"])
            if "mc_token" in cookie:
                verify_token(cookie["mc_token"].value)
                return True
        except Exception: pass
        return False

    def do_GET(self):
        # 页面访问权限控制
        if self.path.startswith('/settings.html') or self.path.startswith('/edit.html'):
            if not self._check_auth_cookie():
                self.send_error(404, "Not Found")
                return
        
        # SSE 连接特殊处理
        if self.path.startswith('/api/auth/watch'):
            try:
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                session_id = query.get('session_id', [None])[0]
                if not session_id:
                    self.send_error(400, "Missing session_id")
                    return

                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                status = verify_manager.session_wait(session_id, timeout=120)
                payload = json.dumps(status)
                self.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                self.wfile.flush()
                return
            except Exception as e:
                print(f"SSE Error: {e}")
                return

        # 路由分发
        if handle_auth_routes(self, self.path, "GET", {}, SERVER_GEN): return
        if handle_post_routes(self, self.path, "GET", {}, SERVER_GEN): return
        if handle_interact_routes(self, self.path, "GET", {}, SERVER_GEN): return
        
        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body) if body else {}
            
            # 路由分发
            if handle_auth_routes(self, self.path, "POST", data, SERVER_GEN): return
            if handle_post_routes(self, self.path, "POST", data, SERVER_GEN): return
            if handle_interact_routes(self, self.path, "POST", data, SERVER_GEN): return
            
            self.send_error(404, "API Not Found")
        except Exception as e:
            print(f"Server Error: {e}")
            self.send_response(400)
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def server_start(port: int) -> None:
    global SERVER_GEN
    try:
        conn = create_connection()
        conn.ping()
        conn.close()
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    os.makedirs(WEB_ROOT, exist_ok=True)
    
    SERVER_GEN = StaticSiteGenerator(WEB_ROOT)
    watcher = DBWatcher(SERVER_GEN)
    t_watcher = threading.Thread(target=watcher.start, args=(3,), daemon=True)
    t_watcher.start()

    print(f"[+] Server started on port {port} (Multi-threaded).")
    try:
        with ThreadingHTTPServer(("0.0.0.0", port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        if os.path.exists(PID_FILE): os.remove(PID_FILE)