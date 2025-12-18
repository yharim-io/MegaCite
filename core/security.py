import hashlib
import uuid
import secrets
import string

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def generate_token() -> str:
    return uuid.uuid4().hex

def generate_cid(length=11) -> str:
    """生成指定长度的随机 alphanumeric 字符串作为 CID"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))