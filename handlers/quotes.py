from telegram import Update
from telegram.ext import ContextTypes
from tinkoff_api.instruments import InstrumentCache
from utils.rate_limit import rate_limit

@rate_limit()
async def quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils.logger import log_action
    await log_action("quotes_command", "User requested quotes", update.effective_user.id)
    
    # Используем кэш инструментов
    cache = InstrumentCache()
    instruments = await cache.get_instruments()
    
    # Формируем список инструментов
    text_lines = []
    count = 0
    for ticker, data in instruments.items():
        if count >= 10:
            break
        text_lines.append(f"{ticker}: {data['name']}")
        count += 1
    
    await update.message.reply_text(f"Доступные инструменты (пример):\n" + "\n".join(text_lines))