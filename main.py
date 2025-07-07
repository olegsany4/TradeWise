import sys
import logging
try:
    from redis.asyncio import Redis
except ImportError:
    logging.critical("Требуется библиотека redis: pip install redis")
    sys.exit(1)

from telegram.ext import ApplicationBuilder, CommandHandler
from config import TELEGRAM_TOKEN
from handlers.common import start
from handlers.portfolio import portfolio
from handlers.quotes import quotes
from handlers.backtest import backtest
from handlers.strategy import strategy
from utils.ptb_persistence import RedisPersistence

redis = Redis(host='localhost', port=6379, db=0)
persistence = RedisPersistence(redis)

application = ApplicationBuilder() \
    .token(TELEGRAM_TOKEN) \
    .persistence(persistence) \
    .build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("portfolio", portfolio))
application.add_handler(CommandHandler("quotes", quotes))
application.add_handler(CommandHandler("backtest", backtest))
application.add_handler(CommandHandler("strategy", strategy))

def main():
    application.run_polling()

if __name__ == "__main__":
    main()
