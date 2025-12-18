import os

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "114514",
    "database": "megacite",
    "charset": "utf8mb4"
}

SERVER_CONFIG = {
    "host": "127.0.0.1",
    "port": 8080
}

OPENAI_CONFIG = {
    "api_key": os.getenv("MC_API_KEY"),
    "base_url": "https://api.moonshot.cn/v1",
    "model": "moonshot-v1-32k"
}