import pandas as pd
import numpy as np

def generate_mock_candles(rows=100):
    np.random.seed(42)
    price = np.cumsum(np.random.randn(rows)) + 100
    df = pd.DataFrame({
        'open': price + np.random.rand(rows),
        'high': price + np.random.rand(rows),
        'low': price - np.random.rand(rows),
        'close': price,
        'volume': np.random.randint(100, 1000, size=rows),
    })
    return df
