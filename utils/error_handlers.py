import logging
from telegram import Update
from telegram.ext import ContextTypes
import sentry_sdk

logger = logging.getLogger(__name__)

async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок"""
    error = context.error
    logger.error(f"Exception while handling update: {error}", exc_info=True)
    
    # Отправляем ошибку в Sentry
    if hasattr(context, 'sentry_event_id'):
        sentry_sdk.capture_exception(error)
    
    # Уведомляем пользователя
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла техническая ошибка. Разработчики уже уведомлены!"
        )