import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd
import mplfinance as mpf
import numpy as np
from tinkoff_api.historical import get_candles  # Предполагается реализация

async def generate_price_chart(ticker: str, days: int = 30, interval: str = 'day'):
    """Генерация ценового графика для инструмента"""
    # Получение данных (заглушка)
    df = pd.DataFrame({
        'open': np.random.uniform(250, 300, 30),
        'high': np.random.uniform(255, 305, 30),
        'low': np.random.uniform(245, 295, 30),
        'close': np.random.uniform(250, 300, 30),
        'volume': np.random.randint(10000, 50000, 30)
    }, index=pd.date_range(end=pd.Timestamp.today(), periods=30, freq='D'))
    
    # Создание свечного графика
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # График цены
    mpf.plot(df, type='candle', ax=axes[0], volume=axes[1], show_nontrading=False)
    
    # Настройка оформления
    axes[0].set_title(f'График {ticker} ({days} дней)', fontsize=14)
    axes[0].set_ylabel('Цена', fontsize=12)
    axes[1].set_ylabel('Объем', fontsize=12)
    
    # Сохранение в буфер
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_technical_analysis(df: pd.DataFrame, indicators: dict):
    """Генерация графика с техническими индикаторами"""
    plt.figure(figsize=(12, 8))
    
    # График цены
    plt.subplot(2, 1, 1)
    plt.plot(df['close'], label='Цена', color='black', linewidth=2)
    
    # Добавление индикаторов
    if 'MA' in indicators:
        for window in indicators['MA']:
            ma = df['close'].rolling(window).mean()
            plt.plot(ma, label=f'MA({window})', linestyle='--')
    
    if 'Bollinger' in indicators:
        ma = df['close'].rolling(20).mean()
        std = df['close'].rolling(20).std()
        plt.plot(ma, label='Bollinger MA', color='blue')
        plt.fill_between(df.index, ma - 2*std, ma + 2*std, alpha=0.1, color='blue')
    
    plt.title('Технический анализ', fontsize=14)
    plt.legend()
    plt.grid(True)
    
    # Индикатор RSI
    if 'RSI' in indicators:
        plt.subplot(2, 1, 2)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        plt.plot(rsi, label='RSI', color='purple')
        plt.axhline(y=30, color='green', linestyle='--')
        plt.axhline(y=70, color='red', linestyle='--')
        plt.ylim(0, 100)
        plt.ylabel('RSI', fontsize=12)
        plt.grid(True)
    
    # Сохранение в буфер
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf