from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.rate_limit import rate_limit
from utils.logger import log_action

@rate_limit()
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_action("start", update.message.text, update.effective_user.id)
    
    # Улучшенное меню с группировкой функций
    keyboard = [
        [
            InlineKeyboardButton("💰 Баланс", callback_data="balance"),
            InlineKeyboardButton("🧳 Портфель", callback_data="portfolio")
        ],
        [
            InlineKeyboardButton("📈 График инструмента", callback_data="chart_start"),
            InlineKeyboardButton("📊 Тех. анализ", callback_data="technical_analysis")
        ],
        [
            InlineKeyboardButton("🤖 Торговые стратегии", callback_data="strategy"),
            InlineKeyboardButton("🧪 Бэктест", callback_data="backtest")
        ],
        [
            InlineKeyboardButton("📝 Создать ордер", callback_data="create_order"),
            InlineKeyboardButton("📋 Мои ордера", callback_data="orders")
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔮 Добро пожаловать в TradeWise - ваш персональный торговый помощник!\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расширенная справка по командам"""
    help_text = (
        "📚 *Доступные команды и функции:*\n\n"
        "💰 */balance* - Показать баланс счетов\n"
        "🧳 */portfolio* - Показать инвестиционный портфель\n"
        "📈 */chart TICKER* - Показать график инструмента (пример: /chart SBER)\n"
        "🤖 */strategy* - Управление торговыми стратегиями\n"
        "🧪 */backtest* - Запустить бэктест стратегии\n"
        "📝 */order BUY/SELL TICKER QTY PRICE* - Создать ордер (пример: /order BUY SBER 10 280.5)\n"
        "📋 */orders* - Показать активные ордера\n"
        "❌ */cancelorder ID* - Отменить ордер (пример: /cancelorder 42)\n\n"
        "⚙️ */settings* - Настройки бота\n"
        "ℹ️ */help* - Показать эту справку\n\n"
        "Для торговли акциями используйте команды /order и /orders."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню настроек"""
    keyboard = [
        [InlineKeyboardButton("🔁 Режим песочницы", callback_data="toggle_sandbox")],
        [InlineKeyboardButton("📊 Источник данных", callback_data="data_source")],
        [InlineKeyboardButton("🔐 Безопасность", callback_data="security")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ *Настройки TradeWise*\n\n"
        "Текущие параметры:\n"
        f"- Режим: {'Песочница 🧪' if context.bot_data.get('sandbox_mode', True) else 'Реальный торговый 🚀'}\n"
        f"- Источник данных: {'Tinkoff API 📡' if context.bot_data.get('use_real_data', False) else 'Тестовые данные 🧪'}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )