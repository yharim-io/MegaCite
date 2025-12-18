import pymysql.connections
from .models import User

class MySQLUserDAO:
    """MySQL 实现的 UserDAO。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def create_user(self, username: str, password_hash: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
            user_id = cur.lastrowid
        self.conn.commit()
        return user_id

    def get_user_by_username(self, username: str) -> User | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return User(id=row[0], username=row[1], password_hash=row[2])

    def get_user_by_id(self, user_id: int) -> User | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return User(id=row[0], username=row[1], password_hash=row[2])

    def update_user(self, user_id: int, updates: dict[str, any]) -> bool:
        if not updates:
            return False
        keys = []
        values = []
        for k, v in updates.items():
            keys.append(f"{k} = %s")
            values.append(v)
        values.append(user_id)
        sql = f"UPDATE users SET {', '.join(keys)} WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            changed = cur.rowcount
        self.conn.commit()
        return changed > 0

    def delete_user(self, user_id: int) -> bool:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            deleted = cur.rowcount
        self.conn.commit()
        return deleted > 0