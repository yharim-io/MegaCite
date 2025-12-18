import json
import os
from pathlib import Path

# Cookie 存储在用户主目录下，按用户名隔离
COOKIE_FILE = Path.home() / ".megacite_cookies"

def _load_all_data() -> dict:
    if not COOKIE_FILE.exists():
        return {}
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def _save_all_data(data: dict) -> None:
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    if os.name == 'posix':
        os.chmod(COOKIE_FILE, 0o600)

def save_cookies(user_id: int, platform: str, cookies: list[dict]) -> None:
    """保存 Cookie，按 user_id 隔离"""
    data = _load_all_data()
    uid_str = str(user_id)
    
    if uid_str not in data:
        data[uid_str] = {}
    
    data[uid_str][platform] = cookies
    _save_all_data(data)

def load_cookies(user_id: int, platform: str) -> list[dict] | None:
    """加载指定用户的 Cookie"""
    data = _load_all_data()
    uid_str = str(user_id)
    
    return data.get(uid_str, {}).get(platform)

def clear_cookies(user_id: int, platform: str) -> None:
    data = _load_all_data()
    uid_str = str(user_id)
    
    if uid_str in data and platform in data[uid_str]:
        del data[uid_str][platform]
        _save_all_data(data)