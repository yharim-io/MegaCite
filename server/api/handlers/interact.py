import json
import traceback
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs
from core.auth import verify_token
from dao import interact_dao
from dao.post_dao import get_post_dao

def get_current_user(headers):
    if "Cookie" not in headers:
        return None
    try:
        cookie = SimpleCookie(headers["Cookie"])
        if "mc_token" in cookie:
            user = verify_token(cookie["mc_token"].value)
            return user
    except Exception:
        pass
    return None

def get_user_id(user):
    """安全获取用户ID，兼容 user 是对象或整数的情况"""
    if hasattr(user, 'id'):
        return user.id
    if isinstance(user, int):
        return user
    if isinstance(user, dict) and 'id' in user:
        return user['id']
    return None

def handle_interact_routes(handler, path, method, data, server_gen):
    # 仅处理 /api/interact 开头的请求
    if not path.startswith('/api/interact'):
        return False

    try:
        user = get_current_user(handler.headers)
        user_id = get_user_id(user) if user else None
        
        # 解析查询参数
        parsed_url = urlparse(path)
        query_params = parse_qs(parsed_url.query)
        
        # 获取 PostDAO 实例
        post_dao_inst = get_post_dao()

        # ------------------------------------------------
        # GET /api/interact/batch_stats - 批量获取文章统计数据
        # ------------------------------------------------
        if parsed_url.path == '/api/interact/batch_stats' and method == 'GET':
            cids_param = query_params.get('cids', [None])[0]
            if not cids_param:
                _send_json(handler, 400, {'error': '缺少参数 cids'})
                return True
            
            # cids 应该是一个逗号分隔的字符串
            cids = cids_param.split(',')
            results = {}
            
            for cid in cids:
                if not cid.strip(): continue
                likes = interact_dao.count_likes_for_post(cid)
                comments = interact_dao.count_comments_for_post(cid)
                results[cid] = {
                    'likes': likes,
                    'comments': comments
                }
            
            _send_json(handler, 200, results)
            return True

        # ------------------------------------------------
        # POST /api/interact/like - 点赞/取消点赞
        # ------------------------------------------------
        if parsed_url.path == '/api/interact/like' and method == 'POST':
            if not user_id:
                _send_json(handler, 401, {'error': '请先登录'})
                return True
            
            post_cid = data.get('post_cid')
            if not post_cid:
                _send_json(handler, 400, {'error': '缺少参数 post_cid'})
                return True

            # 检查文章是否存在
            post = post_dao_inst.get_post_by_cid(post_cid)
            if not post:
                _send_json(handler, 404, {'error': '文章不存在'})
                return True
            
            # 禁止自赞
            if post.owner_id == user_id:
                _send_json(handler, 400, {'error': '不能给自己点赞'})
                return True

            # 执行点赞逻辑
            if interact_dao.has_user_liked(user_id, post_cid):
                interact_dao.remove_like(user_id, post_cid)
                action = 'removed'
            else:
                interact_dao.add_like(user_id, post_cid)
                action = 'added'
            
            new_count = interact_dao.count_likes_for_post(post_cid)
            _send_json(handler, 200, {'status': 'ok', 'action': action, 'count': new_count})
            return True

        # ------------------------------------------------
        # GET /api/interact/stats - 获取单篇文章统计数据 (包含用户状态)
        # ------------------------------------------------
        if parsed_url.path == '/api/interact/stats' and method == 'GET':
            post_cid = query_params.get('post_cid', [None])[0]
            if not post_cid:
                _send_json(handler, 400, {'error': '缺少 post_cid'})
                return True
                
            likes = interact_dao.count_likes_for_post(post_cid)
            comments = interact_dao.count_comments_for_post(post_cid)
            liked_by_me = False
            if user_id:
                liked_by_me = interact_dao.has_user_liked(user_id, post_cid)
                
            _send_json(handler, 200, {
                'likes': likes,
                'comments': comments,
                'liked_by_me': liked_by_me,
                'current_user_id': user_id
            })
            return True

        # ------------------------------------------------
        # POST /api/interact/comment - 发布评论
        # ------------------------------------------------
        if parsed_url.path == '/api/interact/comment' and method == 'POST':
            if not user_id:
                _send_json(handler, 401, {'error': '请先登录'})
                return True
                
            post_cid = data.get('post_cid')
            content = data.get('content')
            
            if not post_cid:
                _send_json(handler, 400, {'error': '缺少 post_cid'})
                return True
            if not content or not content.strip():
                _send_json(handler, 400, {'error': '评论内容不能为空'})
                return True

            interact_dao.create_comment(user_id, post_cid, content)
            _send_json(handler, 200, {'status': 'ok'})
            return True

        # ------------------------------------------------
        # GET /api/interact/comments - 获取评论列表
        # ------------------------------------------------
        if parsed_url.path == '/api/interact/comments' and method == 'GET':
            post_cid = query_params.get('post_cid', [None])[0]
            if not post_cid:
                _send_json(handler, 400, {'error': '缺少 post_cid'})
                return True

            comments_data = interact_dao.get_comments_for_post(post_cid)
            
            # 获取文章作者ID
            post = post_dao_inst.get_post_by_cid(post_cid)
            post_owner_id = post.owner_id if post else -1

            resp_list = []
            for c in comments_data:
                can_delete = False
                if user_id:
                    if user_id == c.user_id or user_id == post_owner_id:
                        can_delete = True
                
                resp_list.append({
                    'id': c.id,
                    'user_id': c.user_id,
                    'username': c.username,
                    'content': c.content,
                    'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(c.created_at, 'strftime') else str(c.created_at),
                    'can_delete': can_delete
                })

            _send_json(handler, 200, {'comments': resp_list})
            return True

        # ------------------------------------------------
        # DELETE /api/interact/comment - 删除评论
        # ------------------------------------------------
        if parsed_url.path == '/api/interact/comment' and method == 'DELETE':
            if not user_id:
                _send_json(handler, 401, {'error': '请先登录'})
                return True
                
            comment_id = query_params.get('id', [None])[0]
            if not comment_id:
                _send_json(handler, 400, {'error': '缺少评论ID'})
                return True
            
            comment = interact_dao.get_comment_by_id(comment_id)
            if not comment:
                _send_json(handler, 404, {'error': '评论不存在'})
                return True
                
            post = post_dao_inst.get_post_by_cid(comment.post_cid)
            
            is_sender = (user_id == comment.user_id)
            is_owner = (post and user_id == post.owner_id)
            
            if not (is_sender or is_owner):
                _send_json(handler, 403, {'error': '无权删除'})
                return True
                
            interact_dao.delete_comment(comment_id)
            _send_json(handler, 200, {'status': 'ok'})
            return True

        return False

    except Exception as e:
        print(f"[-] Interact Handler Exception: {str(e)}")
        traceback.print_exc()
        _send_json(handler, 500, {'error': f'Internal Server Error: {str(e)}'})
        return True

def _send_json(handler, code, data):
    try:
        response = json.dumps(data).encode('utf-8')
        handler.send_response(code)
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Content-Length', str(len(response)))
        handler.end_headers()
        handler.wfile.write(response)
    except Exception as e:
        print(f"[-] Failed to send JSON response: {e}")