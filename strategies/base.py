import pandas as pd

class Strategy:
    def calculate_signal(self, df: pd.DataFrame) -> str:
        raise NotImplementedError
    def backtest(self, df: pd.DataFrame) -> dict:
        raise NotImplementedError
