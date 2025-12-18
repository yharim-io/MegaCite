import hashlib
import uuid
import time
from dao.factory import create_connection
from dao.user_dao import MySQLUserDAO

# 简单的内存 Token 存储 (生产环境应使用 Redis)
_TOKEN_CACHE = {} 

def generate_token(user_id):
    token = str(uuid.uuid4())
    _TOKEN_CACHE[token] = {
        "user_id": user_id,
        "expires": time.time() + 86400 * 7 # 7 days
    }
    return token

def verify_token(token):
    if not token:
        raise ValueError("Token is empty")
    session = _TOKEN_CACHE.get(token)
    if not session:
        raise ValueError("Invalid token")
    if time.time() > session['expires']:
        del _TOKEN_CACHE[token]
        raise ValueError("Token expired")
    return session['user_id']

def user_login(username, password):
    conn = create_connection()
    try:
        user_dao = MySQLUserDAO(conn)
        user = user_dao.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        # 简单哈希验证
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash != password_hash:
            raise ValueError("Invalid password")
            
        return generate_token(user.id)
    finally:
        conn.close()

def user_register(username, password, email=None):
    """
    注册新用户
    :param username: 用户名
    :param password: 密码
    :param email: 邮箱 (可选)
    """
    conn = create_connection()
    try:
        user_dao = MySQLUserDAO(conn)
        if user_dao.get_user_by_username(username):
            raise ValueError("Username already exists")
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        # [修复] 传递 email 给 DAO
        user_id = user_dao.create_user(username, password_hash, email)
        return user_id
    finally:
        conn.close()

def change_password(token, old_password, new_password):
    user_id = verify_token(token)
    conn = create_connection()
    try:
        user_dao = MySQLUserDAO(conn)
        user = user_dao.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
            
        old_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if user.password_hash != old_hash:
            raise ValueError("Wrong old password")
            
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        user_dao.update_password(user_id, new_hash)
    finally:
        conn.close()