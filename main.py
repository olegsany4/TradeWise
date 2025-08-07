import sys
import logging
import matplotlib
matplotlib.use('Agg')  # Устанавливаем неинтерактивный бэкенд для matplotlib

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
from handlers.backtest import backtest_command, select_period, show_backtest_graph, PERIOD
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
from utils.logger import log_action, logger
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
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# Инициализация Redis
redis = Redis(
    host=RedisConfig.HOST,
    port=RedisConfig.PORT,
    db=RedisConfig.DB,
    decode_responses=False
)
persistence = RedisPersistence(redis)

# Создание приложения Telegram
application = ApplicationBuilder() \
    .token(TELEGRAM_TOKEN) \
    .persistence(persistence) \
    .build()

# Функция-обертка для обработки входа в стратегию через кнопку
async def strategy_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await strategy(update, context)

# ================================================
# РЕГИСТРАЦИЯ ОСНОВНЫХ ОБРАБОТЧИКОВ КОМАНД
# ================================================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("portfolio", portfolio))
application.add_handler(CommandHandler("quotes", quotes))
application.add_handler(CommandHandler("api_orders", api_orders))
application.add_handler(CommandHandler("order", create_order))
application.add_handler(CommandHandler("orders", list_orders))
application.add_handler(CommandHandler("cancelorder", cancel_order))

# ================================================
# FSM ДЛЯ УПРАВЛЕНИЯ СТРАТЕГИЯМИ
# ================================================
strategy_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('strategy', strategy),
        CallbackQueryHandler(strategy_callback_wrapper, pattern="^strategy$")
    ],
    states={
        SELECT_STRATEGY: [
            CallbackQueryHandler(strategy_selection, pattern="^(MA|RSI|Bollinger)$"),
            CallbackQueryHandler(partial(strategy, cancel=True), pattern="^cancel_config$")
        ],
        CONFIGURE_STRATEGY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, strategy_configuration),
            CallbackQueryHandler(partial(strategy, cancel=True), pattern="^cancel_config$")
        ]
    },
    fallbacks=[CommandHandler('cancel', partial(strategy, cancel=True))],
    name="strategy_conversation"
)
application.add_handler(strategy_conv_handler)

# ================================================
# FSM ДЛЯ БЭКТЕСТИНГА
# ================================================
backtest_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('backtest', backtest_command),
        CallbackQueryHandler(backtest_command, pattern="^backtest$")
    ],
    states={
        PERIOD: [
            CallbackQueryHandler(select_period, pattern="^(30|60|90)$"),
            CallbackQueryHandler(partial(backtest_command, cancel=True), pattern="^cancel_backtest$")
        ]
    },
    fallbacks=[CommandHandler('cancel', partial(backtest_command, cancel=True))],
    name="backtest_conversation"
)
application.add_handler(backtest_conv_handler)

# ConversationHandler для работы со свечными данными
application.add_handler(candles_conv_handler)

# Глобальный обработчик ошибок
application.add_error_handler(global_error_handler)

