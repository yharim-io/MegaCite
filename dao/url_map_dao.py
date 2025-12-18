import pymysql.connections

class MySQLUrlMapDAO:
    """维护 URL 到 CID 的双向映射。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def upsert_mapping(self, cid: str, url_path: str) -> None:
        """插入或更新映射。url_path 必须以 / 开头，例如 /user/title.html"""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO url_mappings (cid, url_path) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE url_path = %s",
                (cid, url_path, url_path),
            )
        self.conn.commit()

    def get_cid_by_url(self, url_path: str) -> str | None:
        """通过 URL 查找 CID。"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT cid FROM url_mappings WHERE url_path = %s", (url_path,))
            row = cur.fetchone()
        return row[0] if row else None

    def get_url_by_cid(self, cid: str) -> str | None:
        """通过 CID 查找 URL。"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT url_path FROM url_mappings WHERE cid = %s", (cid,))
            row = cur.fetchone()
        return row[0] if row else None