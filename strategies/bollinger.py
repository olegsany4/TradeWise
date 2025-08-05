import pandas as pd
import numpy as np
from .base import Strategy

class BollingerStrategy(Strategy):  # Изменено имя класса
    """Стратегия на основе полос Боллинджера."""

    def __init__(self, period: int = 20, deviation: float = 2.0):
        self.period = period
        self.deviation = deviation

    def calculate_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        # Рассчитываем среднюю скользящую
        df['sma'] = df['close'].rolling(self.period).mean()
        # Рассчитываем стандартное отклонение
        df['std'] = df['close'].rolling(self.period).std()
        # Рассчитываем верхнюю и нижнюю полосы
        df['upper'] = df['sma'] + (df['std'] * self.deviation)
        df['lower'] = df['sma'] - (df['std'] * self.deviation)
        return df

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Рассчитываем полосы Боллинджера
        df = self.calculate_bands(df)
        
        # Создаем DataFrame для сигналов
        signals = pd.DataFrame(index=df.index, columns=['signal'])
        signals['signal'] = 'HOLD'  # Значение по умолчанию
        
        # Определяем условия для сигналов
        buy_condition = df['close'] < df['lower']
        sell_condition = df['close'] > df['upper']
        
        # Присваиваем сигналы BUY и SELL
        signals.loc[buy_condition, 'signal'] = 'BUY'
        signals.loc[sell_condition, 'signal'] = 'SELL'
        
        return signals

    def __str__(self) -> str:
        return f"Bollinger Bands (period={self.period}, deviation={self.deviation})"