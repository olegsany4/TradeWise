import sys
import logging
import asyncio
logging.basicConfig(level=logging.DEBUG)

from contextlib import suppress
from functools import partial
from redis.asyncio import Redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from config import TELEGRAM_TOKEN, RedisConfig
from handlers.common import start
from handlers.portfolio import portfolio
from handlers.quotes import quotes
from handlers.backtest import backtest
from handlers.order_commands import api_orders, create_order, list_orders, cancel_order, cancel_order_button
from handlers.strategy import (
    strategy,
    SELECT_STRATEGY,
    CONFIGURE_STRATEGY,
    strategy_selection,
    strategy_configuration
)
from handlers.market_data import candles_conv_handler
from utils.ptb_persistence import RedisPersistence
from utils.formatters import format_balance, format_portfolio, format_orders, format_candles
from utils.logger import log_action
from utils.rate_limit import rate_limit
from utils.error_handlers import global_error_handler
from tinkoff_api.accounts import get_or_create_sandbox_account
from tinkoff_api.client import TinkoffClient
from config import USE_SANDBOX, PRIMARY_ACCOUNT_ID
from tinkoff_api.historical import HistoricalData
from tinkoff_api.historical import INTERVAL_MAPPING

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Redis
redis = Redis(
    host=RedisConfig.HOST,
    port=RedisConfig.PORT,
    db=RedisConfig.DB,
    decode_responses=False
)
persistence = RedisPersistence(redis)

# Создание приложения
application = ApplicationBuilder() \
    .token(TELEGRAM_TOKEN) \
    .persistence(persistence) \
    .build()

# Регистрация обработчиков команд
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("portfolio", portfolio))
application.add_handler(CommandHandler("quotes", quotes))
application.add_handler(CommandHandler("backtest", backtest))
application.add_handler(CommandHandler("strategy", strategy))
application.add_handler(CommandHandler("api_orders", api_orders))
application.add_handler(CommandHandler("order", create_order))
application.add_handler(CommandHandler("orders", list_orders))
application.add_handler(CommandHandler("cancelorder", cancel_order))

# Добавляем ConversationHandler для свечей ПЕРЕД общим обработчиком кнопок
application.add_handler(candles_conv_handler)

# FSM для стратегий
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('strategy', strategy)],
    states={
        SELECT_STRATEGY: [
            CallbackQueryHandler(strategy_selection, pattern='^(MA|RSI|Bollinger)$')
        ],
        CONFIGURE_STRATEGY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, strategy_configuration)
        ]
    },
    fallbacks=[CommandHandler('cancel', partial(strategy, cancel=True))],
    # Исправление предупреждения PTBUserWarning
    per_message=True
)
application.add_handler(conv_handler)

# Обработчик ошибок
application.add_error_handler(global_error_handler)

# Обработчик inline-кнопок
@rate_limit()
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        # Пропускаем кнопки свечей - их обрабатывает ConversationHandler
        if query.data.startswith(("candles_ticker_", "candles_interval_")):
            return
            
        if query.data == "balance":
            account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
            client = TinkoffClient(sandbox=USE_SANDBOX)
            portfolio_data = await client.get_portfolio(account_id)
            text = format_balance(portfolio_data)
            await query.edit_message_text(text)
            
        elif query.data == "portfolio":
            account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
            client = TinkoffClient(sandbox=USE_SANDBOX)
            portfolio_data = await client.get_portfolio(account_id)
            text = format_portfolio(portfolio_data)
            await query.edit_message_text(text)
            
        elif query.data == "strategy":
            await strategy(update, context)
            
        elif query.data == "backtest":
            await backtest(update, context)
            
        elif query.data == "orders":
            await list_orders(update, context)
            
        elif query.data == "api_orders":
            account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
            client = TinkoffClient(sandbox=USE_SANDBOX)
            active_orders, executed_orders = await client.get_orders(account_id)
            text = format_orders(active_orders, executed_orders)
            await query.edit_message_text(text)
            
        elif query.data.startswith("cancel_"):
            order_id = int(query.data.split("_")[1])
            await cancel_order_button(update, context, order_id)
            
        elif query.data == "refresh_portfolio":
            await portfolio(update, context)
            
        elif query.data == "launch_strategy":
            await strategy(update, context)
            
        elif query.data == "show_forest":
            await query.edit_message_text("🌲 Ваш лес: 1 дерево! (геймификация)")
            
        # Обработка обновления свечей с новым форматом
        elif query.data.startswith("rcandles_"):
            parts = query.data.split('_')
            
            # Проверка корректности формата
            if len(parts) < 4:
                logger.error(f"Invalid refresh candles format: {query.data}")
                await query.edit_message_text("⚠️ Ошибка формата запроса")
                return
                
            ticker = parts[1]
            interval = parts[2]
            
            try:
                days = int(parts[3])
            except (ValueError, IndexError):
                logger.error(f"Invalid days value: {parts}")
                await query.edit_message_text("⚠️ Некорректное значение дней")
                return
            
            # Показываем сообщение о загрузке
            await query.edit_message_text(f"⏳ Обновляю данные для {ticker}...")
            
            try:
                # Получаем данные
                historical = HistoricalData()
                interval_enum = INTERVAL_MAPPING.get(interval)
                if not interval_enum:
                    await query.edit_message_text("❌ Неверный интервал")
                    return
                    
                candles_data = await historical.get_candles(ticker, interval_enum, days)
                
                if not candles_data:
                    await query.edit_message_text(f"❌ Не удалось получить данные для {ticker}")
                    return
                    
                # Форматируем ответ
                formatted = [historical.format_candle(c) for c in candles_data]
                text = format_candles(ticker, interval, formatted)
                
                # Обновляем сообщение
                keyboard = [
                    [InlineKeyboardButton(
                        "🔄 Обновить", 
                        callback_data=f"rcandles_{ticker}_{interval}_{days}"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup
                )
                
            except Exception as e:
                logger.error(f"Error loading candles for {ticker}: {e}", exc_info=True)
                await query.edit_message_text(f"⚠️ Ошибка при загрузке данных: {str(e)[:100]}")
            
        else:
            await query.edit_message_text("Неизвестная команда.")
            
        await log_action("button_callback", f"Handled: {query.data}", update.effective_user.id)
        
    except Exception as e:
        logger.error(f"Error in button_callback: {e}", exc_info=True)
        await query.edit_message_text("⚠️ Произошла ошибка при обработке запроса")

application.add_handler(CallbackQueryHandler(button_callback))

# Запуск приложения
if __name__ == "__main__":
    application.run_polling()