
import logging
import random
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def refresh_candles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обновляет данные по свечам при нажатии на кнопку "🔄 Обновить".
    """
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split("_")
        if len(parts) < 4:
            await query.edit_message_text("❌ Неверный диапазон/интервал")
            return
        _, ticker, interval, days = parts[:4]
        await query.edit_message_text(
            f"⏳ Обновляю данные для {ticker}..."
        )
        # Генерируем случайные данные для примера
        candles_data = [
            f"{ticker} {interval} {days} | open: {random.randint(90, 110)} | close: {random.randint(90, 110)} | high: {random.randint(110, 120)} | low: {random.randint(80, 90)} | vol: {random.randint(900, 1100)}"
            for _ in range(3)
        ]
        text = f"📊 Свечи для {ticker} ({interval}) за {days} дн.\n" + "\n".join(candles_data)
        refresh_button = InlineKeyboardButton(
            "🔄 Обновить",
            callback_data=f"rcandles_{ticker}_{interval}_{days}"
        )
        reply_markup = InlineKeyboardMarkup([[refresh_button]])
        await query.edit_message_text(
            text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error("Ошибка в refresh_candles: %s", e, exc_info=True)
        await query.edit_message_text(f"⚠️ Произошла ошибка: {e}")
