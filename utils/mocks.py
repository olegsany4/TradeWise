import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_mock_prices(
    days: int = 180,
    start_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0
) -> pd.DataFrame:
    """
    Генерация DataFrame с моковыми ценами за указанное количество дней
    
    Улучшения:
    1. Добавлен параметр `trend` для генерации восходящего/нисходящего тренда
    2. Реалистичные OHLC-данные с корреляцией между свечами
    3. Сохранена обратная совместимость
    
    :param days: Количество дней данных
    :param start_price: Начальная цена
    :param volatility: Волатильность (стандартное отклонение дневных изменений)
    :param trend: Суточный тренд в долях (0.01 = 1% дневного роста)
    :return: DataFrame с колонками ['open', 'high', 'low', 'close'] и датами в индексе
    """
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    prices = []
    current = start_price
    
    for i in range(days):
        # Базовое изменение цены = тренд + случайная волатильность
        change = trend + np.random.normal(0, volatility)
        prev_close = current
        current = prev_close * (1 + change)
        
        # Генерация OHLC на основе новой цены
        open_price = prev_close * (1 + np.random.normal(0, volatility/3))
        close_price = current
        high = max(open_price, close_price) * (1 + abs(np.random.normal(0, volatility/3)))
        low = min(open_price, close_price) * (1 - abs(np.random.normal(0, volatility/3)))
        
        # Гарантируем соблюдение соотношения high > low
        high = max(open_price, close_price, high)
        low = min(open_price, close_price, low)
        
        prices.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price
        })
    
    return pd.DataFrame(prices, index=dates)