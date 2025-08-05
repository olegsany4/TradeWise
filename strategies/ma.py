import pandas as pd
from .base import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, short_window: int = 10, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Рассчитываем скользящие средние с min_periods=1
        df['short_ma'] = df['close'].rolling(window=self.short_window, min_periods=1).mean()
        df['long_ma'] = df['close'].rolling(window=self.long_window, min_periods=1).mean()
        
        # Создаем сигналы
        df['signal'] = 'HOLD'
        
        # Условия пересечения (а не просто сравнения)
        buy_condition = (df['short_ma'] > df['long_ma']) & (df['short_ma'].shift(1) <= df['long_ma'].shift(1))
        sell_condition = (df['short_ma'] < df['long_ma']) & (df['short_ma'].shift(1) >= df['long_ma'].shift(1))
        
        df.loc[buy_condition, 'signal'] = 'BUY'
        df.loc[sell_condition, 'signal'] = 'SELL'
        
        return df[['signal']]