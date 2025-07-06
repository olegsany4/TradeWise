import asyncio
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_TOKEN
from handlers.common import start
from handlers.portfolio import portfolio
from handlers.quotes import quotes
from handlers.backtest import backtest
from handlers.strategy import strategy

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("quotes", quotes))
    app.add_handler(CommandHandler("backtest", backtest))
    app.add_handler(CommandHandler("strategy", strategy))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
