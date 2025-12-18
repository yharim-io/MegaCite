"""
会话管理模块 - 用于管理第三方平台验证的会话状态
"""
import uuid
import json
import time
from typing import Dict, Optional, List
from pathlib import Path
from threading import Lock

SESSION_DIR = Path.home() / ".megacite_sessions"
SESSION_DIR.mkdir(exist_ok=True)

# 内存缓存会话信息（用于快速访问）
_sessions_cache: Dict[str, dict] = {}
_cache_lock = Lock()

class VerificationSession:
    """验证会话类，用于跟踪验证过程状态"""
    
    def __init__(self, session_id: str, user_id: int, platform: str):
        self.session_id = session_id
        self.user_id = user_id
        self.platform = platform
        self.created_at = time.time()
        self.status = "pending"  # pending, authenticated, failed
        self.cookies = None
        self.error_message = None
        self.last_screenshot = None
        
    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'platform': self.platform,
            'created_at': self.created_at,
            'status': self.status,
            'error_message': self.error_message,
        }
    
    def save(self):
        """持久化会话信息到磁盘"""
        session_file = SESSION_DIR / f"{self.session_id}.json"
        data = self.to_dict()
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    @staticmethod
    def load(session_id: str) -> Optional['VerificationSession']:
        """从磁盘加载会话信息"""
        session_file = SESSION_DIR / f"{session_id}.json"
        if not session_file.exists():
            return None
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            session = VerificationSession(
                data['session_id'],
                data['user_id'],
                data['platform']
            )
            session.created_at = data['created_at']
            session.status = data['status']
            session.error_message = data.get('error_message')
            return session
        except Exception as e:
            print(f"[-] Failed to load session {session_id}: {e}")
            return None
    
    @staticmethod
    def delete(session_id: str):
        """删除会话数据"""
        session_file = SESSION_DIR / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()


class SessionManager:
    """全局会话管理器"""
    
    @staticmethod
    def create_session(user_id: int, platform: str) -> str:
        """创建新的验证会话"""
        session_id = str(uuid.uuid4())
        session = VerificationSession(session_id, user_id, platform)
        
        with _cache_lock:
            _sessions_cache[session_id] = session
        
        session.save()
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[VerificationSession]:
        """获取会话信息"""
        with _cache_lock:
            if session_id in _sessions_cache:
                return _sessions_cache[session_id]
        
        # 从磁盘加载
        session = VerificationSession.load(session_id)
        if session:
            with _cache_lock:
                _sessions_cache[session_id] = session
        return session
    
    @staticmethod
    def update_session(session_id: str, status: str, 
                      cookies: Optional[List[dict]] = None,
                      error_message: Optional[str] = None):
        """更新会话状态"""
        session = SessionManager.get_session(session_id)
        if not session:
            return False
        
        session.status = status
        if cookies is not None:
            session.cookies = cookies
        if error_message:
            session.error_message = error_message
        
        session.save()
        
        with _cache_lock:
            _sessions_cache[session_id] = session
        
        return True
    
    @staticmethod
    def close_session(session_id: str):
        """关闭并删除会话"""
        VerificationSession.delete(session_id)
        with _cache_lock:
            if session_id in _sessions_cache:
                del _sessions_cache[session_id]
    
    @staticmethod
    def cleanup_expired_sessions(max_age_seconds: int = 3600):
        """清理过期的会话（超过指定时间）"""
        current_time = time.time()
        with _cache_lock:
            expired_ids = [
                sid for sid, session in _sessions_cache.items()
                if current_time - session.created_at > max_age_seconds
            ]
            for sid in expired_ids:
                del _sessions_cache[sid]
                VerificationSession.delete(sid)
