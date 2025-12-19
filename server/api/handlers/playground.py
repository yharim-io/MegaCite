import math
from dao.factory import create_connection
from dao.post_dao import MySQLPostDAO
from dao.url_map_dao import MySQLUrlMapDAO
from core.config import SERVER_CONFIG
from server.api.utils import send_error
from server.api.handlers.utils import highlight_title, highlight_snippet

def handle_playground_request(handler, query_params):
    """处理 /playground 请求，支持搜索和分页"""
    keyword = query_params.get('q', [''])[0].strip()
    try:
        page = int(query_params.get('page', ['1'])[0])
    except ValueError:
        page = 1
    if page < 1: page = 1
    
    page_size = 15
    offset = (page - 1) * page_size
    
    conn = create_connection()
    try:
        post_dao = MySQLPostDAO(conn)
        url_dao = MySQLUrlMapDAO(conn)
        # 直接使用 SQL 模糊搜索
        posts, total_count = post_dao.search_public_posts_paged(keyword, offset, page_size)
        
        host = SERVER_CONFIG.get("host", "127.0.0.1")
        port = SERVER_CONFIG.get("port", 8080)
        base_url = f"http://{host}:{port}"
        
        for p in posts:
            rel_path = url_dao.get_url_by_cid(p['cid'])
            if rel_path:
                if not rel_path.startswith('/'):
                    rel_path = '/' + rel_path
                if not rel_path.endswith('.html'):
                    rel_path += '.html'
                p['url'] = f"{base_url}{rel_path}"
            else:
                p['url'] = f"{base_url}/post.html?cid={p['cid']}"
                
    finally:
        conn.close()
    
    # 构建文章列表 HTML
    items_html = []
    if not posts:
        items_html.append('<div class="no-results" style="text-align: center; color: #666; margin-top: 50px;">未找到相关文章。</div>')
    else:
        items_html.append('<div class="post-list">')
        for p in posts:
            display_title = highlight_title(p.get('title'), keyword)
            display_snippet = highlight_snippet(p.get('context'), keyword)
            
            item = f"""
            <div class="post-item-container playground-item">
                <a href="{p['url']}" class="post-item-link">
                    <div class="post-item-title">{display_title}</div>
                    <div class="post-item-snippet">{display_snippet}</div>
                    <div class="post-item-meta">
                        <span class="post-item-author">{p.get('author', 'Unknown')}</span>
                        <span>{p.get('date', '')}</span>
                    </div>
                </a>
            </div>
            """
            items_html.append(item)
        items_html.append('</div>')

    # 构建分页 HTML
    total_pages = math.ceil(total_count / page_size)
    if total_pages > 1:
        pagination_html = ['<div class="pagination" style="display: flex; justify-content: center; gap: 10px; margin-top: 40px;">']
        if page > 1:
            pagination_html.append(f'<a href="/playground.html?q={keyword}&page={page-1}" class="page-link">上一页</a>')
        
        pagination_html.append(f'<span class="page-info" style="line-height: 36px;">第 {page} 页 / 共 {total_pages} 页</span>')
        
        if page < total_pages:
            pagination_html.append(f'<a href="/playground.html?q={keyword}&page={page+1}" class="page-link">下一页</a>')
        pagination_html.append('</div>')
        items_html.append("".join(pagination_html))
    
    content_list_html = "".join(items_html)
    
    # 读取模板并替换
    try:
        with open('templates/playground.html', 'r', encoding='utf-8') as f:
            template_playground = f.read()
        
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            template_base = f.read()
            
        fragment = template_playground.replace('{content_list}', content_list_html)
        fragment = fragment.replace('{search_query}', keyword)
        
        full_html = template_base.format(
            content=fragment,
            page_title="广场 - MegaCite",
            nav_console_active="",
            nav_settings_active="",
            nav_playground_active="active",
            meta_extra='<meta name="page-type" content="playground">',
            modal_extra=""
        )
        
        handler.send_response(200)
        handler.send_header('Content-type', 'text/html; charset=utf-8')
        handler.end_headers()
        handler.wfile.write(full_html.encode('utf-8'))
        return True
    except Exception as e:
        send_error(handler, f"Template Error: {str(e)}")
        return True