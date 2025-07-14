import pandas as pd
import numpy as np
from .base import BaseStrategy

class MovingAverageStrategy(BaseStrategy):
    """Стратегия на основе скользящих средних."""

    def __init__(self, window: int = 20) -> None:
        self.window = window

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['ma'] = df['close'].rolling(self.window).mean()
        df['signal'] = np.where(df['close'] > df['ma'], 1, 0)
        df['position'] = df['signal'].shift(1).fillna(0)
        return df

    def backtest(self, df: pd.DataFrame) -> dict:
        df = self.calculate_signals(df)
        df['returns'] = df['close'].pct_change().fillna(0) * df['position']
        df['equity'] = (1 + df['returns']).cumprod()

        return {
            'returns': df['returns'].sum(),
            'equity_curve': df['equity'],
            'signals': df[['close', 'ma', 'signal', 'position']]
        }

    def __str__(self) -> str:
        return f"Moving Average (window={self.window})"