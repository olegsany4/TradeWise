from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from tinkoff_api.accounts import get_or_create_sandbox_account
from tinkoff_api.client import TinkoffClient
from utils.formatters import format_portfolio
from config import USE_SANDBOX, PRIMARY_ACCOUNT_ID
from utils.rate_limit import rate_limit
from utils.logger import log_action

@rate_limit()
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_action("portfolio_command", "User requested portfolio", update.effective_user.id)
    if USE_SANDBOX:
        account_id = await get_or_create_sandbox_account()
    else:
        account_id = PRIMARY_ACCOUNT_ID
    client = TinkoffClient(sandbox=USE_SANDBOX)
    portfolio_data = await client.get_portfolio(account_id)
    text = format_portfolio(portfolio_data)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Обновить", callback_data="refresh_portfolio")],
        [InlineKeyboardButton("🧠 Запустить стратегию", callback_data="launch_strategy")],
        [InlineKeyboardButton("🌲 Лес", callback_data="show_forest")],
    ])
    await update.effective_message.reply_text(text, reply_markup=reply_markup)