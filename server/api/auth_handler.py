import json
import http.cookies
from core.auth import user_login, user_register, change_password, verify_token
from verification import manager as verify_manager
from dao.factory import create_connection
from dao.auth_dao import MySQLAuthDAO
from server.api.utils import send_json, send_error

def handle_auth_routes(handler, path: str, method: str, body_data: dict, server_gen):
    """
    分发处理 /api/auth/* 及登录注册相关的请求
    """
    if method == "POST":
        if path == '/api/login':
            token = user_login(body_data.get('username'), body_data.get('password'))
            try:
                user_id = verify_token(token)
                if server_gen:
                    print(f"[*] Login Sync: Generating index for user {user_id}")
                    server_gen.sync_user_index(user_id)
            except Exception as e:
                print(f"[-] Login Sync Failed: {e}")
            send_json(handler, {'token': token})
            return True

        elif path == '/api/register':
            uid = user_register(body_data.get('username'), body_data.get('password'))
            if server_gen:
                try: server_gen.sync_user_index(uid)
                except Exception: pass
            send_json(handler, {'status': 'ok'})
            return True
        
        elif path == '/api/change_password':
            try:
                token = _get_token(handler)
                change_password(token, body_data.get('old_password'), body_data.get('new_password'))
                send_json(handler, {'status': 'ok'})
            except ValueError as ve:
                send_error(handler, str(ve))
            return True

        # --- 第三方验证 ---
        elif path == '/api/auth/init':
            token = _get_token(handler)
            user_id = verify_token(token)
            platform = body_data.get('platform')
            session_id = verify_manager.session_init(user_id, platform)
            if session_id:
                send_json(handler, {'session_id': session_id, 'status': 'initialized'})
            else:
                send_error(handler, "Failed to init session")
            return True
        
        elif path == '/api/auth/save_cookies':
            session_id = body_data.get('session_id')
            cookies = body_data.get('cookies', [])
            if verify_manager.session_save_cookies(session_id, cookies):
                send_json(handler, {'status': 'ok'})
            else:
                send_error(handler, "Failed to save cookies")
            return True
        
        elif path == '/api/auth/save_error':
            verify_manager.session_save_error(body_data.get('session_id'), body_data.get('error'))
            send_json(handler, {'status': 'ok'})
            return True

        elif path == '/api/auth/cancel':
            verify_manager.session_close(body_data.get('session_id'))
            send_json(handler, {'status': 'cancelled'})
            return True

        elif path == '/api/auth/unbind':
            token = _get_token(handler)
            user_id = verify_token(token)
            platform = body_data.get('platform')
            conn = create_connection()
            try:
                dao = MySQLAuthDAO(conn)
                dao.remove_platform_auth(user_id, platform)
                send_json(handler, {'status': 'ok'})
            finally:
                conn.close()
            return True

    elif method == "GET":
        if path == '/api/auth/bindings':
            try:
                token = _get_token(handler)
                user_id = verify_token(token)
                conn = create_connection()
                try:
                    dao = MySQLAuthDAO(conn)
                    platforms = dao.list_platform_auths(user_id)
                    send_json(handler, {'bindings': platforms})
                finally:
                    conn.close()
            except Exception:
                send_json(handler, {'bindings': []})
            return True
            
        elif path == '/api/auth/status':
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(handler.path)
            query = parse_qs(parsed.query)
            session_id = query.get('session_id', [None])[0]
            if not session_id:
                send_error(handler, "Missing session_id")
            else:
                status = verify_manager.session_get_status(session_id)
                send_json(handler, status)
            return True
    
    return False

def _get_token(handler):
    token = handler.headers.get('Authorization')
    if not token and "Cookie" in handler.headers:
        try:
            cookie = http.cookies.SimpleCookie(handler.headers["Cookie"])
            if "mc_token" in cookie:
                token = cookie["mc_token"].value
        except: pass
    return token