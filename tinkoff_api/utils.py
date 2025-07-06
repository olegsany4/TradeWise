import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import TELEGRAM_TOKEN

# Декоратор для авторизации по Telegram ID
ALLOWED_USERS = set()

def authorized(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if ALLOWED_USERS and user_id not in ALLOWED_USERS:
            await update.message.reply_text("Нет доступа.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# Логгер
logger = logging.getLogger("tradewise")
logging.basicConfig(level=logging.INFO)
