from dao.models import User

class MySQLUserDAO:
    def __init__(self, conn):
        self.conn = conn

    def create_user(self, username, password_hash, email=None):
        cursor = self.conn.cursor()
        # [注意] 如果数据库表 users 还没有 email 列，需要手动执行 ALTER TABLE users ADD COLUMN email VARCHAR(255);
        sql = "INSERT INTO users (username, password_hash, email, created_at) VALUES (%s, %s, %s, NOW())"
        cursor.execute(sql, (username, password_hash, email))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_by_username(self, username):
        # Removed dictionary=True to fix compatibility issues
        cursor = self.conn.cursor() 
        sql = "SELECT id, username, password_hash, created_at, email FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            # Manually map row to User object
            return User(id=row[0], username=row[1], password_hash=row[2], created_at=row[3], email=row[4])
        return None

    def get_user_by_id(self, user_id):
        # Removed dictionary=True to fix compatibility issues
        cursor = self.conn.cursor()
        sql = "SELECT id, username, password_hash, created_at, email FROM users WHERE id = %s"
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            # Manually map row to User object
            return User(id=row[0], username=row[1], password_hash=row[2], created_at=row[3], email=row[4])
        return None

    def update_password(self, user_id, new_hash):
        cursor = self.conn.cursor()
        sql = "UPDATE users SET password_hash = %s WHERE id = %s"
        cursor.execute(sql, (new_hash, user_id))
        self.conn.commit()
        cursor.close()