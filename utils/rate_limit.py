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
            # Универсальный user_id (и для callback, и для message)
            user_id = None
            if update.effective_user:
                user_id = update.effective_user.id
            elif update.callback_query and update.callback_query.from_user:
                user_id = update.callback_query.from_user.id

            if not user_id:
                # Если вдруг не нашли user_id, просто пропускаем rate_limit
                return await func(update, context, *args, **kwargs)

            now = time.time()
            redis_key = f"rate_limit:{user_id}"

            # Проверяем время последнего запроса в Redis
            last_time = await redis.get(redis_key)

            if last_time:
                last_time = float(last_time)
                if now - last_time < limit:
                    # Ответ пользователю — и в message, и в callback
                    if update.message:
                        await update.message.reply_text(f"⏳ Слишком частые запросы! Подождите {limit} секунд")
                    elif update.callback_query:
                        await update.callback_query.answer(
                            f"⏳ Слишком частые запросы! Подождите {limit} секунд", 
                            show_alert=True
                        )
                    return

            # Обновляем время запроса
            await redis.setex(redis_key, int(limit * 2), now)

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator