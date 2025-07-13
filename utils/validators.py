def validate_ticker(ticker: str) -> bool:
    """
    Проверяет валидность тикера
    - Только буквы
    - Длина 3-5 символов
    """
    return ticker.isalpha() and 3 <= len(ticker) <= 5

def validate_interval(interval: str) -> bool:
    """Проверяет валидность интервала свечей"""
    valid_intervals = ['1min', '5min', '15min', '30min', 'hour', '2hour', '4hour', 'day', 'week', 'month']
    return interval in valid_intervals

def validate_days(days: int) -> bool:
    """Проверяет валидность периода (количество дней)"""
    return