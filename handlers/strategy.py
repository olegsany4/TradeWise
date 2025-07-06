from telegram import Update
from telegram.ext import ContextTypes
from strategies.ma import MovingAverageStrategy

async def strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите стратегию: MA, RSI, Bollinger Bands")
    # FSM/Inline-клавиатура для выбора и настройки
