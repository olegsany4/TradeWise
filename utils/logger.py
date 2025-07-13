import logging
import datetime
from sqlalchemy.exc import SQLAlchemyError

# Настройка стандартного логгера для консоли
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("tradewise")

async def log_action(action, details, user_id=None):
    # Лог в консоль
    logger.info(f"ACTION: {action} | USER: {user_id} | DETAILS: {details}")
    
    # Отложенный импорт для избежания циклических зависимостей
    try:
        from db.session import async_session
        from db.models import ActionLog
        
        # Лог в БД
        async with async_session() as session:
            log_entry = ActionLog(
                user_id=user_id,
                action=action,
                details=details,
                created_at=datetime.datetime.utcnow()
            )
            session.add(log_entry)
            await session.commit()
    except ImportError as e:
        logger.error(f"Import error in logger: {e}")
    except SQLAlchemyError as e:
        logger.error(f"DB LOGGING ERROR: {e}")