from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.rate_limit import rate_limit
from utils.logger import log_action, logger
from utils.formatters import format_strategy_params
from functools import partial

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
    # Универсальное получение chat_id через effective_chat
    chat_id = update.effective_chat.id

    if cancel:
        await context.bot.send_message(chat_id, "❌ Настройка стратегии отменена")
        return ConversationHandler.END

    await log_action("strategy_command", "User requested strategy selection", update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("Скользящие средние (MA)", callback_data="MA")],
        [InlineKeyboardButton("Индекс RSI", callback_data="RSI")],
        [InlineKeyboardButton("Полосы Боллинджера", callback_data="Bollinger")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_config")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="📊 Выберите торговую стратегию:",
        reply_markup=reply_markup
    )
    return SELECT_STRATEGY

async def strategy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    strategy_key = query.data

    # Обработка отмены
    if strategy_key == "cancel_config":
        await query.edit_message_text("❌ Настройка стратегии отменена")
        return ConversationHandler.END

    context.user_data["selected_strategy"] = strategy_key
    strategy_info = STRATEGIES[strategy_key]

    # Создаем клавиатуру с кнопкой отмены
    keyboard = [
        [InlineKeyboardButton("❌ Отменить настройку", callback_data="cancel_config")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем список параметров
    params_list = "\n".join([f"- {param} ({param_type})" 
                            for param, param_type in strategy_info["params"].items()])
    
    # Формируем пример ввода
    example = "window=20" if strategy_key == "MA" else \
              "period=14 oversold=30 overbought=70" if strategy_key == "RSI" else \
              "period=20 deviation=2.0"

    await query.edit_message_text(
        f"⚙️ Настройка {strategy_info['name']}:\n\n"
        f"{strategy_info['description']}\n\n"
        f"🔧 Параметры:\n{params_list}\n\n"
        f"📝 Введите параметры в формате:\n"
        f"параметр=значение [параметр=значение...]\n\n"
        f"Пример: {example}",
        reply_markup=reply_markup
    )
    return CONFIGURE_STRATEGY

async def strategy_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    strategy_key = context.user_data.get("selected_strategy")
    strategy_info = STRATEGIES.get(strategy_key)
    
    if not strategy_info:
        await update.message.reply_text("❌ Стратегия не выбрана. Начните заново /strategy")
        return ConversationHandler.END

    try:
        params = {}
        # Улучшенный парсинг параметров с поддержкой пробелов
        for item in user_input.split():
            if '=' not in item:
                continue  # Пропускаем некорректные части
                
            key, value = [part.strip() for part in item.split('=', 1)]
            
            if key not in strategy_info["params"]:
                continue  # Пропускаем неизвестные параметры
                
            param_type = strategy_info["params"][key]
            try:
                if param_type == "int":
                    params[key] = int(value)
                    # Дополнительная валидация для MA
                    if strategy_key == "MA" and key == "window" and (params[key] < 2 or params[key] > 200):
                        await update.message.reply_text("⚠️ Значение window должно быть от 2 до 200")
                        return CONFIGURE_STRATEGY
                elif param_type == "float":
                    params[key] = float(value)
                else:
                    params[key] = value
            except ValueError:
                await update.message.reply_text(f"❌ Некорректное значение для {key}. Ожидается {param_type}")
                return CONFIGURE_STRATEGY
        
        # Проверка обязательных параметров
        required_params = set(strategy_info["params"].keys())
        provided_params = set(params.keys())
        missing = required_params - provided_params
        
        if missing:
            await update.message.reply_text(
                f"❌ Отсутствуют обязательные параметры: {', '.join(missing)}\n"
                f"Пожалуйста, введите все необходимые параметры."
            )
            return CONFIGURE_STRATEGY
            
        # Сохранение параметров
        context.user_data["strategy_params"] = params
        formatted_params = format_strategy_params(params)
        
        # Клавиатура с действиями после настройки
        keyboard = [
            [InlineKeyboardButton("▶️ Запустить бэктест", callback_data="backtest")],
            [InlineKeyboardButton("🚀 Включить на реальных данных", callback_data="activate_real")],
            [InlineKeyboardButton("↩️ Назад к стратегиям", callback_data="strategy")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Стратегия {strategy_info['name']} настроена:\n\n"
            f"{formatted_params}\n\n"
            f"Что сделать дальше?",
            reply_markup=reply_markup
        )
        await log_action("strategy_configured", f"{strategy_key} с параметрами: {params}", update.effective_user.id)
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Ошибка конфигурации стратегии: {e}", exc_info=True)
        # Формируем пример ввода
        example = "window=20" if strategy_key == "MA" else \
                  "period=14 oversold=30 overbought=70" if strategy_key == "RSI" else \
                  "period=20 deviation=2.0"
                  
        await update.message.reply_text(
            "❌ Ошибка формата параметров. Используйте формат:\n"
            "параметр1=значение параметр2=значение\n\n"
            f"Пример для {strategy_info['name']}: {example}\n"
            f"Попробуйте снова или введите /cancel"
        )
        return CONFIGURE_STRATEGY