from dataclasses import dataclass
from datetime import date

@dataclass
class User:
    id: int
    username: str
    password_hash: str


@dataclass
class Post:
    cid: str
    owner_id: int
    title: str | None
    context: str | None
    description: str | None
    category: str | None
    date: date