from telegram import Update
from telegram.ext import ContextTypes
from tinkoff_api.client import TinkoffClient
from tinkoff_api.accounts import get_or_create_sandbox_account
from utils.formatters import format_orders
from config import USE_SANDBOX, PRIMARY_ACCOUNT_ID
from utils.logger import log_action

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /orders"""
    try:
        account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
        client = TinkoffClient(sandbox=USE_SANDBOX)
        
        # Получаем активные и завершённые ордера
        active_orders, executed_orders = await client.get_orders(account_id)
        
        # Форматируем вывод
        text = format_orders(active_orders, executed_orders)
        await update.message.reply_text(text)
        
        await log_action("orders_command", "Fetched orders", update.effective_user.id)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при получении ордеров: {str(e)}")
        await log_action("orders_command", f"Error: {str(e)}", update.effective_user.id)