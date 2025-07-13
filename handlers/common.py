from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.rate_limit import rate_limit
from utils.logger import log_action

@rate_limit()
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_action("start", update.message.text, update.effective_user.id)
    
    # Создаем клавиатуру с кнопками
    keyboard = [
        [
            InlineKeyboardButton("💰 Баланс", callback_data="balance"),
            InlineKeyboardButton("🧳 Портфель", callback_data="portfolio")
        ],
        [
            InlineKeyboardButton("📊 Котировки", callback_data="quotes"),
            InlineKeyboardButton("📈 Свечи", callback_data="candles_start")  # Новая кнопка
        ],
        [
            InlineKeyboardButton("🤖 Стратегии", callback_data="strategy"),
            InlineKeyboardButton("🧪 Бэктест", callback_data="backtest")
        ],
        [
            InlineKeyboardButton("📝 Ордера", callback_data="orders"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔮 Добро пожаловать в TradeWise!\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )