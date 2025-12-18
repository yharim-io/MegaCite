from dao.factory import create_connection
from dao.post_dao import MySQLPostDAO
from dao.reference_dao import MySQLPostReferenceDAO

def update_post_content_in_db(post_cid: str, old_str: str, new_str: str):
    """
    仅更新文章的正文内容。
    用于将 markdown 中的 http 链接替换为内部引用格式。
    """
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        current_context = dao.get_field(post_cid, "context") or ""
        new_context = current_context.replace(old_str, new_str)
        if new_context != current_context:
            dao.update_field(post_cid, "context", new_context)
            print(f"[Renderer] DB Content Updated for {post_cid}")
    finally:
        conn.close()

def update_post_references_in_db(post_cid: str, refs: set):
    """
    覆盖式重建文章的引用关系表。
    """
    conn = create_connection()
    try:
        ref_dao = MySQLPostReferenceDAO(conn)
        ref_dao.update_references(post_cid, refs)
    finally:
        conn.close()