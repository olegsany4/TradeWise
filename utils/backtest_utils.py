import matplotlib
# Установка неинтерактивного бэкенда для безопасной работы в потоках
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import io

def plot_backtest_results(results: dict) -> io.BytesIO:
    """
    Генерирует график кривой капитала и возвращает его как BytesIO объект
    
    :param results: Словарь с результатами бэктеста
    :return: Буфер с изображением в формате PNG
    """
    plt.figure(figsize=(10, 6))
    plt.plot(results['equity_curve'], label='Equity Curve')
    plt.title('Backtest Results')
    plt.xlabel('Time')
    plt.ylabel('Equity')
    plt.legend()
    plt.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf