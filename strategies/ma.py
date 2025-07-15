import pandas as pd
import numpy as np
from .base import Strategy

class MovingAverageStrategy(Strategy):
    """Стратегия на основе скользящих средних."""

    def __init__(self, window: int = 20):
        self.window = window

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df['MA'] = df['close'].rolling(self.window).mean()
        df['signal'] = np.where(df['close'] > df['MA'], 1, 0)
        df['position'] = df['signal'].shift(1)
        return df

    def calculate_signal(self, df: pd.DataFrame) -> str:
        df = self.calculate_signals(df.copy())
        return "BUY" if df['signal'].iloc[-1] == 1 else "SELL"

    def __str__(self) -> str:
        return f"Moving Average (window={self.window})"
