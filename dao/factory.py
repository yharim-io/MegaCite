import pymysql
from core.config import DB_CONFIG
from dao.driver import get_mysql_connection

def create_connection() -> pymysql.connections.Connection:
    """
    根据 core/config.py 的配置创建一个新的数据库连接。
    调用者有责任在使用完毕后关闭连接。
    """
    return get_mysql_connection(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"]
    )