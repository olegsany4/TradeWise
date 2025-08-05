import pandas as pd
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class Strategy(ABC):
    @abstractmethod
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Генерация торговых сигналов на основе данных
        Возвращает DataFrame с колонкой 'signal'
        """
        pass

    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
        """
        Базовый бэктест стратегии
        Возвращает словарь с результатами:
        - equity_curve: кривая капитала
        - trades: список сделок
        - metrics: метрики эффективности
        
        Изменения:
        1. Работа с копией данных (не модифицируем исходный df)
        2. Обработка конфликта имён колонок
        3. Безопасный расчёт коэффициента Шарпа
        4. Подсчёт общего количества сделок
        5. Пропуск строк с NaN в сигналах
        """
        # Создаем копию для безопасной работы
        df_backtest = df.copy()
        
        # Генерируем сигналы
        signals = self.calculate_signals(df_backtest)
        
        # Обработка конфликта имен колонок
        if 'signal' in df_backtest.columns:
            # Переименовываем существующую колонку
            df_backtest.rename(columns={'signal': 'signal_original'}, inplace=True)
        
        # Объединяем с сигналами
        df_backtest = df_backtest.join(signals[['signal']])
        
        # Упрощенная логика исполнения сигналов
        position = 0
        capital = initial_capital
        equity_curve = []
        trades = []
        
        # Счетчики для диагностики
        buy_signals = 0
        sell_signals = 0
        skip_count = 0
        
        for i, row in df_backtest.iterrows():
            # Пропускаем строки с NaN в сигнале
            if pd.isna(row['signal']) or row['signal'] not in ['BUY', 'SELL']:
                skip_count += 1
                current_value = capital + (position * row['close'] if position > 0 else 0)
                equity_curve.append(current_value)
                continue
                
            if row['signal'] == 'BUY' and position == 0:
                position = capital / row['close']
                capital = 0
                trades.append({'date': i, 'action': 'BUY', 'price': row['close']})
                buy_signals += 1
            elif row['signal'] == 'SELL' and position > 0:
                capital = position * row['close']
                position = 0
                trades.append({'date': i, 'action': 'SELL', 'price': row['close']})
                sell_signals += 1
            
            # Расчет текущего капитала
            current_value = capital + (position * row['close'] if position > 0 else 0)
            equity_curve.append(current_value)
        
        # Диагностика
        logger.debug(f"Backtest summary: {buy_signals} BUY, {sell_signals} SELL, {skip_count} rows skipped")
        
        df_backtest['equity_curve'] = equity_curve
        
        # Расчет метрик
        returns = df_backtest['equity_curve'].pct_change().dropna()
        
        # Безопасный расчет коэффициента Шарпа
        if len(returns) > 1 and returns.std() != 0:
            sharpe = returns.mean() / returns.std() * (252**0.5)
        else:
            sharpe = 0
        
        # Рассчитываем максимальную просадку
        max_drawdown = (df_backtest['equity_curve'] / df_backtest['equity_curve'].cummax() - 1).min()
        
        # Общее количество трейдов
        total_trades = len(trades)
        
        return {
            'equity_curve': df_backtest['equity_curve'],
            'trades': trades,
            'metrics': {
                'sharpe': sharpe,
                'max_drawdown': max_drawdown,
                'final_return': equity_curve[-1] / initial_capital - 1,
                'total_trades': total_trades  # Добавляем общее количество сделок
            }
        }