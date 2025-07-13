import pandas as pd  # Добавить в начало файла

class BaseStrategy:
    """Базовый класс для торговых стратегий"""
    
    def backtest(self, df: pd.DataFrame) -> dict:
        """Базовый метод для бэктестирования (должен быть переопределен)"""
        raise NotImplementedError("Метод backtest должен быть реализован в дочерних классах")
    
    def __str__(self):
        """Строковое представление стратегии"""
        return self.__class__.__name__