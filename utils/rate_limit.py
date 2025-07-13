import asyncio
import time
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from redis.asyncio import Redis
from config import RedisConfig

# Инициализация Redis
redis = Redis(
    host=RedisConfig.HOST,
    port=RedisConfig.PORT,
    db=RedisConfig.DB,
    decode_responses=True
)

RATE_LIMIT_SECONDS = 0.5

def rate_limit(limit=RATE_LIMIT_SECONDS):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            now = time.time()
            
            # Проверяем время последнего запроса в Redis
            last_time = await redis.get(f"rate_limit:{user_id}")
            
            if last_time:
                last_time = float(last_time)
                if now - last_time < limit:
                    if update.message:
                        await update.message.reply_text("⏳ Слишком частые запросы! Подождите 0.5 секунды")
                    return
            
            # Обновляем время запроса
            await redis.setex(f"rate_limit:{user_id}", int(limit * 2), now)
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator