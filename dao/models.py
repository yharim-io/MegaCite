from dataclasses import dataclass
from datetime import date

@dataclass
class User:
    def __init__(self, id, username, password_hash, created_at=None, email=None, **kwargs):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at
        self.email = email
        # 兼容性设计：忽略多余的 kwargs 参数（防止数据库字段变动导致报错）


@dataclass
class Post:
    cid: str
    owner_id: int
    title: str | None
    context: str | None
    description: str | None
    category: str | None
    date: date