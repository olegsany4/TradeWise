from telegram import Update
from telegram.ext import ContextTypes
from utils.rate_limit import rate_limit

@rate_limit()
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Доступные команды: /portfolio, /buy, /backtest")
