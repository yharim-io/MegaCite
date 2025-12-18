import argparse
import sys
from core import auth, post
from server import manager as server_manager
from client import login_store
import crawler
# 新增验证模块
from verification import manager as verify_manager

def main():
    parser = argparse.ArgumentParser(description="MegaCite CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- mc-server ---
    server_parser = subparsers.add_parser("server", help="Server management")
    server_subs = server_parser.add_subparsers(dest="action", required=True)
    start_parser = server_subs.add_parser("start", help="Start the server")
    start_parser.add_argument("port", type=int, help="Port to listen on")

    # --- user ---
    user_parser = subparsers.add_parser("user", help="User management")
    user_subs = user_parser.add_subparsers(dest="action", required=True)
    
    reg_parser = user_subs.add_parser("register", help="Register a new user")
    reg_parser.add_argument("username", help="Username")
    reg_parser.add_argument("password", help="Password")

    login_parser = user_subs.add_parser("login", help="Login to system")
    login_parser.add_argument("username", help="Username")
    login_parser.add_argument("password", help="Password")

    user_subs.add_parser("logout", help="Logout from system")

    # [新增] 修改密码命令
    passwd_parser = user_subs.add_parser("password", help="Change password")
    passwd_parser.add_argument("old_password", help="Current password")
    passwd_parser.add_argument("new_password", help="New password")

    # --- auth (New) ---
    auth_parser = subparsers.add_parser("auth", help="External platform authentication")
    auth_subs = auth_parser.add_subparsers(dest="action", required=True)

    auth_add = auth_subs.add_parser("add", help="Add platform authentication")
    auth_add.add_argument("platform", help="Platform name (e.g., csdn)")
    
    auth_clear = auth_subs.add_parser("clear", help="Clear platform authentication cookies")
    auth_clear.add_argument("platform", help="Platform name (e.g., csdn)")

    # --- post ---
    post_parser = subparsers.add_parser("post", help="Post management")
    post_subs = post_parser.add_subparsers(dest="action", required=True)
    
    list_p = post_subs.add_parser("list", help="List posts")
    list_p.add_argument("count", nargs="?", type=int, default=None)
    
    post_subs.add_parser("create", help="Create a post")
    
    update_p = post_subs.add_parser("update", help="Update post")
    update_p.add_argument("cid")
    update_p.add_argument("field", choices=["title", "context", "description", "category", "date"])
    update_p.add_argument("value")
    
    delete_p = post_subs.add_parser("delete", help="Delete post")
    delete_p.add_argument("cid")
    
    get_p = post_subs.add_parser("get", help="Get field")
    get_p.add_argument("cid")
    get_p.add_argument("field")
    
    search_p = post_subs.add_parser("search", help="Search")
    search_p.add_argument("keyword")

    migrate_p = post_subs.add_parser("migrate", help="Migrate post from URL")
    migrate_p.add_argument("url")

    args = parser.parse_args()

    try:
        if args.command == "server":
            if args.action == "start":
                server_manager.server_start(args.port)

        elif args.command == "user":
            if args.action == "register":
                uid = auth.user_register(args.username, args.password)
                print(f"User registered. ID: {uid}")
            elif args.action == "login":
                token = auth.user_login(args.username, args.password)
                login_store.save_local_token(token)
                print("Login successful.")
            elif args.action == "logout":
                login_store.clear_local_token()
                print("Logged out.")
            elif args.action == "password":
                # [新增] 修改密码逻辑
                token = login_store.load_local_token()
                if not token:
                    print("Error: Please login first.")
                else:
                    auth.change_password(token, args.old_password, args.new_password)
                    print("Password changed successfully.")

        # 处理 Auth 命令
        elif args.command == "auth":
            if args.action == "add":
                verify_manager.login_platform(args.platform)
            elif args.action == "clear":
                from client.cookie_store import clear_cookies
                clear_cookies(args.platform)
                print(f"Cleared cookies for {args.platform}")

        elif args.command == "post":
            token = login_store.load_local_token()
            
            if args.action == "list":
                print(f"Posts: {post.post_list(token, args.count)}")
            
            elif args.action == "create":
                new_cid = post.post_create(token)
                print(f"Post created. CID: {new_cid}")
            
            elif args.action == "update":
                value = args.value.replace("\\n", "\n")
                ok = post.post_update(token, args.cid, args.field, value)
                print("Success" if ok else "Failed")
            
            elif args.action == "delete":
                ok = post.post_delete(token, args.cid)
                print("Success" if ok else "Failed")
            
            elif args.action == "get":
                print(f"{args.field}: {post.post_get(token, args.cid, args.field)}")
            
            elif args.action == "search":
                print(f"Results: {post.post_search(token, args.keyword)}")

            elif args.action == "migrate":
                cid = crawler.migrate_post_from_url(token, args.url)
                if cid:
                    print(f"Migration successful. CID: {cid}")

    except PermissionError as e:
        print(f"Permission Denied: {e}")
    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()