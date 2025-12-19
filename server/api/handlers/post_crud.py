from urllib.parse import parse_qs
from dao.factory import create_connection
from dao.post_dao import MySQLPostDAO
from dao.user_dao import MySQLUserDAO
from dao.url_map_dao import MySQLUrlMapDAO
from core.post import post_create, post_delete, post_get_full, post_update_content, post_set_public
from core.auth import verify_token
from server.api.utils import send_json, send_error
from server.api.handlers.utils import get_token

def force_sync_post(server_gen, cid: str, user_id: int):
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
        server_gen.sync_playground()
    finally:
        conn.close()

def force_sync_delete(server_gen, cid: str, user_id: int):
    if not server_gen: return
    print(f"[Sync] Force removing files for {cid}...")
    server_gen.remove_post_file(cid)
    server_gen.sync_user_index(user_id)
    server_gen.sync_playground()

def handle_create(handler, server_gen):
    try:
        token = get_token(handler)
        user_id = verify_token(token)
        cid = post_create(token)
        force_sync_post(server_gen, cid, user_id)
        send_json(handler, {'status': 'ok', 'cid': cid})
    except Exception as e:
        send_error(handler, str(e))
    return True

def handle_update(handler, body_data, server_gen):
    try:
        token = get_token(handler)
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

def handle_set_public(handler, body_data, server_gen):
    try:
        token = get_token(handler)
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

def handle_delete(handler, body_data, server_gen):
    try:
        token = get_token(handler)
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

def handle_detail(handler, parsed_path):
    try:
        token = get_token(handler)
        query = parse_qs(parsed_path.query)
        cid = query.get('cid', [None])[0]
        if not cid:
            send_error(handler, "Missing cid")
        else:
            data = post_get_full(token, cid)
            send_json(handler, data)
    except Exception as e:
        send_error(handler, str(e))
    return True

def handle_categories(handler):
    try:
        token = get_token(handler)
        user_id = verify_token(token)
        
        conn = create_connection()
        try:
            dao = MySQLPostDAO(conn)
            cats = dao.get_user_categories(user_id)
        finally:
            conn.close()
        send_json(handler, {'categories': cats})
    except Exception as e:
        send_error(handler, str(e))
    return True