from telegram import Update
from telegram.ext import ContextTypes
from tinkoff_api.instruments import get_instruments

async def quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instruments = await get_instruments()
    text = '\n'.join([f"{i.figi}: {i.ticker}" for i in instruments.instruments[:10]])
    await update.message.reply_text(f"Доступные инструменты (пример):\n{text}")
