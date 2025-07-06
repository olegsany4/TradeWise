from tinkoff.invest import AsyncClient
from config import TINKOFF_TOKEN, USE_SANDBOX

async def place_order(account_id: str, figi: str, quantity: int, direction: str, price=None):
    async with AsyncClient(TINKOFF_TOKEN) as client:
        if USE_SANDBOX:
            return await client.sandbox.post_sandbox_order(
                account_id=account_id,
                figi=figi,
                quantity=quantity,
                direction=direction,
                order_type="limit" if price else "market",
                price=price
            )
        else:
            return await client.orders.post_order(
                account_id=account_id,
                figi=figi,
                quantity=quantity,
                direction=direction,
                order_type="limit" if price else "market",
                price=price
            )
