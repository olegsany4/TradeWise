import pandas as pd
import numpy as np
from .base import Strategy

class BollingerBandsStrategy(Strategy):
    """Стратегия на основе полос Боллинджера."""

    def __init__(self, period: int = 20, deviation: float = 2.0):
        self.period = period
        self.deviation = deviation

    def calculate_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        df['sma'] = df['close'].rolling(self.period).mean()
        df['std'] = df['close'].rolling(self.period).std()
        df['upper'] = df['sma'] + (df['std'] * self.deviation)
        df['lower'] = df['sma'] - (df['std'] * self.deviation)
        return df

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_bands(df)
        df['signal'] = 0
        buy_condition = df['close'] < df['lower']
        sell_condition = df['close'] > df['upper']
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        df['position'] = df['signal'].replace(0, method='ffill').fillna(0)
        return df

    def __str__(self) -> str:
        return f"Bollinger Bands (period={self.period}, deviation={self.deviation})"
