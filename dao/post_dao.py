from datetime import datetime
import pymysql.connections
from dao.factory import create_connection
from dao.models import Post

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
                "snippet": r[6]
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

    def search_public_posts_paged(self, keyword: str, offset: int, limit: int) -> tuple[list[dict], int]:
        params = []
        where_clause = "WHERE p.is_public = TRUE"
        
        if keyword:
            where_clause += " AND (p.title LIKE %s OR p.context LIKE %s OR p.description LIKE %s)"
            like_kw = f"%{keyword}%"
            params.extend([like_kw, like_kw, like_kw])
            
        count_sql = f"SELECT COUNT(*) FROM posts p {where_clause}"
        
        data_sql = f"""
            SELECT p.cid, p.title, p.category, p.date, p.description, u.username, p.context
            FROM posts p
            JOIN users u ON p.owner_id = u.id
            {where_clause}
            ORDER BY p.date DESC
            LIMIT %s OFFSET %s
        """
        
        with self.conn.cursor() as cur:
            cur.execute(count_sql, tuple(params))
            total = cur.fetchone()[0]
            
            if total > 0:
                full_params = params + [limit, offset]
                cur.execute(data_sql, tuple(full_params))
                rows = cur.fetchall()
            else:
                rows = []

        posts = [
            {
                "cid": r[0],
                "title": r[1],
                "category": r[2],
                "date": str(r[3]),
                "description": r[4],
                "author": r[5],
                "context": r[6]
            }
            for r in rows
        ]
        
        return posts, total

    def get_user_categories(self, user_id: int) -> list[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT DISTINCT category FROM posts WHERE owner_id = %s ORDER BY category", (user_id,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []

    def get_post_by_cid(self, cid: str) -> Post:
        """获取单个文章对象 (兼容 Interact Handler)"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT cid, owner_id, title, context, description, category, date, is_public FROM posts WHERE cid=%s", (cid,))
            row = cur.fetchone()
        
        if not row:
            return None
            
        return Post(
            cid=row[0],
            owner_id=row[1],
            title=row[2],
            context=row[3],
            description=row[4],
            category=row[5],
            date=row[6],
            is_public=bool(row[7])
        )

# 辅助函数：获取 DAO 实例
def get_post_dao():
    conn = create_connection()
    return MySQLPostDAO(conn)