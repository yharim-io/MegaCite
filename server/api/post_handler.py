import json
import http.cookies
from dao.factory import create_connection
from dao.post_dao import MySQLPostDAO
from dao.user_dao import MySQLUserDAO
from dao.url_map_dao import MySQLUrlMapDAO
from core.post import post_create, post_delete, post_get_full, post_update_content, post_set_public
from core.auth import verify_token
from crawler.service import migrate_post_from_url
from server.api.utils import send_json, send_error

def force_sync_post(server_gen, cid: str, user_id: int):
    """
    强制同步文章生成（由 Controller 调用）
    """
    if not server_gen: return

    conn = create_connection()
    try:
        post_dao = MySQLPostDAO(conn)
        title = post_dao.get_field(cid, "title")
        category = post_dao.get_field(cid, "category")
        date = post_dao.get_field(cid, "date")
        context = post_dao.get_field(cid, "context")
        desc = post_dao.get_field(cid, "description")
        is_public = post_dao.get_field(cid, "is_public")
        
        post_data = {
            "cid": cid, "title": title, "category": category,
            "date": str(date), "context": context, "description": desc,
            "is_public": bool(is_public)
        }
        
        user_dao = MySQLUserDAO(conn)
        user = user_dao.get_user_by_id(user_id)
        if not user: return
        
        print(f"[Sync] Force generating files for {cid}...")
        server_gen.sync_post_file(post_data, user.username)
        server_gen.sync_user_index(user_id)
        # 强制同步广场
        server_gen.sync_playground()
    finally:
        conn.close()

def force_sync_delete(server_gen, cid: str, user_id: int):
    if not server_gen: return
    print(f"[Sync] Force removing files for {cid}...")
    server_gen.remove_post_file(cid)
    server_gen.sync_user_index(user_id)
    server_gen.sync_playground()

def _get_token(handler):
    token = handler.headers.get('Authorization')
    if not token and "Cookie" in handler.headers:
        try:
            cookie = http.cookies.SimpleCookie(handler.headers["Cookie"])
            if "mc_token" in cookie:
                token = cookie["mc_token"].value
        except: pass
    return token

def handle_post_routes(handler, path: str, method: str, body_data: dict, server_gen):
    """
    分发 /api/post/* 及 categories 请求
    """
    if method == "POST":
        if path == '/api/post/create':
            try:
                token = _get_token(handler)
                user_id = verify_token(token)
                cid = post_create(token)
                force_sync_post(server_gen, cid, user_id)
                send_json(handler, {'status': 'ok', 'cid': cid})
            except Exception as e:
                send_error(handler, str(e))
            return True
        
        elif path == '/api/post/update':
            try:
                token = _get_token(handler)
                user_id = verify_token(token)
                cid = body_data.get('cid')
                
                if post_update_content(
                    token, cid, 
                    body_data.get('title'), 
                    body_data.get('category'), 
                    body_data.get('context'), 
                    body_data.get('description')
                ):
                    force_sync_post(server_gen, cid, user_id)
                    
                    target_url = None
                    conn = create_connection()
                    try:
                        map_dao = MySQLUrlMapDAO(conn)
                        target_url = map_dao.get_url_by_cid(cid)
                    finally:
                        conn.close()
                    
                    send_json(handler, {'status': 'ok', 'url': target_url})
                else:
                    send_error(handler, "Update failed")
            except Exception as e:
                send_error(handler, str(e))
            return True
        
        # [新增] 设置公开状态接口
        elif path == '/api/post/set_public':
            try:
                token = _get_token(handler)
                user_id = verify_token(token)
                cid = body_data.get('cid')
                is_public = body_data.get('is_public')
                
                if post_set_public(token, cid, is_public):
                    force_sync_post(server_gen, cid, user_id)
                    send_json(handler, {'status': 'ok'})
                else:
                    send_error(handler, "Update failed")
            except Exception as e:
                send_error(handler, str(e))
            return True

        elif path == '/api/post/delete':
            try:
                token = _get_token(handler)
                user_id = verify_token(token)
                cid = body_data.get('cid')
                if post_delete(token, cid):
                    force_sync_delete(server_gen, cid, user_id)
                    send_json(handler, {'status': 'ok'})
                else:
                    send_error(handler, "Delete failed")
            except Exception as e:
                send_error(handler, str(e))
            return True

        elif path == '/api/post/migrate':
            # SSE 迁移逻辑比较特殊，直接在这里处理响应流
            try:
                token = _get_token(handler)
                user_id = verify_token(token)
                url = body_data.get('url')
                
                handler.send_response(200)
                handler.send_header('Content-Type', 'text/event-stream')
                handler.send_header('Cache-Control', 'no-cache')
                handler.send_header('Connection', 'keep-alive')
                handler.end_headers()

                def progress_callback(msg):
                    try:
                        payload = json.dumps({'step': msg})
                        handler.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                        handler.wfile.flush()
                    except: pass

                try:
                    cid = migrate_post_from_url(token, url, progress_callback)
                    progress_callback("[*] Finalizing: Generating static pages...")
                    force_sync_post(server_gen, cid, user_id)
                    
                    success_payload = json.dumps({'success': True, 'cid': cid})
                    handler.wfile.write(f"data: {success_payload}\n\n".encode('utf-8'))
                except Exception as e:
                    error_payload = json.dumps({'error': str(e)})
                    handler.wfile.write(f"data: {error_payload}\n\n".encode('utf-8'))
                
                handler.wfile.flush()
            except Exception as e:
                send_error(handler, str(e))
            return True

    elif method == "GET":
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(handler.path)
        
        if parsed.path == '/api/post/detail':
            try:
                token = _get_token(handler)
                query = parse_qs(parsed.query)
                cid = query.get('cid', [None])[0]
                if not cid:
                    send_error(handler, "Missing cid")
                else:
                    data = post_get_full(token, cid)
                    send_json(handler, data)
            except Exception as e:
                send_error(handler, str(e))
            return True

        elif parsed.path == '/api/categories':
            try:
                token = _get_token(handler)
                user_id = verify_token(token)  # 验证用户，实现隔离
                
                conn = create_connection()
                try:
                    dao = MySQLPostDAO(conn)
                    cats = dao.get_user_categories(user_id) # 获取当前用户的分类
                finally:
                    conn.close()
                send_json(handler, {'categories': cats})
            except Exception as e:
                send_error(handler, str(e))
            return True

    return False