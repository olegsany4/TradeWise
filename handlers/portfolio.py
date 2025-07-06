from telegram import Update
from telegram.ext import ContextTypes
from tinkoff_api.accounts import get_or_create_sandbox_account
from tinkoff_api.client import TinkoffClient
from utils.formatters import format_portfolio
from config import USE_SANDBOX, PRIMARY_ACCOUNT_ID

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if USE_SANDBOX:
        account_id = await get_or_create_sandbox_account()
    else:
        account_id = PRIMARY_ACCOUNT_ID
    client = TinkoffClient(sandbox=USE_SANDBOX)
    portfolio = await client.get_portfolio(account_id)
    await update.message.reply_text(format_portfolio(portfolio))
