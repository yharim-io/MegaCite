from datetime import datetime
import pymysql.connections

class MySQLPostDAO:
    """MySQL 实现的 PostDAO。"""

    ALLOWED_FIELDS = {"context", "title", "date", "description", "category", "owner_id", "is_public"}

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def create_post(self, owner_id: int, cid: str, title: str, category: str = "default", date: str = None) -> None:
        """创建文章，必须提供 title，category 默认为 default"""
        if date is None:
            date = datetime.now().date()
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO posts (cid, owner_id, title, category, date, is_public) VALUES (%s, %s, %s, %s, %s, %s)",
                (cid, owner_id, title, category, date, False),
            )
        self.conn.commit()

    def update_field(self, cid: str, field: str, value: any) -> bool:
        if field not in self.ALLOWED_FIELDS:
            return False
        sql = f"UPDATE posts SET {field} = %s WHERE cid = %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, (value, cid))
            changed = cur.rowcount
        self.conn.commit()
        return changed > 0

    def update_post_fields(self, cid: str, **kwargs) -> bool:
        """
        同时更新多个字段。
        """
        if not kwargs: return False
        
        set_clauses = []
        values = []
        for k, v in kwargs.items():
            if k in self.ALLOWED_FIELDS:
                set_clauses.append(f"{k} = %s")
                values.append(v)
        
        if not set_clauses: return False
        
        values.append(cid)
        sql = f"UPDATE posts SET {', '.join(set_clauses)} WHERE cid = %s"
        
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            changed = cur.rowcount
        self.conn.commit()
        return changed > 0

    def get_field(self, cid: str, field: str) -> any:
        if field not in self.ALLOWED_FIELDS:
            return None
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT {field} FROM posts WHERE cid = %s", (cid,))
            row = cur.fetchone()
        if not row:
            return None
        return row[0]

    def delete_post(self, cid: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM posts WHERE cid = %s", (cid,))
            deleted = cur.rowcount
        self.conn.commit()
        return deleted > 0

    def list_posts(self, offset: int, limit: int, orderby=None) -> list[str]:
        allowed_order = {"date", "title", "cid", "id"}
        order_clause = "ORDER BY date DESC"
        if orderby in allowed_order:
            order_clause = f"ORDER BY {orderby}"
        sql = f"SELECT cid FROM posts {order_clause} LIMIT %s OFFSET %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, (limit, offset))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []

    def list_public_posts(self) -> list[dict]:
        """获取所有公开的文章，包含作者信息和内容摘要"""
        # 使用 LEFT(context, 200) 获取前200字符作为摘要基础，后续在 Python 中处理
        sql = """
            SELECT p.cid, p.title, p.category, p.date, p.description, u.username, LEFT(p.context, 200)
            FROM posts p
            JOIN users u ON p.owner_id = u.id
            WHERE p.is_public = TRUE
            ORDER BY p.date DESC
        """
        with self.conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        
        return [
            {
                "cid": r[0],
                "title": r[1],
                "category": r[2],
                "date": str(r[3]),
                "description": r[4],
                "author": r[5],
                "snippet": r[6]  # 新增摘要字段
            }
            for r in rows
        ]

    def search_posts(self, keyword: str) -> list[str]:
        like = f"%{keyword}%"
        results: list[str] = []
        seen = set()

        with self.conn.cursor() as cur:
            cur.execute("SELECT cid FROM posts WHERE title LIKE %s", (like,))
            for r in cur.fetchall():
                cid = r[0]
                if cid not in seen:
                    seen.add(cid)
                    results.append(cid)

            cur.execute("SELECT cid FROM posts WHERE description LIKE %s", (like,))
            for r in cur.fetchall():
                cid = r[0]
                if cid not in seen:
                    seen.add(cid)
                    results.append(cid)

            cur.execute("SELECT cid FROM posts WHERE context LIKE %s", (like,))
            for r in cur.fetchall():
                cid = r[0]
                if cid not in seen:
                    seen.add(cid)
                    results.append(cid)

        return results

    def get_all_categories(self) -> list[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT DISTINCT category FROM posts ORDER BY category")
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []