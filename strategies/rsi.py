import pandas as pd
import numpy as np
from .base import Strategy

class RSIStrategy(Strategy):
    """Стратегия на основе индекса относительной силы (RSI)."""

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Используем скользящее среднее вместо EMA для более стабильных результатов
        avg_gain = gain.rolling(window=self.period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df)
        
        # Улучшенные условия для сигналов
        buy_condition = (df['rsi'] < self.oversold)
        sell_condition = (df['rsi'] > self.overbought)
        
        # Генерация сигналов на основе пересечений
        df['signal'] = 'HOLD'
        df.loc[buy_condition, 'signal'] = 'BUY'
        df.loc[sell_condition, 'signal'] = 'SELL'
        
        # Добавляем условия выхода из позиций
        df.loc[(df['signal'].shift(1) == 'BUY') & (df['rsi'] > self.oversold), 'signal'] = 'SELL'
        df.loc[(df['signal'].shift(1) == 'SELL') & (df['rsi'] < self.overbought), 'signal'] = 'BUY'
        
        return df[['signal']]

    def __str__(self) -> str:
        return (
            f"RSI Strategy (period={self.period}, oversold={self.oversold}, "
            f"overbought={self.overbought})"
        )