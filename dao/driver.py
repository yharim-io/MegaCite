import pymysql
import pymysql.cursors

def get_mysql_connection(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    charset: str = "utf8mb4",
) -> pymysql.connections.Connection:
    """
    建立并返回一个 pymysql MySQL 连接。
    """
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=charset,
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False,
    )
    return conn