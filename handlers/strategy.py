from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.rate_limit import rate_limit
from utils.logger import log_action, logger
from utils.formatters import format_strategy_params

# Состояния FSM
SELECT_STRATEGY, CONFIGURE_STRATEGY = range(2)

# Доступные стратегии
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

@rate_limit()
async def strategy(update: Update, context: ContextTypes.DEFAULT_TYPE, cancel: bool = False):
    message = update.effective_message
    if cancel:
        await message.reply_text("❌ Настройка стратегии отменена")
        return ConversationHandler.END
        
    await log_action("strategy_command", "User requested strategy selection", update.effective_user.id)
    
    # Создаем клавиатуру с выбором стратегии
    keyboard = [
        [InlineKeyboardButton("Скользящие средние (MA)", callback_data="MA")],
        [InlineKeyboardButton("Индекс RSI", callback_data="RSI")],
        [InlineKeyboardButton("Полосы Боллинджера", callback_data="Bollinger")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        "📊 Выберите торговую стратегию:",
        reply_markup=reply_markup
    )
    
    return SELECT_STRATEGY

async def strategy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    strategy_key = query.data
        
    # Сохраняем выбор стратегии в контексте
    context.user_data["selected_strategy"] = strategy_key
    strategy_info = STRATEGIES[strategy_key]
    
    # Формируем инструкцию для параметров
    params_desc = "\n".join([
        f"{param} ({meta}):" 
        for param, meta in strategy_info["params"].items()
    ])
    
    await query.edit_message_text(
        f"⚙️ Настройка {strategy_info['name']}:\n\n"
        f"{strategy_info['description']}\n\n"
        f"Введите параметры в формате:\n"
        f"{params_desc}\n\n"
        f"Пример: window=20"
    )
    
    return CONFIGURE_STRATEGY

async def strategy_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    strategy_key = context.user_data["selected_strategy"]
    strategy_info = STRATEGIES[strategy_key]
    
    try:
        # Парсим параметры
        params = {}
        for item in user_input.split():
            key, value = item.split('=')
            param_type = strategy_info["params"][key]
            
            if param_type == "int":
                params[key] = int(value)
            elif param_type == "float":
                params[key] = float(value)
            else:
                params[key] = value
                
        # Сохраняем параметры
        context.user_data["strategy_params"] = params
        
        # Форматируем подтверждение
        formatted_params = format_strategy_params(params)
        await update.effective_message.reply_text(
            f"✅ Стратегия {strategy_info['name']} настроена:\n\n"
            f"{formatted_params}\n\n"
            f"Используйте /backtest для тестирования"
        )
        
        await log_action(
            "strategy_configured", 
            f"{strategy_key} with params: {params}", 
            update.effective_user.id
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Strategy config error: {e}")
        await update.effective_message.reply_text(
            "❌ Ошибка в формате параметров. Попробуйте еще раз или введите /cancel"
        )
        return CONFIGURE_STRATEGY