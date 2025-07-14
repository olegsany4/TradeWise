import io
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# Используем неинтерактивный бэкенд
matplotlib.use('Agg')


def plot_backtest(results: pd.DataFrame) -> io.BytesIO:
    """Строит график кривой капитала и возвращает буфер изображения."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(results['equity_curve'], label='Equity')
    ax.set_title('Backtest Results')
    ax.set_xlabel('Period')
    ax.set_ylabel('Value')
    ax.legend()
    ax.grid(True)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf
