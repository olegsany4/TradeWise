import pandas as pd

class Strategy:
    """Базовый класс для торговых стратегий."""

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Генерация торговых сигналов."""
        raise NotImplementedError(
            "Метод calculate_signals должен быть реализован в дочерних классах"
        )

    def backtest(self, df: pd.DataFrame) -> dict:
        """Тестирование стратегии на исторических данных."""
        df = self.calculate_signals(df.copy())
        if 'position' not in df:
            df['position'] = df['signal'].shift(1).fillna(0)
        df['returns'] = df['close'].pct_change().fillna(0) * df['position']
        df['equity_curve'] = (1 + df['returns']).cumprod()
        return {
            'returns': df['returns'].sum(),
            'equity_curve': df['equity_curve'],
            'signals': df
        }

    def __str__(self) -> str:
        return self.__class__.__name__
