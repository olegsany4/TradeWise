import json
from datetime import datetime, timedelta
from tinkoff.invest import (
    AsyncClient,
    CandleInterval,
    HistoricCandle,
    Quotation
)
from tinkoff.invest.utils import now, quotation_to_decimal
from db.session import get_redis
from config import TINKOFF_TOKEN  # Используем только TINKOFF_TOKEN
from tinkoff_api.instruments import InstrumentCache
from utils.logger import logger

# ОБНОВЛЕНО: Ключи приведены в соответствие с callback-запросами
INTERVAL_MAPPING = {
    '1min': CandleInterval.CANDLE_INTERVAL_1_MIN,
    '5min': CandleInterval.CANDLE_INTERVAL_5_MIN,
    '15min': CandleInterval.CANDLE_INTERVAL_15_MIN,
    'hour': CandleInterval.CANDLE_INTERVAL_HOUR,
    'day': CandleInterval.CANDLE_INTERVAL_DAY,
}

class HistoricalData:
    def __init__(self):
        self.instrument_cache = InstrumentCache()
        self.token = TINKOFF_TOKEN  # Используем единый токен

    async def get_candles(
        self,
        ticker: str,
        interval: CandleInterval,
        days: int = 7
    ) -> list[HistoricCandle]:
        figi = await self.instrument_cache.get_figi(ticker)
        if not figi:
            raise ValueError(f"Инструмент {ticker} не найден")

        # Проверяем кэш
        cache_key = f"candles:{figi}:{interval}:{days}"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        
        if cached:
            try:
                # Десериализуем данные из JSON
                cached_data = json.loads(cached)
                candles = [
                    HistoricCandle(
                        time=datetime.fromisoformat(candle["time"]),
                        open=Quotation(units=candle["open"]["units"], nano=candle["open"]["nano"]),
                        high=Quotation(units=candle["high"]["units"], nano=candle["high"]["nano"]),
                        low=Quotation(units=candle["low"]["units"], nano=candle["low"]["nano"]),
                        close=Quotation(units=candle["close"]["units"], nano=candle["close"]["nano"]),
                        volume=candle["volume"]
                    )
                    for candle in cached_data
                ]
                return candles
            except Exception as e:
                logger.error(f"Error deserializing cached data: {e}")
                # В случае ошибки игнорируем кэш и загружаем заново

        # Получаем данные из API
        async with AsyncClient(self.token) as client:
            end_time = now()
            start_time = end_time - timedelta(days=days)
            
            candles = []
            async for candle in client.get_all_candles(
                figi=figi,
                from_=start_time,
                to=end_time,
                interval=interval
            ):
                candles.append(candle)
            
            # Сериализуем и кэшируем на 15 минут
            serialized_candles = [
                {
                    "time": candle.time.isoformat(),
                    "open": {"units": candle.open.units, "nano": candle.open.nano},
                    "high": {"units": candle.high.units, "nano": candle.high.nano},
                    "low": {"units": candle.low.units, "nano": candle.low.nano},
                    "close": {"units": candle.close.units, "nano": candle.close.nano},
                    "volume": candle.volume
                }
                for candle in candles
            ]
            await redis.set(cache_key, json.dumps(serialized_candles), ex=900)
            
            logger.info(f"Loaded {len(candles)} candles for {ticker} from API")
            return candles

    @staticmethod
    def format_candle(candle: HistoricCandle) -> str:
        """Форматирует одну свечу в строку."""
        if not candle:
            return ""
        time = candle.time.strftime("%Y-%m-%d %H:%M")
        open_ = float(quotation_to_decimal(candle.open))
        high = float(quotation_to_decimal(candle.high))
        low = float(quotation_to_decimal(candle.low))
        close = float(quotation_to_decimal(candle.close))
        volume = candle.volume
        return f"{time} | O:{open_:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f} V:{volume}"

    @staticmethod
    def interval_to_str(interval: CandleInterval) -> str:
        """ОБНОВЛЕНО: Приведено в соответствие с INTERVAL_MAPPING"""
        mapping = {
            CandleInterval.CANDLE_INTERVAL_1_MIN: "1min",
            CandleInterval.CANDLE_INTERVAL_5_MIN: "5min",
            CandleInterval.CANDLE_INTERVAL_15_MIN: "15min",
            CandleInterval.CANDLE_INTERVAL_HOUR: "hour",
            CandleInterval.CANDLE_INTERVAL_DAY: "day",
        }
        return mapping.get(interval, "unknown")