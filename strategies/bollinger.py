import pandas as pd
import numpy as np
from .base import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    """
    Стратегия на основе полос Боллинджера
    
    Правила:
    - Покупаем, когда цена закрывается ниже нижней полосы
    - Продаем, когда цена закрывается выше верхней полосы
    
    Параметры:
    - period: период для скользящей средней (по умолчанию 20)
    - deviation: количество стандартных отклонений (по умолчанию 2.0)
    """
    
    def __init__(self, period: int = 20, deviation: float = 2.0):
        self.period = period
        self.deviation = deviation
        
    def calculate_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчет полос Боллинджера"""
        df['sma'] = df['close'].rolling(self.period).mean()
        df['std'] = df['close'].rolling(self.period).std()
        df['upper'] = df['sma'] + (df['std'] * self.deviation)
        df['lower'] = df['sma'] - (df['std'] * self.deviation)
        return df
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_bands(df.copy())
        df['signal'] = 0
        buy_condition = df['close'] < df['lower']
        sell_condition = df['close'] > df['upper']
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        df['position'] = df['signal'].replace(0, method='ffill').fillna(0)
        return df

    def backtest(self, df: pd.DataFrame) -> dict:
        """Запуск бэктеста на исторических данных."""
        df = self.calculate_signals(df)
        df['returns'] = df['close'].pct_change().fillna(0) * df['position'].shift(1)
        df['equity'] = (1 + df['returns']).cumprod()

        return {
            'returns': df['returns'].sum(),
            'equity_curve': df['equity'],
            'signals': df[['close', 'sma', 'upper', 'lower', 'signal', 'position']]
        }
    
    def __str__(self):
        return f"Bollinger Bands (period={self.period}, deviation={self.deviation})"