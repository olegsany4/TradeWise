import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TINKOFF_TOKEN = os.getenv("TINKOFF_TOKEN")
USE_SANDBOX = os.getenv("USE_SANDBOX", "True").lower() in ("true", "1", "yes")
PRIMARY_ACCOUNT_ID = os.getenv("PRIMARY_ACCOUNT_ID")
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./tradewise.db")

class RedisConfig:
    HOST = os.getenv("REDIS_HOST", "localhost")
    PORT = int(os.getenv("REDIS_PORT", 6379))
    DB = int(os.getenv("REDIS_DB", 0))
