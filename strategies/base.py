import pandas as pd

class BaseStrategy:
    """Базовый класс для торговых стратегий."""

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Генерация торговых сигналов."""
        raise NotImplementedError

    def backtest(self, df: pd.DataFrame) -> dict:
        """Запуск бэктеста на переданных данных."""
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__class__.__name__
