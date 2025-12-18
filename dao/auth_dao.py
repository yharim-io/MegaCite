import pymysql.connections

class MySQLAuthDAO:
    """MySQL 实现的 AuthDAO。"""

    def __init__(self, conn: pymysql.connections.Connection):
        self.conn = conn

    def add_platform_auth(self, user_id: int, platform: str, credential: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO auth_platforms (user_id, platform, credential) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE credential = %s",
                (user_id, platform, credential, credential),
            )
        self.conn.commit()

    def remove_platform_auth(self, user_id: int, platform: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM auth_platforms WHERE user_id = %s AND platform = %s",
                (user_id, platform),
            )
            deleted = cur.rowcount
        self.conn.commit()
        return deleted > 0

    def list_platform_auths(self, user_id: int) -> list[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT platform FROM auth_platforms WHERE user_id = %s", (user_id,))
            rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []

    def get_platform_credential(self, user_id: int, platform: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT credential FROM auth_platforms WHERE user_id = %s AND platform = %s",
                (user_id, platform),
            )
            row = cur.fetchone()
        return row[0] if row else None