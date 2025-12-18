import http.server
import socketserver
import os
import threading
from generator.builder import StaticSiteGenerator
from generator.watcher import DBWatcher

def run_http_server(port: int, root_dir: str):
    """启动 HTTP 服务，阻塞运行"""
    abs_root = os.path.abspath(root_dir)
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=abs_root, **kwargs)

    print(f"[*] Starting HTTP Server on port {port} serving {abs_root}")
    with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()

def start_full_service(port: int = 8080):
    """
    启动所有服务：Watcher 和 HTTP Server
    """
    gen = StaticSiteGenerator("www")
    watcher = DBWatcher(gen)
    
    t_watcher = threading.Thread(target=watcher.start, args=(2,), daemon=True)
    t_watcher.start()
    
    run_http_server(port, "www")

if __name__ == "__main__":
    start_full_service()