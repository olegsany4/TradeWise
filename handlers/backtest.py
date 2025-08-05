import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from strategies.ma import MovingAverageStrategy
from utils.mocks import generate_mock_prices
from strategies.backtest_utils import plot_backtest_results
from utils.rate_limit import rate_limit
import logging

logger = logging.getLogger(__name__)

# Функция для форматирования параметров стратегии
def format_strategy_params(params: dict) -> str:
    """Преобразует словарь параметров в читаемую строку."""
    return ", ".join(f"{key}={value}" for key, value in params.items())

# Состояния для ConversationHandler бэктеста
PERIOD = 0

@rate_limit(5)
async def backtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Проверяем, настроена ли стратегия
    if 'selected_strategy' not in context.user_data or 'strategy_params' not in context.user_data:
        keyboard = [
            [InlineKeyboardButton("⚙️ Перейти к стратегиям", callback_data="strategy")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Если команда пришла из сообщения
        if update.message:
            await update.message.reply_text(
                "🔄 Сначала выберите стратегию в меню «Стратегии»!",
                reply_markup=reply_markup
            )
        # Если из callback (кнопки)
        else:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "🔄 Сначала выберите стратегию в меню «Стратегии»!",
                reply_markup=reply_markup
            )
        return ConversationHandler.END

    # Предлагаем выбрать период
    keyboard = [
        [
            InlineKeyboardButton("30 дней", callback_data="30"),
            InlineKeyboardButton("60 дней", callback_data="60"),
            InlineKeyboardButton("90 дней", callback_data="90"),
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_backtest")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Получаем информацию о стратегии
    strategy_key = context.user_data['selected_strategy']
    strategy_params = context.user_data['strategy_params']
    strategy_name = STRATEGIES[strategy_key]['name']
    formatted_params = format_strategy_params(strategy_params)
    
    caption = (
        f"⚙️ Стратегия: {strategy_name}\n"
        f"🔧 Параметры: {formatted_params}\n\n"
        f"🕒 Укажите период для бэктестинга:"
    )

    if update.message:
        await update.message.reply_text(caption, reply_markup=reply_markup)
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(caption, reply_markup=reply_markup)

    return PERIOD

async def select_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel_backtest':
        await query.edit_message_text("❌ Бэктест отменён")
        return ConversationHandler.END

    # Сохраняем период
    period_days = int(query.data)
    
    # Получаем параметры стратегии
    strategy_key = context.user_data['selected_strategy']
    strategy_params = context.user_data['strategy_params']
    strategy_name = STRATEGIES[strategy_key]['name']
    formatted_params = format_strategy_params(strategy_params)

    # Информируем о мок-данных
    mock_warning = "\n⚠️ Использую тестовые (мок) данные!" if True else ""  # Здесь можно добавить проверку на реальные данные

    # Запускаем бэктест
    await query.edit_message_text(
        f"⏳ Запускаю бэктест стратегии {strategy_name} ({formatted_params}) "
        f"за {period_days} дней...{mock_warning}"
    )

    # Генерация тестовых данных
    df = generate_mock_prices(days=period_days)
    
    # Создание стратегии на основе выбранного типа
    strategy = None
    min_days = 0  # Минимальное количество дней для расчета стратегии
    
    if strategy_key == "MA":
        # Преобразуем параметры для MA стратегии
        ma_params = {}
        if 'window' in strategy_params:
            # Конвертируем единый параметр window в short_window и long_window
            window = int(strategy_params['window'])
            ma_params = {'short_window': window, 'long_window': window * 3}
            min_days = window * 3  # Для расчета long MA
        else:
            # Используем явно указанные параметры
            short = int(strategy_params.get('short_window', 10))
            long = int(strategy_params.get('long_window', 50))
            ma_params = {'short_window': short, 'long_window': long}
            min_days = max(short, long)
        
        # Проверка достаточности данных
        if period_days < min_days:
            await query.edit_message_text(
                f"⚠️ Для стратегии MA с параметрами {formatted_params} требуется минимум {min_days} дней.\n"
                f"Вы выбрали {period_days} дней. Пожалуйста, выберите больший период."
            )
            return ConversationHandler.END
            
        strategy = MovingAverageStrategy(**ma_params)
        
    elif strategy_key == "RSI":
        # Заглушка для RSI стратегии
        from strategies.rsi import RSIStrategy  # Импорт по необходимости
        min_days = strategy_params.get('period', 14) * 2  # Для расчета RSI
        strategy = RSIStrategy(**strategy_params)
        
        if period_days < min_days:
            await query.edit_message_text(
                f"⚠️ Для стратегии RSI с периодом {min_days//2} требуется минимум {min_days} дней.\n"
                f"Вы выбрали {period_days} дней. Пожалуйста, выберите больший период."
            )
            return ConversationHandler.END
            
    elif strategy_key == "Bollinger":
        # Заглушка для Bollinger стратегии
        from strategies.bollinger import BollingerStrategy
        min_days = strategy_params.get('period', 20) * 2
        strategy = BollingerStrategy(**strategy_params)
        
        if period_days < min_days:
            await query.edit_message_text(
                f"⚠️ Для стратегии Боллинджера с периодом {min_days//2} требуется минимум {min_days} дней.\n"
                f"Вы выбрали {period_days} дней. Пожалуйста, выберите больший период."
            )
            return ConversationHandler.END
    else:
        await query.edit_message_text(f"⚠️ Стратегия {strategy_key} не поддерживается")
        return ConversationHandler.END
    
    # Запуск бэктеста в отдельном потоке
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        results = await loop.run_in_executor(pool, strategy.backtest, df)
        
        # Генерация графика
        buf = await loop.run_in_executor(pool, plot_backtest_results, results)
    
    # Подготовка результатов
    metrics = results['metrics']
    caption = (
        f"📊 Результаты бэктеста ({period_days} дней):\n"
        f"💰 Доходность: {metrics['final_return']:.2%}\n"
        f"📈 Коэффициент Шарпа: {metrics['sharpe']:.2f}\n"
        f"📉 Макс. просадка: {metrics['max_drawdown']:.2%}\n"
        f"🔢 Трейдов: {metrics['total_trades']}"
    )
    
    # Клавиатура с действиями
    keyboard = [
        [InlineKeyboardButton("📈 Показать график", callback_data="show_graph")],
        [InlineKeyboardButton("🔄 Повторить бэктест", callback_data="backtest")],
        [InlineKeyboardButton("↩️ Назад к стратегиям", callback_data="strategy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Сохраняем график для показа по требованию
    context.user_data['backtest_graph'] = buf
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=caption,
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def show_backtest_graph(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if 'backtest_graph' in context.user_data:
        buf = context.user_data['backtest_graph']
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=buf
        )
    else:
        await query.answer("⚠️ График недоступен", show_alert=True)

# Словарь стратегий для использования в бэктесте
STRATEGIES = {
    "MA": {
        "name": "Скользящие средние",
        "params": {"window": "int"},
        "description": "Торговля по пересечению MA"
    },
    "RSI": {
        "name": "Индекс относительной силы",
        "params": {"period": "int", "oversold": "int", "overbought": "int"},
        "description": "Торговля по уровням RSI"
    },
    "Bollinger": {
        "name": "Полосы Боллинджера",
        "params": {"period": "int", "deviation": "float"},
        "description": "Торговля по волатильности"
    }
}