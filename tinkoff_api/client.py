from tinkoff.invest import AsyncClient
from config import TINKOFF_TOKEN, USE_SANDBOX

class TinkoffClient:
    def __init__(self, token: str = TINKOFF_TOKEN, sandbox: bool = USE_SANDBOX):
        self.token = token
        self.sandbox = sandbox

    async def get_portfolio(self, account_id: str):
        async with AsyncClient(self.token) as client:
            if self.sandbox:
                return await client.sandbox.get_sandbox_portfolio(account_id=account_id)
            else:
                return await client.operations.get_portfolio(account_id=account_id)
