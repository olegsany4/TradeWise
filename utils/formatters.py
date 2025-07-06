import pandas as pd
from tabulate import tabulate

def format_portfolio(portfolio) -> str:
    # Пример форматирования портфеля
    rows = []
    for pos in getattr(portfolio, 'positions', []):
        rows.append([pos.figi, pos.quantity, pos.current_price.units])
    return tabulate(rows, headers=["FIGI", "Qty", "Price"], tablefmt="github")
