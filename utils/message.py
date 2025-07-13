from telegram import Update
from telegram.ext import ContextTypes

async def safe_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    """Универсальный метод отправки сообщений"""
    if update.message:
        await update.message.reply_text(text, **kwargs)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, **kwargs)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            **kwargs
        )