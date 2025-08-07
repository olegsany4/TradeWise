from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters
)
from utils.formatters import format_instrument_info
from utils.plotters import generate_price_chart
from utils.logger import log_action
from utils.rate_limit import rate_limit
import logging

logger = logging.getLogger(__name__)

# Состояния для диалога создания ордера
SELECT_INSTRUMENT, SELECT_SIDE, SELECT_QUANTITY, SELECT_PRICE, CONFIRM_ORDER = range(5)

@rate_limit()
async def start_order_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса создания ордера"""
    await update.message.reply_text(
        "📈 Для создания ордера введите тикер инструмента (например: SBER):"
    )
    return SELECT_INSTRUMENT

async def select_instrument(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора инструмента"""
    ticker = update.message.text.upper()
    context.user_data['ticker'] = ticker
    
    # Поиск информации об инструменте (заглушка)
    instrument_info = {
        'name': f"{ticker} Company",
        'price': 280.50,
        'lot_size': 10,
        'currency': 'RUB'
    }
    
    # Генерация графика
    chart = await generate_price_chart(ticker, days=30)
    
    # Отправка информации пользователю
    await update.message.reply_photo(
        photo=chart,
        caption=format_instrument_info(instrument_info)
    )
    
    # Клавиатура для выбора действия
    keyboard = [
        [
            InlineKeyboardButton("📤 Купить", callback_data="BUY"),
            InlineKeyboardButton("📥 Продать", callback_data="SELL")
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выберите действие для инструмента:",
        reply_markup=reply_markup
    )
    return SELECT_SIDE

async def select_side(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора действия (покупка/продажа)"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Создание ордера отменено")
        return ConversationHandler.END
    
    context.user_data['side'] = query.data
    await query.edit_message_text(
        f"Вы выбрали: {query.data}\n\n"
        "Введите количество лотов:"
    )
    return SELECT_QUANTITY

async def select_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода количества"""
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError
        context.user_data['quantity'] = quantity
        await update.message.reply_text(
            "Введите цену (для рыночного ордера введите 'MARKET'):"
        )
        return SELECT_PRICE
    except ValueError:
        await update.message.reply_text("❌ Неверное количество. Введите целое число больше 0")
        return SELECT_QUANTITY

async def select_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода цены"""
    price_input = update.message.text.upper()
    if price_input == "MARKET":
        context.user_data['price'] = "MARKET"
        context.user_data['price_value'] = None
    else:
        try:
            price = float(price_input)
            if price <= 0:
                raise ValueError
            context.user_data['price'] = price
            context.user_data['price_value'] = price
        except ValueError:
            await update.message.reply_text("❌ Неверная цена. Введите число или 'MARKET'")
            return SELECT_PRICE
    
    # Подготовка данных для подтверждения
    ticker = context.user_data['ticker']
    side = context.user_data['side']
    quantity = context.user_data['quantity']
    price = context.user_data['price']
    
    # Клавиатура подтверждения
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
            InlineKeyboardButton("✏️ Изменить", callback_data="change")
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🧾 Подтвердите ордер:\n\n"
        f"• Инструмент: {ticker}\n"
        f"• Действие: {side}\n"
        f"• Количество лотов: {quantity}\n"
        f"• Цена: {price}",
        reply_markup=reply_markup
    )
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и создание ордера"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm":
        # Создание ордера (заглушка)
        order_data = context.user_data
        order_id = "12345"  # В реальной реализации здесь будет вызов API
        
        await query.edit_message_text(
            f"✅ Ордер #{order_id} успешно создан!\n\n"
            f"• Инструмент: {order_data['ticker']}\n"
            f"• Действие: {order_data['side']}\n"
            f"• Количество: {order_data['quantity']} лотов\n"
            f"• Цена: {order_data['price']}"
        )
        await log_action("order_created", f"{order_data['side']} {order_data['ticker']}", update.effective_user.id)
    elif query.data == "change":
        await query.edit_message_text("Возврат к началу создания ордера...")
        return await start_order_creation(update, context)
    else:
        await query.edit_message_text("❌ Создание ордера отменено")
    
    return ConversationHandler.END

# ConversationHandler для создания ордера
order_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('createorder', start_order_creation)],
    states={
        SELECT_INSTRUMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_instrument)],
        SELECT_SIDE: [CallbackQueryHandler(select_side)],
        SELECT_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_quantity)],
        SELECT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_price)],
        CONFIRM_ORDER: [CallbackQueryHandler(confirm_order)]
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)