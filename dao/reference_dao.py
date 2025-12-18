import pymysql.connections

class MySQLPostReferenceDAO:
    """MySQL 实现的 PostReferenceDAO。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def add_reference(self, post_cid: str, ref_cid: str) -> None:
        """(旧接口保留) 单个添加"""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO post_references (post_cid, ref_cid) VALUES (%s, %s)",
                (post_cid, ref_cid),
            )
        self.conn.commit()

    def remove_reference(self, post_cid: str, ref_cid: str) -> None:
        """(旧接口保留) 单个删除"""
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM post_references WHERE post_cid = %s AND ref_cid = %s",
                (post_cid, ref_cid),
            )
        self.conn.commit()

    def list_references(self, post_cid: str) -> list[str]:
        """列出文章引用的对象"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT ref_cid FROM post_references WHERE post_cid = %s", (post_cid,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []

    def update_references(self, post_cid: str, ref_cids: set[str]) -> None:
        """
        覆盖式重建引用关系：先清空该文章的所有引用，再批量插入新的。
        """
        with self.conn.cursor() as cur:
            # 1. 清除旧引用
            cur.execute("DELETE FROM post_references WHERE post_cid = %s", (post_cid,))
            
            # 2. 批量插入新引用
            if ref_cids:
                values = [(post_cid, ref) for ref in ref_cids]
                cur.executemany(
                    "INSERT INTO post_references (post_cid, ref_cid) VALUES (%s, %s)",
                    values
                )
        self.conn.commit()

    def get_referencing_posts(self, ref_cid: str) -> list[str]:
        """
        反向查找：找出所有引用了 ref_cid 的文章（post_cid）。
        用于当 ref_cid 的 URL 发生变化时，通知这些文章重新渲染。
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT post_cid FROM post_references WHERE ref_cid = %s", (ref_cid,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []