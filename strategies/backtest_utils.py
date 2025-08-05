import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

def plot_backtest_results(results: dict) -> BytesIO:
    """
    Визуализация результатов бэктеста
    Возвращает BytesIO с изображением графика
    """
    plt.figure(figsize=(12, 8))
    
    # График кривой капитала
    plt.subplot(2, 1, 1)
    results['equity_curve'].plot(title='Equity Curve')
    plt.ylabel('Capital')
    
    # График сделок
    plt.subplot(2, 1, 2)
    prices = results['equity_curve'].index.to_series()
    buy_dates = [trade['date'] for trade in results['trades'] if trade['action'] == 'BUY']
    sell_dates = [trade['date'] for trade in results['trades'] if trade['action'] == 'SELL']
    
    plt.plot(prices, label='Price')
    plt.scatter(buy_dates, prices.loc[buy_dates], color='green', marker='^', label='Buy')
    plt.scatter(sell_dates, prices.loc[sell_dates], color='red', marker='v', label='Sell')
    plt.legend()
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf