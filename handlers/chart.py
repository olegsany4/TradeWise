from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from utils.plotters import generate_chart, plot_technical_analysis
from utils.instruments import find_instrument
import logging

logger = logging.getLogger(__name__)

async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /chart"""
    args = context.args
    if not args:
        await update.message.reply_text("ℹ️ Использование: /chart <тикер> [дни=30]")
        return
    
    ticker = args[0].upper()
    days = int(args[1]) if len(args) > 1 else 30
    
    # Поиск инструмента
    instrument = await find_instrument(ticker)
    if not instrument:
        await update.message.reply_text(f"❌ Инструмент {ticker} не найден")
        return
    
    # Генерация графика
    try:
        chart = await generate_chart(instrument.figi, days)
        await update.message.reply_photo(
            photo=chart,
            caption=f"📈 График {instrument.name} ({ticker}) за {days} дней"
        )
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        await update.message.reply_text("❌ Ошибка при построении графика")

def setup_chart_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("chart", chart_command))