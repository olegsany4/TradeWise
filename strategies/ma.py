import pandas as pd
import numpy as np
from .base import BaseStrategy

class MovingAverageStrategy(BaseStrategy):
    """Стратегия на основе скользящих средних"""
    
    def __init__(self, window: int = 20):
        self.window = window
        
    def backtest(self, df: pd.DataFrame) -> dict:
        # Реализация бэктеста
        df['ma'] = df['close'].rolling(self.window).mean()
        df['signal'] = np.where(df['close'] > df['ma'], 1, 0)
        df['position'] = df['signal'].shift(1)
        
        df['returns'] = df['close'].pct_change() * df['position']
        df['equity'] = (1 + df['returns']).cumprod()
        
        return {
            'returns': df['returns'].sum(),
            'equity_curve': df['equity'],
            'signals': df[['close', 'ma', 'signal', 'position']]
        }
    
    def __str__(self):
        return f"Moving Average (window={self.window})"