from verification.csdn import CSDNVerifier
from verification.jianshu import JianshuVerifier
from verification.cnblogs import CNBlogsVerifier
from verification.juejin import JuejinVerifier
from verification.yuque import YuqueVerifier
from client.cookie_store import save_cookies
from dao.factory import create_connection
from dao.auth_dao import MySQLAuthDAO
import json
import uuid
from threading import Lock, Event
from time import time

_sessions = {}
_sessions_lock = Lock()

class VerificationSession:
    def __init__(self, session_id: str, user_id: int, platform: str):
        self.session_id = session_id
        self.user_id = user_id
        self.platform = platform
        self.created_at = time()
        self.status = "pending"
        self.error_message = None
        # 用于异步通知状态变更的事件锁
        self.event = Event()

def _get_verifier(platform_or_url: str):
    target = platform_or_url.lower()
    if target == "csdn" or "csdn.net" in target: return CSDNVerifier()
    if target == "jianshu" or "jianshu.com" in target: return JianshuVerifier()
    if target == "cnblogs" or "cnblogs.com" in target: return CNBlogsVerifier()
    if target == "juejin" or "juejin.cn" in target: return JuejinVerifier()
    if target == "yuque" or "yuque.com" in target: return YuqueVerifier()
    return None

def login_platform(platform_name: str) -> bool:
    # 仅供 CLI 本地使用
    verifier = _get_verifier(platform_name)
    return verifier.login() if verifier else False

def verify_url_owner(url: str, user_id: int) -> bool:
    """验证 URL 所有权，需传入 user_id 以加载对应 Cookie"""
    verifier = _get_verifier(url)
    if not verifier:
        print(f"[-] No verifier found for URL: {url}")
        return False
    
    return verifier.check_ownership(url, user_id)

# ========== 会话管理 APIs ==========

def session_init(user_id: int, platform: str) -> str:
    if not _get_verifier(platform):
        raise ValueError(f"Platform '{platform}' not supported")
    session_id = str(uuid.uuid4())
    session = VerificationSession(session_id, user_id, platform)
    with _sessions_lock:
        _sessions[session_id] = session
    return session_id

def session_save_cookies(session_id: str, cookies: list) -> bool:
    with _sessions_lock:
        session = _sessions.get(session_id)
        if not session: return False
    
    # 传入 user_id 进行隔离存储
    save_cookies(session.user_id, session.platform, cookies)
    
    try:
        conn = create_connection()
        dao = MySQLAuthDAO(conn)
        credential = json.dumps(cookies)
        dao.add_platform_auth(session.user_id, session.platform, credential)
        conn.close()
    except Exception as e:
        print(f"[-] Failed to save to database: {e}")
    
    with _sessions_lock:
        session.status = "authenticated"
        # 唤醒等待的线程
        session.event.set()
    return True

def session_get_status(session_id: str) -> dict:
    with _sessions_lock:
        session = _sessions.get(session_id)
    if not session: return {"status": "invalid"}
    return {"status": session.status, "platform": session.platform, "error": session.error_message}

def session_wait(session_id: str, timeout: int = 60) -> dict:
    """
    阻塞等待会话状态变更 (Long Polling / SSE 支持)
    """
    session = None
    with _sessions_lock:
        session = _sessions.get(session_id)
    
    if not session:
        return {"status": "invalid"}
        
    # 如果状态已经是非 pending，直接返回
    if session.status != "pending":
        return {"status": session.status, "platform": session.platform, "error": session.error_message}
        
    # 阻塞等待事件触发或超时
    session.event.wait(timeout)
    
    return {"status": session.status, "platform": session.platform, "error": session.error_message}

def session_close(session_id: str):
    with _sessions_lock:
        if session_id in _sessions: del _sessions[session_id]

def session_save_error(session_id: str, error_message: str):
    with _sessions_lock:
        session = _sessions.get(session_id)
        if not session: return False
        session.status = "failed"
        session.error_message = error_message
        # 唤醒等待的线程
        session.event.set()
    return True