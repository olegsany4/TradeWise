import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TINKOFF_TOKEN = os.getenv("TINKOFF_TOKEN")
USE_SANDBOX = os.getenv("USE_SANDBOX", "True").lower() in ("true", "1", "yes")
PRIMARY_ACCOUNT_ID = os.getenv("PRIMARY_ACCOUNT_ID")
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./tradewise.db")
