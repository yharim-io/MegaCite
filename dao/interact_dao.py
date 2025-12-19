from dao.factory import create_connection
from dao.models import Like, Comment

def init_interact_tables():
    """初始化交互所需的数据库表（如果不存在）"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                post_cid VARCHAR(32) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY ux_user_post_like (user_id, post_cid),
                CONSTRAINT fk_like_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_like_post FOREIGN KEY (post_cid) REFERENCES posts(cid) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                post_cid VARCHAR(32) NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_comment_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_comment_post FOREIGN KEY (post_cid) REFERENCES posts(cid) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def add_like(user_id: int, post_cid: str) -> bool:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT IGNORE INTO likes (user_id, post_cid) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, post_cid))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def remove_like(user_id: int, post_cid: str) -> bool:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM likes WHERE user_id = %s AND post_cid = %s"
        cursor.execute(sql, (user_id, post_cid))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def has_user_liked(user_id: int, post_cid: str) -> bool:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT 1 FROM likes WHERE user_id = %s AND post_cid = %s LIMIT 1"
        cursor.execute(sql, (user_id, post_cid))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def count_likes_for_post(post_cid: str) -> int:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT COUNT(*) FROM likes WHERE post_cid = %s"
        cursor.execute(sql, (post_cid,))
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        conn.close()

def count_total_likes_for_username(username: str) -> int:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT COUNT(l.id) 
            FROM likes l
            JOIN posts p ON l.post_cid = p.cid
            JOIN users u ON p.owner_id = u.id
            WHERE u.username = %s
        """
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        conn.close()

def create_comment(user_id: int, post_cid: str, content: str) -> int:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO comments (user_id, post_cid, content) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, post_cid, content))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def delete_comment(comment_id: int) -> bool:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM comments WHERE id = %s"
        cursor.execute(sql, (comment_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def get_comment_by_id(comment_id: int) -> Comment:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT id, user_id, post_cid, content, created_at FROM comments WHERE id = %s"
        cursor.execute(sql, (comment_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return Comment(
            id=row[0],
            user_id=row[1],
            post_cid=row[2],
            content=row[3],
            created_at=row[4]
        )
    finally:
        cursor.close()
        conn.close()

def get_comments_for_post(post_cid: str) -> list[Comment]:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT c.id, c.user_id, c.post_cid, c.content, c.created_at, u.username 
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_cid = %s
            ORDER BY c.created_at DESC
        """
        cursor.execute(sql, (post_cid,))
        rows = cursor.fetchall()
        comments = []
        for row in rows:
            c = Comment(
                id=row[0],
                user_id=row[1],
                post_cid=row[2],
                content=row[3],
                created_at=row[4],
                username=row[5]
            )
            comments.append(c)
        return comments
    finally:
        cursor.close()
        conn.close()

def count_comments_for_post(post_cid: str) -> int:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT COUNT(*) FROM comments WHERE post_cid = %s"
        cursor.execute(sql, (post_cid,))
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        conn.close()

def count_total_comments_for_username(username: str) -> int:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT COUNT(c.id) 
            FROM comments c
            JOIN posts p ON c.post_cid = p.cid
            JOIN users u ON p.owner_id = u.id
            WHERE u.username = %s
        """
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        conn.close()