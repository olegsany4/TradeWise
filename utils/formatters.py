import pandas as pd
from tabulate import tabulate
from decimal import Decimal, getcontext
from tinkoff.invest import PortfolioResponse, MoneyValue, Quotation, Order, OrderDirection, OrderExecutionReportStatus
from datetime import datetime

# Устанавливаем точность вычислений для Decimal
getcontext().prec = 10

def to_decimal(value) -> Decimal:
    """Конвертирует MoneyValue или Quotation в Decimal."""
    if hasattr(value, 'units') and hasattr(value, 'nano'):
        return Decimal(value.units) + Decimal(value.nano) / Decimal(10**9)
    elif isinstance(value, (int, float, str, Decimal)):
        return Decimal(value)
    else:
        return Decimal(0)

def get_currency_symbol(currency: str) -> str:
    """Возвращает символ валюты по коду"""
    currency = currency.lower()
    if currency == 'rub':
        return '₽'
    elif currency == 'usd':
        return '$'
    elif currency == 'eur':
        return '€'
    elif currency == 'gbp':
        return '£'
    else:
        return currency.upper()

def format_balance(portfolio: PortfolioResponse, is_sandbox: bool = False) -> str:
    """Форматирование баланса с учетом типа счета (песочница/реальный)"""
    # Получаем общую стоимость портфеля
    total_portfolio_value = to_decimal(portfolio.total_amount_portfolio)
    
    # Получаем доступные средства
    available = to_decimal(portfolio.total_amount_currencies)
    
    # Определяем валюту
    currency = portfolio.total_amount_portfolio.currency
    currency_symbol = get_currency_symbol(currency)
    
    # Форматируем текст для песочницы и реального счета
    if is_sandbox:
        # Рассчитываем PnL для песочницы
        initial_deposit = Decimal('1000000')
        pnl_absolute = total_portfolio_value - initial_deposit
        pnl_percent = (pnl_absolute / initial_deposit) * 100
        pnl_sign = "+" if pnl_absolute >= 0 else ""
        pnl_text = (
            f"📉 Текущий PnL: {pnl_sign}{pnl_absolute:,.2f} {currency_symbol} "
            f"({pnl_sign}{pnl_percent:.2f}%)"
        )
    else:
        # Для реального счета не показываем PnL
        pnl_text = "📊 Режим реального счета"
    
    return (
        f"💰 *Ваш баланс*\n"
        f"🧾 Счёт: {'Песочница' if is_sandbox else 'Брокерский Tinkoff'}\n"
        f"💵 Валюта: {currency.upper()}\n"
        f"📊 Доступно для торговли: {available:,.2f} {currency_symbol}\n"
        f"📈 Общая стоимость портфеля: {total_portfolio_value:,.2f} {currency_symbol}\n"
        f"{pnl_text}"
    )

def format_portfolio(portfolio: PortfolioResponse) -> str:
    """Форматирование портфеля с учетом валюты позиций"""
    if not portfolio.positions:
        return "🧳 Ваш портфель пуст."
    
    text = "🧳 *Ваш портфель:*\n\n"
    
    # Иконки для разных типов активов
    asset_icons = {
        "share": "🟡",  # Акции
        "bond": "🔵",   # Облигации
        "etf": "🟢",    # Фонды
        "currency": "🟣",  # Валюта
        "future": "🟠", # Фьючерсы
    }
    
    for pos in portfolio.positions:
        # Получаем иконку для типа актива
        asset_icon = asset_icons.get(pos.instrument_type.lower(), "⚪️")
        
        # Получаем тикер или FIGI, если тикер недоступен
        ticker = getattr(pos, 'ticker', None) or pos.figi
        
        # Получаем валюту позиции и символ
        currency = pos.current_price.currency
        symbol = get_currency_symbol(currency)
        
        # Получаем значения в Decimal
        current_price = to_decimal(pos.current_price)
        average_price = to_decimal(pos.average_position_price)
        quantity = to_decimal(pos.quantity)
        
        # Рассчитываем PnL для позиции
        pnl_absolute = (current_price - average_price) * quantity
        pnl_percent = (current_price / average_price - 1) * 100 if average_price != 0 else Decimal(0)
        
        # Форматируем строку позиции
        text += (
            f"{asset_icon} *{ticker}*\n"
            f"  📦 *Кол-во*: {quantity:.2f} шт\n"
            f"  💵 *Средняя цена*: {average_price:,.2f} {symbol}\n"
            f"  💰 *Текущая цена*: {current_price:,.2f} {symbol}\n"
            f"  🔄 *PnL*: {'+' if pnl_absolute >= 0 else ''}{pnl_absolute:,.2f} {symbol} "
            f"({'+' if pnl_percent >= 0 else ''}{pnl_percent:.2f}%)\n\n"
        )
    
    return text

def format_orders(active_orders: list, executed_orders: list) -> str:
    """Форматирование списка ордеров"""
    text = "🧾 *Ваши ордера*\n\n"
    
    # Активные ордера
    if active_orders:
        text += "🔄 *Активные заявки:*\n"
        for order in active_orders:
            direction = "📤 Покупка" if order.direction == OrderDirection.ORDER_DIRECTION_BUY else "📥 Продажа"
            status = "⏳ В ожидании" if order.execution_report_status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_NEW else "🟡 Частично исполнен"
            price = to_decimal(order.initial_order_price)
            text += f"{direction} {order.lots_requested} шт {order.figi} по {price:,.2f} — {status}\n"
        text += "\n"
    
    # Исполненные ордера
    if executed_orders:
        text += "✅ *Завершённые сделки:*\n"
        for order in executed_orders[:5]:  # Последние 5
            direction = "📤 Покупка" if order.direction == OrderDirection.ORDER_DIRECTION_BUY else "📥 Продажа"
            price = to_decimal(order.initial_order_price)
            text += f"{direction} {order.lots_executed} шт {order.figi} по {price:,.2f} — Исполнен ✅\n"
    
    if not active_orders and not executed_orders:
        text += "У вас пока нет активных или завершённых ордеров.\n"
    
    text += "\n🔍 Используйте: /orders"
    return text

def format_strategy_params(params: dict) -> str:
    """Форматирование параметров стратегии"""
    return "\n".join([f"{k}: {v}" for k, v in params.items()])

def format_candles(ticker: str, interval: str, candles: list) -> str:
    """
    Форматирует список свечей для отображения в Telegram
    """
    if not candles:
        return f"📭 Нет данных для {ticker} ({interval})"
    
    # Ограничиваем количество свечей для отображения
    max_candles = 15
    if len(candles) > max_candles:
        candles_text = "\n".join(candles[:max_candles])
        footer = f"\n\n... и ещё {len(candles) - max_candles} свеч"
    else:
        candles_text = "\n".join(candles)
        footer = ""
    
    return f"📊 *{ticker}* | `{interval}`\n\n{candles_text}{footer}"