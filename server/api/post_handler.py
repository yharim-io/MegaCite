from urllib.parse import urlparse, parse_qs
from server.api.handlers.playground import handle_playground_request
from server.api.handlers.post_crud import (
    handle_create, handle_update, handle_set_public, 
    handle_delete, handle_detail, handle_categories,
    force_sync_post, force_sync_delete
)
from server.api.handlers.migration import handle_migrate

# Re-exporting for compatibility if needed elsewhere
__all__ = [
    'handle_post_routes', 'force_sync_post', 'force_sync_delete'
]

def handle_post_routes(handler, path: str, method: str, body_data: dict, server_gen):
    """
    分发 /api/post/* 及 categories 请求
    """
    parsed = urlparse(path)
    if (parsed.path == '/playground' or parsed.path == '/playground.html') and method == 'GET':
        query = parse_qs(parsed.query)
        return handle_playground_request(handler, query)

    if method == "POST":
        if path == '/api/post/create':
            return handle_create(handler, server_gen)
        
        elif path == '/api/post/update':
            return handle_update(handler, body_data, server_gen)
        
        elif path == '/api/post/set_public':
            return handle_set_public(handler, body_data, server_gen)

        elif path == '/api/post/delete':
            return handle_delete(handler, body_data, server_gen)

        elif path == '/api/post/migrate':
            return handle_migrate(handler, body_data, server_gen)

    elif method == "GET":
        if parsed.path == '/api/post/detail':
            return handle_detail(handler, parsed)

        elif parsed.path == '/api/categories':
            return handle_categories(handler)

    return False