import json

def send_json(handler, data: dict, status: int = 200):
    """
    通用 JSON 响应辅助函数
    """
    handler.send_response(status)
    handler.send_header('Content-type', 'application/json')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())

def send_error(handler, message: str, status: int = 400):
    """
    通用错误响应
    """
    send_json(handler, {'error': message}, status)