import json
import http.cookies
from urllib.parse import urlparse
from core.auth import user_login, user_register, change_password, verify_token
from verification import manager as verify_manager
from dao.factory import create_connection
from dao.auth_dao import MySQLAuthDAO
from dao.user_dao import MySQLUserDAO
from server.api.utils import send_json, send_error
from core.email_utils import send_verification_email, verify_code

def _get_token(handler):
    token = handler.headers.get('Authorization')
    if not token and "Cookie" in handler.headers:
        try:
            cookie = http.cookies.SimpleCookie(handler.headers["Cookie"])
            if "mc_token" in cookie:
                token = cookie["mc_token"].value
        except: pass
    return token

def handle_auth_routes(handler, path: str, method: str, body_data: dict, server_gen):
    """
    分发处理 /api/auth/* 及登录注册相关的请求
    """
    # 解析纯路径，忽略查询参数
    parsed_path = urlparse(path).path

    if method == "POST":
        if parsed_path == '/api/login':
            try:
                token = user_login(body_data.get('username'), body_data.get('password'))
                try:
                    user_id = verify_token(token)
                    if server_gen:
                        print(f"[*] Login Sync: Generating index for user {user_id}")
                        server_gen.sync_user_index(user_id)
                except Exception as e:
                    print(f"[-] Login Sync Failed: {e}")
                send_json(handler, {'token': token})
            except Exception as e:
                send_error(handler, str(e))
            return True

        elif parsed_path == '/api/auth/send_code':
            email = body_data.get('email')
            if not email:
                send_error(handler, "请输入邮箱地址")
                return True
            if send_verification_email(email):
                send_json(handler, {'status': 'ok'})
            else:
                send_error(handler, "发送失败")
            return True

        elif parsed_path == '/api/register':
            username = body_data.get('username')
            password = body_data.get('password')
            email = body_data.get('email')
            code = body_data.get('code')

            # 验证码校验
            if email and code:
                if not verify_code(email, code):
                    send_error(handler, "验证码错误或已过期")
                    return True
            
            try:
                uid = user_register(username, password, email)
                if server_gen:
                    try: server_gen.sync_user_index(uid)
                    except Exception: pass
                
                token = user_login(username, password)
                send_json(handler, {'status': 'ok', 'token': token})
            except Exception as e:
                send_error(handler, str(e))
            return True
        
        elif parsed_path == '/api/change_password':
            try:
                token = _get_token(handler)
                change_password(token, body_data.get('old_password'), body_data.get('new_password'))
                send_json(handler, {'status': 'ok'})
            except ValueError as ve:
                send_error(handler, str(ve))
            return True

        # --- 第三方验证 ---
        elif parsed_path == '/api/auth/init':
            token = _get_token(handler)
            # 这里也需要鉴权，但为了逻辑统一，假设 _get_token 失败会在 session_init 内部处理或抛错
            # 严格来说应该在这里 verify_token
            try:
                user_id = verify_token(token)
            except Exception as e:
                send_error(handler, str(e), 401)
                return True

            platform = body_data.get('platform')
            session_id = verify_manager.session_init(user_id, platform)
            if session_id:
                send_json(handler, {'session_id': session_id, 'status': 'initialized'})
            else:
                send_error(handler, "Failed to init session")
            return True
        
        elif parsed_path == '/api/auth/save_cookies':
            session_id = body_data.get('session_id')
            cookies = body_data.get('cookies', [])
            if verify_manager.session_save_cookies(session_id, cookies):
                send_json(handler, {'status': 'ok'})
            else:
                send_error(handler, "Failed to save cookies")
            return True
        
        elif parsed_path == '/api/auth/save_error':
            verify_manager.session_save_error(body_data.get('session_id'), body_data.get('error'))
            send_json(handler, {'status': 'ok'})
            return True

        elif parsed_path == '/api/auth/cancel':
            verify_manager.session_close(body_data.get('session_id'))
            send_json(handler, {'status': 'cancelled'})
            return True

        elif parsed_path == '/api/auth/unbind':
            try:
                token = _get_token(handler)
                user_id = verify_token(token)
            except Exception as e:
                send_error(handler, str(e), 401)
                return True

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
        # [修改] 获取用户信息 - 严格分离鉴权错误和业务错误
        if parsed_path == '/api/user/info':
            # 1. 鉴权阶段
            user_id = None
            try:
                token = _get_token(handler)
                if not token:
                    raise ValueError("Token missing")
                user_id = verify_token(token)
            except Exception as e:
                send_error(handler, f"Auth failed: {str(e)}", 401)
                return True

            # 2. 业务阶段
            try:
                conn = create_connection()
                try:
                    user_dao = MySQLUserDAO(conn)
                    user = user_dao.get_user_by_id(user_id)
                    if user:
                        # 兼容 User 对象或字典返回
                        created_at = getattr(user, 'created_at', None)
                        email = getattr(user, 'email', None)
                        username = getattr(user, 'username', 'Unknown')

                        # 如果 getattr 没取到，尝试用字典方式 (针对某些 DAO 实现)
                        if username == 'Unknown' and isinstance(user, dict):
                            created_at = user.get('created_at')
                            email = user.get('email')
                            username = user.get('username')

                        created_at_str = str(created_at).split(" ")[0] if created_at else "未知"
                        
                        send_json(handler, {
                            'username': username,
                            'email': email if email else "未绑定",
                            'created_at': created_at_str
                        })
                    else:
                        send_error(handler, "User not found in DB", 404)
                finally:
                    conn.close()
            except Exception as e:
                # 打印错误堆栈到服务端控制台，方便调试
                import traceback
                traceback.print_exc()
                send_error(handler, f"Server Error: {str(e)}", 500)
            return True

        elif parsed_path == '/api/auth/bindings':
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
                # 这里为了静默失败保持原样，也可以改为更严格的错误处理
                send_json(handler, {'bindings': []})
            return True
            
        elif parsed_path == '/api/auth/status':
            from urllib.parse import parse_qs
            parsed = urlparse(handler.path) # 这里还需要 parse query
            query = parse_qs(parsed.query)
            session_id = query.get('session_id', [None])[0]
            if not session_id:
                send_error(handler, "Missing session_id")
            else:
                status = verify_manager.session_get_status(session_id)
                send_json(handler, status)
            return True
    
    return False