import json
from core.auth import verify_token
from crawler.service import migrate_post_from_url
from server.api.utils import send_error
from server.api.handlers.utils import get_token
from server.api.handlers.post_crud import force_sync_post

def handle_migrate(handler, body_data, server_gen):
    try:
        token = get_token(handler)
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