import os
from pathlib import Path

TOKEN_FILE = Path.home() / ".megacite_token"

def save_local_token(token: str) -> None:
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(token)

def load_local_token() -> str | None:
    if not TOKEN_FILE.exists():
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None

def clear_local_token() -> None:
    if TOKEN_FILE.exists():
        os.remove(TOKEN_FILE)