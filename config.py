import os
from dotenv import load_dotenv

load_dotenv()

class RedisConfig:
    HOST = os.getenv("REDIS_HOST", "localhost")
    PORT = int(os.getenv("REDIS_PORT", 6379))
    DB = int(os.getenv("REDIS_DB", 0))

# Telegram Bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Tinkoff Invest API
USE_SANDBOX = os.getenv("USE_SANDBOX", "True").lower() == "true"
PRIMARY_ACCOUNT_ID = os.getenv("PRIMARY_ACCOUNT_ID")

# Раздельные ключи для разных режимов
TINKOFF_SANDBOX_TOKEN = os.getenv("TINKOFF_SANDBOX_TOKEN")
TINKOFF_REAL_TOKEN = os.getenv("TINKOFF_REAL_TOKEN")

# Выбор токена в зависимости от режима
TINKOFF_TOKEN = TINKOFF_SANDBOX_TOKEN if USE_SANDBOX else TINKOFF_REAL_TOKEN

# Webhook settings
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-domain.com")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 8443))

# Database
DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trades.db")