import pandas as pd
from .base import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, window: int = 20):
        self.window = window
    def calculate_signal(self, df: pd.DataFrame) -> str:
        df['MA'] = df['close'].rolling(self.window).mean()
        if df['close'].iloc[-1] > df['MA'].iloc[-1]:
            return "BUY"
        return "SELL"
    def backtest(self, df: pd.DataFrame) -> dict:
        df['MA'] = df['close'].rolling(self.window).mean()
        df['signal'] = (df['close'] > df['MA']).astype(int)
        df['equity_curve'] = df['signal'].cumsum()
        return df
