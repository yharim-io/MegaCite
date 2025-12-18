from dao import MySQLUserDAO
from dao.factory import create_connection
from core.security import hash_password, generate_token

def user_register(username: str, password: str) -> int:
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        # 简单检查是否存在
        if dao.get_user_by_username(username):
            raise ValueError("Username already exists")
            
        hashed = hash_password(password)
        user_id = dao.create_user(username, hashed)
        return user_id
    finally:
        conn.close()

def user_login(username: str, password: str) -> str:
    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        user = dao.get_user_by_username(username)
        
        if not user:
            raise ValueError("User not found")
        
        if user.password_hash != hash_password(password):
            raise ValueError("Invalid password")
            
        new_token = generate_token()
        dao.update_user(user.id, {"token": new_token})
        return new_token
    finally:
        conn.close()

def change_password(token: str, old_pass: str, new_pass: str) -> None:
    user_id = verify_token(token)
    
    if not new_pass or len(new_pass) < 6:
        raise ValueError("New password is too short")

    conn = create_connection()
    try:
        dao = MySQLUserDAO(conn)
        
        # 1. 获取用户信息
        user = dao.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
            
        # 2. 验证旧密码
        if user.password_hash != hash_password(old_pass):
            raise ValueError("Incorrect old password")
        
        # 3. 更新新密码
        hashed_new = hash_password(new_pass)
        dao.update_user(user_id, {"password_hash": hashed_new})
    finally:
        conn.close()

def verify_token(token: str) -> int:
    if not token:
        raise PermissionError("No token provided")

    conn = create_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE token = %s", (token,))
            row = cur.fetchone()
            
        if not row:
            raise PermissionError("Invalid or expired token")
            
        return row[0]
    finally:
        conn.close()