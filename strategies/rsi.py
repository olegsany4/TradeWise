import pandas as pd
import numpy as np
from .base import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    Стратегия на основе индекса относительной силы (RSI)
    
    Правила:
    - Покупаем, когда RSI < oversold и начинается рост
    - Продаем, когда RSI > overbought и начинается падение
    
    Параметры:
    - period: период для расчета RSI (по умолчанию 14)
    - oversold: уровень перепроданности (по умолчанию 30)
    - overbought: уровень перекупленности (по умолчанию 70)
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """Расчет индикатора RSI"""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(alpha=1/self.period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/self.period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def backtest(self, df: pd.DataFrame) -> dict:
        """Запуск бэктеста на исторических данных"""
        # Рассчитываем RSI
        df['rsi'] = self.calculate_rsi(df)
        
        # Генерируем сигналы
        df['signal'] = 0
        df['position'] = 0
        
        # Условия для покупки
        buy_condition = (
            (df['rsi'] < self.oversold) & 
            (df['rsi'].shift(1) < df['rsi'])
        )
        
        # Условия для продажи
        sell_condition = (
            (df['rsi'] > self.overbought) & 
            (df['rsi'].shift(1) > df['rsi'])
        )
        
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        # Рассчитываем позиции
        df['position'] = df['signal'].replace(0, method='ffill').fillna(0)
        
        # Рассчитываем доходность
        df['returns'] = df['close'].pct_change() * df['position'].shift(1)
        df['equity'] = (1 + df['returns']).cumprod()
        
        return {
            'returns': df['returns'].sum(),
            'equity_curve': df['equity'],
            'signals': df[['close', 'rsi', 'signal', 'position']]
        }
    
    def __str__(self):
        return f"RSI Strategy (period={self.period}, oversold={self.oversold}, overbought={self.overbought})"