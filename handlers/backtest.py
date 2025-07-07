from telegram import Update
from telegram.ext import ContextTypes
from strategies.ma import MovingAverageStrategy
from utils.mocks import generate_mock_candles
import matplotlib.pyplot as plt
import io
from utils.rate_limit import rate_limit

@rate_limit()
async def backtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = generate_mock_candles(200)
    strategy = MovingAverageStrategy(window=20)
    results = strategy.backtest(df)
    fig, ax = plt.subplots()
    ax.plot(results['equity_curve'])
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    await update.message.reply_photo(buf, caption="Результаты бэктеста")
