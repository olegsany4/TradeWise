from telegram import Update
from telegram.ext import ContextTypes
from strategies.ma import MovingAverageStrategy
from utils.rate_limit import rate_limit

@rate_limit()
async def strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите стратегию: MA, RSI, Bollinger Bands")
    # FSM/Inline-клавиатура для выбора и настройки