# ================================================
# ГЛОБАЛЬНЫЙ ОБРАБОТЧИК INLINE-КНОПОК
# ================================================
@rate_limit()
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        logger.debug(f"Получен callback: {query.data}")
        
        # Пропускаем кнопки, которые обрабатываются в ConversationHandler
        skip_patterns = [
            "strategy", "MA", "RSI", "Bollinger",
            "candles_ticker_.*", "candles_interval_.*",
            "backtest", "30", "60", "90", "cancel_backtest"
        ]
        
        if any(query.data.startswith(p.split('*')[0]) for p in skip_patterns):
            logger.debug(f"Пропускаем обработку кнопки: {query.data}")
            return
            
        # Обработка кнопки "show_graph"
        if query.data == "show_graph":
            logger.debug("Обработка запроса show_graph")
            await show_backtest_graph(update, context)
            return

        # Обработка кнопки "activate_real"
        if query.data == "activate_real":
            logger.debug("Обработка запроса activate_real")
            await query.edit_message_text("🚀 Режим реальной торговли будет доступен в следующем обновлении!")
            return

        # Обработка кнопки "balance"
        if query.data == "balance":
            logger.debug("Обработка запроса баланса")
            account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
            client = TinkoffClient(sandbox=USE_SANDBOX)
            portfolio_data = await client.get_portfolio(account_id)
            # Передаем флаг песочницы в форматирование
            text = format_balance(portfolio_data, is_sandbox=USE_SANDBOX)
            await query.edit_message_text(text)

        # Обработка кнопки "portfolio"
        elif query.data == "portfolio":
            logger.debug("Обработка запроса портфеля")
            account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
            client = TinkoffClient(sandbox=USE_SANDBOX)
            portfolio_data = await client.get_portfolio(account_id)
            text = format_portfolio(portfolio_data)
            await query.edit_message_text(text)

        # Обработка кнопки "orders"
        elif query.data == "orders":
            logger.debug("Обработка запроса ордеров")
            await list_orders(update, context)

        # Обработка кнопки "api_orders"
        elif query.data == "api_orders":
            logger.debug("Обработка запроса API-ордеров")
            account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
            client = TinkoffClient(sandbox=USE_SANDBOX)
            active_orders, executed_orders = await client.get_orders(account_id)
            text = format_orders(active_orders, executed_orders)
            await query.edit_message_text(text)

        # Обработка кнопок отмены ордеров
        elif query.data.startswith("cancel_"):
            logger.debug(f"Обработка запроса отмены ордера: {query.data}")
            order_id = int(query.data.split("_")[1])
            await cancel_order_button(update, context, order_id)

        # Обработка кнопки "refresh_portfolio"
        elif query.data == "refresh_portfolio":
            logger.debug("Обработка запроса обновления портфеля")
            await portfolio(update, context)

        # Обработка кнопки "launch_strategy"
        elif query.data == "launch_strategy":
            logger.debug("Обработка запроса запуска стратегии")
            await strategy(update, context)

        # Обработка кнопки "show_forest" (геймификация)
        elif query.data == "show_forest":
            logger.debug("Обработка запроса показа леса")
            await query.edit_message_text("🌲 Ваш лес: 1 дерево! (геймификация)")

        # Обработка кнопок обновления свечных данных
        elif query.data.startswith("rcandles_"):
            logger.debug(f"Обработка запроса обновления свечей: {query.data}")
            parts = query.data.split('_')
            if len(parts) < 4:
                logger.error(f"Неверный формат запроса свечей: {query.data}")
                await query.edit_message_text("⚠️ Ошибка формата запроса")
                return
                
            ticker = parts[1]
            interval = parts[2]
            
            try:
                days = int(parts[3])
            except (ValueError, IndexError):
                logger.error(f"Некорректное значение дней: {parts}")
                await query.edit_message_text("⚠️ Некорректное значение дней")
                return
                
            await query.edit_message_text(f"⏳ Обновляю данные для {ticker}...")
            
            try:
                historical = HistoricalData()
                interval_enum = INTERVAL_MAPPING.get(interval)
                
                if not interval_enum:
                    await query.edit_message_text("❌ Неверный интервал")
                    return
                    
                candles_data = await historical.get_candles(ticker, interval_enum, days)
                
                if not candles_data:
                    await query.edit_message_text(f"❌ Не удалось получить данные для {ticker}")
                    return
                    
                formatted = [historical.format_candle(c) for c in candles_data]
                text = format_candles(ticker, interval, formatted)
                
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
                logger.error(f"Ошибка загрузки свечей для {ticker}: {e}", exc_info=True)
                await query.edit_message_text(f"⚠️ Ошибка при загрузке данных: {str(e)[:100]}")
                
        # Обработка неизвестных команд
        else:
            logger.warning(f"Неизвестная команда: {query.data}")
            await query.edit_message_text("Неизвестная команда.")

        # Логирование успешной обработки
        await log_action("button_callback", f"Обработано: {query.data}", update.effective_user.id)
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}", exc_info=True)
        await query.edit_message_text("⚠️ Произошла ошибка при обработке запроса")

# Регистрация глобального обработчика кнопок
application.add_handler(CallbackQueryHandler(button_callback))

# Запуск приложения
if __name__ == "__main__":
    application.run_polling()