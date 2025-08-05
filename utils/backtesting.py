import matplotlib.pyplot as plt
import pandas as pd


def plot_backtest(results: pd.DataFrame, output="backtest.png") -> None:
    """Сохраняет график кривой капитала."""
    plt.figure()
    plt.plot(results['equity_curve'])
    if hasattr(output, 'write'):
        plt.savefig(output, format='png', dpi=100)
    else:
        plt.savefig(output)
    plt.close()
