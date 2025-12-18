import os
from dao import (
    get_mysql_connection,
    MySQLUserDAO,
    MySQLAuthDAO,
    MySQLPostDAO,
    MySQLPostReferenceDAO,
)

def main():
    conn = get_mysql_connection(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="114514",
        database="megacite",
    )

    try:
        user_dao = MySQLUserDAO(conn)
        auth_dao = MySQLAuthDAO(conn)
        post_dao = MySQLPostDAO(conn)
        ref_dao = MySQLPostReferenceDAO(conn)

        # UserDAO Example
        user_id = user_dao.create_user("alice", "hashed_pw_alice")
        user = user_dao.get_user_by_username("alice")
        updated = user_dao.update_user(user_id, {"token": "tok123"})

        # AuthDAO Example
        auth_dao.add_platform_auth(user_id, "csdn", "csdn_token_abc")
        platforms = auth_dao.list_platform_auths(user_id)
        auth_dao.remove_platform_auth(user_id, "csdn")

        # PostDAO Example
        cid1 = "post-cid-1"
        post_dao.create_post(user_id, cid1)
        post_dao.update_field(cid1, "title", "Hello World")
        cids = post_dao.list_posts(0, 10)
        
        cid2 = "post-cid-2"
        post_dao.create_post(user_id, cid2)
        
        # ReferenceDAO Example
        ref_dao.add_reference(cid1, cid2)
        refs = ref_dao.list_references(cid1)

        # Cleanup
        post_dao.delete_post(cid1)
        post_dao.delete_post(cid2)
        user_dao.delete_user(user_id)

    finally:
        conn.close()

if __name__ == "__main__":
    main()