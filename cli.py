import argparse
from server import manager as server_manager

def main():
    parser = argparse.ArgumentParser(description="MegaCite CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- mc-server ---
    server_parser = subparsers.add_parser("server", help="Server management")
    server_subs = server_parser.add_subparsers(dest="action", required=True)
    start_parser = server_subs.add_parser("start", help="Start the server")
    start_parser.add_argument("port", type=int, help="Port to listen on")

    args = parser.parse_args()

    if args.command == "server":
        if args.action == "start":
            server_manager.server_start(args.port)

if __name__ == "__main__":
    main()