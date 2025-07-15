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
        avg_gain = gain.ewm(alpha=1 / self.period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self.period, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df['rsi'] = self.calculate_rsi(df)
        df['signal'] = 0
        buy_condition = (df['rsi'] < self.oversold) & (df['rsi'].shift(1) < df['rsi'])
        sell_condition = (df['rsi'] > self.overbought) & (df['rsi'].shift(1) > df['rsi'])
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        df['position'] = df['signal'].replace(0, method='ffill').fillna(0)
        return df

    def __str__(self) -> str:
        return (
            f"RSI Strategy (period={self.period}, oversold={self.oversold}, "
            f"overbought={self.overbought})"
        )
