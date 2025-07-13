import asyncio
from datetime import datetime, timedelta
from tinkoff.invest import AsyncClient
from tinkoff.invest.utils import quotation_to_decimal
from db.session import get_redis
from config import TINKOFF_TOKEN  # Импортируем только TINKOFF_TOKEN
from utils.logger import logger

class InstrumentCache:
    _instance = None
    _instruments = None
    _last_updated = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_instruments(self):
        async with self._lock:
            if self._instruments is None or self._should_refresh():
                await self._load_instruments()
            return self._instruments

    async def get_instrument(self, ticker):
        instruments = await self.get_instruments()
        return instruments.get(ticker.upper())

    async def get_figi(self, ticker):
        instrument = await self.get_instrument(ticker)
        return instrument["figi"] if instrument else None

    async def get_lot_size(self, ticker):
        instrument = await self.get_instrument(ticker)
        return instrument["lot"] if instrument else None

    def _should_refresh(self):
        return (self._last_updated is None or 
                datetime.now() - self._last_updated > timedelta(hours=24))

    async def _load_instruments(self):
        redis = await get_redis()
        cached = await redis.get("tinkoff_instruments")
        
        if cached:
            self._instruments = eval(cached)
            self._last_updated = datetime.now()
            logger.info("Loaded instruments from cache")
            return

        instruments = {}
        # Используем единый TINKOFF_TOKEN, который уже содержит правильный токен для текущего режима
        token = TINKOFF_TOKEN
        async with AsyncClient(token) as client:
            # Убраны параметры status из всех вызовов
            shares = await client.instruments.shares()
            bonds = await client.instruments.bonds()
            etfs = await client.instruments.etfs()
            currencies = await client.instruments.currencies()

            # Обработка всех инструментов независимо от статуса
            for item in shares.instruments + bonds.instruments + etfs.instruments + currencies.instruments:
                instruments[item.ticker] = {
                    "figi": item.figi,
                    "ticker": item.ticker,
                    "name": item.name,
                    "lot": item.lot,
                    "currency": item.currency,
                    "type": "share" if hasattr(item, 'share') else 
                            "bond" if hasattr(item, 'bond') else 
                            "etf" if hasattr(item, 'etf') else "currency",
                    "min_price_increment": float(quotation_to_decimal(item.min_price_increment))
                }

        self._instruments = instruments
        self._last_updated = datetime.now()
        await redis.set("tinkoff_instruments", str(instruments), ex=24*3600)
        logger.info(f"Loaded {len(instruments)} instruments from Tinkoff API")
        return instruments