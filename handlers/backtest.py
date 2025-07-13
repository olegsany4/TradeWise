from telegram import Update
from telegram.ext import ContextTypes
from strategies.ma import MovingAverageStrategy
from strategies.rsi import RSIStrategy
from strategies.bollinger import BollingerBandsStrategy
from utils.mocks import generate_mock_candles
from utils.rate_limit import rate_limit
from utils.logger import log_action
import asyncio
import matplotlib
import matplotlib.pyplot as plt
import io
from concurrent.futures import ThreadPoolExecutor

# Используем неинтерактивный бэкенд
matplotlib.use('Agg')

def plot_equity_curve(results):
    """Синхронная функция построения графика"""
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

@rate_limit()
async def backtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_action("backtest_command", "User requested backtest", update.effective_user.id)
    
    # Получаем сохраненную стратегию
    strategy_key = context.user_data.get("selected_strategy", "MA")
    params = context.user_data.get("strategy_params", {})
    
    # Выбираем стратегию
    if strategy_key == "MA":
        strategy = MovingAverageStrategy(**params)
    elif strategy_key == "RSI":
        strategy = RSIStrategy(**params)
    elif strategy_key == "Bollinger":
        strategy = BollingerBandsStrategy(**params)
    else:
        strategy = MovingAverageStrategy()
    
    # Генерируем тестовые данные
    df = generate_mock_candles(200)
    
    # Запускаем бэктест
    results = strategy.backtest(df)
    
    # Асинхронное построение графика
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        buf = await loop.run_in_executor(pool, plot_equity_curve, results)
    
    # Отправляем результат
    await update.effective_message.reply_photo(
        photo=buf,
        caption=f"📈 Результаты бэктеста {strategy_key}\n"
                f"Доходность: {results['returns']:.2%}"
    )
    
    # Закрываем буфер
    buf.close()