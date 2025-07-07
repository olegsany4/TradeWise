import asyncio
import time
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# Простая реализация rate-limiting на пользователя
user_timestamps = {}

RATE_LIMIT_SECONDS = 0.5

def rate_limit(limit=RATE_LIMIT_SECONDS):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            now = time.monotonic()
            last_time = user_timestamps.get(user_id, 0)
            if now - last_time < limit:
                await update.message.reply_text("Слишком часто! Подождите немного.")
                return
            user_timestamps[user_id] = now
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
