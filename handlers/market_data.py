from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from tinkoff_api.historical import HistoricalData, INTERVAL_MAPPING  # Импортируем INTERVAL_MAPPING напрямую
from utils.logger import logger

SELECT_TICKER, SELECT_INTERVAL = range(2)

TICKERS = ["SBER", "GAZP", "TCSG"]
INTERVALS = ["1min", "5min", "15min", "hour", "day"]

async def candles_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [[InlineKeyboardButton(t, callback_data=f"candles_ticker_{t}")] for t in TICKERS]
        query = update.callback_query
        if query:
            await query.edit_message_text(
                "Выберите тикер:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.effective_message.reply_text(
                "Выберите тикер:",
                reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_TICKER
    except Exception as e:
        logger.error(f"Error in candles_start: {e}", exc_info=True)
        if update.callback_query:
            await update.callback_query.edit_message_text(f"Ошибка при запуске сценария свечей")
        else:
            await update.effective_message.reply_text(f"Ошибка при запуске сценария свечей")
        return ConversationHandler.END

async def select_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split("_", 2)
        if len(parts) != 3 or not parts[2]:
            await query.edit_message_text(f"Ошибка: некорректный формат данных для тикера")
            return ConversationHandler.END
        ticker = parts[2]
        context.user_data["candles_ticker"] = ticker
        keyboard = [[InlineKeyboardButton(i, callback_data=f"candles_interval_{i}")] for i in INTERVALS]
        await query.edit_message_text(
            f"Тикер: {ticker}\nВыберите интервал:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_INTERVAL
    except Exception as e:
        logger.error(f"Error in select_ticker: {e}", exc_info=True)
        await query.edit_message_text(f"Ошибка при выборе тикера")
        return ConversationHandler.END

async def select_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split("_", 2)
        if len(parts) != 3 or not parts[2]:
            await query.edit_message_text("❌ Неверный интервал")
            return ConversationHandler.END
        interval = parts[2]
        ticker = context.user_data.get("candles_ticker", "?")
        
        # Сразу показываем сообщение о загрузке
        await query.edit_message_text(f"⏳ Загружаю свечи для {ticker} с интервалом {interval}...")
        
        try:
            # Загружаем данные напрямую
            historical = HistoricalData()
            # Используем глобальный INTERVAL_MAPPING вместо атрибута класса
            interval_enum = INTERVAL_MAPPING.get(interval)
            if not interval_enum:
                await query.edit_message_text("❌ Неверный интервал")
                return ConversationHandler.END
                
            candles_data = await historical.get_candles(ticker, interval_enum, 7)
            
            if not candles_data:
                await query.edit_message_text(f"❌ Не удалось получить данные для {ticker}")
                return ConversationHandler.END
                
            # Форматируем ответ
            formatted = [historical.format_candle(c) for c in candles_data]
            text = f"📊 Свечи {ticker} ({interval}):\n" + "\n".join(formatted[-10:])
            
            # Создаем кнопку обновления
            refresh_button = InlineKeyboardButton(
                "🔄 Обновить", 
                callback_data=f"rcandles_{ticker}_{interval}_7" 
            )
            reply_markup = InlineKeyboardMarkup([[refresh_button]])
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error loading candles in select_interval: {e}", exc_info=True)
            await query.edit_message_text(f"⚠️ Ошибка при загрузке данных: {str(e)[:100]}")
            
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in select_interval: {e}", exc_info=True)
        await query.edit_message_text(f"Ошибка при выборе интервала")
        return ConversationHandler.END

candles_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(candles_start, pattern="^candles_start$")],
    states={
        SELECT_TICKER: [CallbackQueryHandler(select_ticker, pattern="^candles_ticker_.*")],
        SELECT_INTERVAL: [CallbackQueryHandler(select_interval, pattern="^candles_interval_.*")],
    },
    fallbacks=[],
    # Исправление предупреждения PTBUserWarning
    per_message=True
)