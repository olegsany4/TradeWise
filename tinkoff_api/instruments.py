from tinkoff.invest import AsyncClient
from config import TINKOFF_TOKEN

async def get_instruments():
    async with AsyncClient(TINKOFF_TOKEN) as client:
        return await client.instruments.shares()