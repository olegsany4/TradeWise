from tinkoff.invest import AsyncClient, MoneyValue
from config import TINKOFF_TOKEN, USE_SANDBOX

async def get_or_create_sandbox_account():
    async with AsyncClient(TINKOFF_TOKEN) as client:
        accounts = await client.sandbox.get_sandbox_accounts()
        if accounts.accounts:
            return accounts.accounts[0].id
        acc = await client.sandbox.open_sandbox_account()
        return acc.account_id

async def deposit_sandbox(account_id: str, amount: float):
    async with AsyncClient(TINKOFF_TOKEN) as client:
        await client.sandbox.sandbox_pay_in(
            account_id=account_id,
            amount=MoneyValue(units=int(amount), nano=0, currency="rub")
        )
