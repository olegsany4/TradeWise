from tinkoff.invest import AsyncClient
from config import TINKOFF_TOKEN
import datetime

async def get_candles(figi: str, from_dt: datetime.datetime, to_dt: datetime.datetime, interval):
    async with AsyncClient(TINKOFF_TOKEN) as client:
        return await client.market_data.get_candles(
            figi=figi,
            from_=from_dt,
            to=to_dt,
            interval=interval
        )
