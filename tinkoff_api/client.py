from tinkoff.invest import AsyncClient, OrderDirection, OrderType, OrderExecutionReportStatus
from config import TINKOFF_TOKEN, USE_SANDBOX
from datetime import datetime, timedelta
from utils.logger import log_action

# Определяем кастомное исключение внутри файла
class TinkoffAPIError(Exception):
    pass

class TinkoffClient:
    def __init__(self, token: str = TINKOFF_TOKEN, sandbox: bool = USE_SANDBOX):
        self.token = token
        self.sandbox = sandbox

    async def get_portfolio(self, account_id: str):
        try:
            async with AsyncClient(self.token) as client:
                if self.sandbox:
                    return await client.sandbox.get_sandbox_portfolio(account_id=account_id)
                return await client.operations.get_portfolio(account_id=account_id)
        except Exception as e:
            await log_action("tinkoff_error", f"get_portfolio: {str(e)}")
            raise TinkoffAPIError(f"Ошибка получения портфеля: {str(e)}")

    async def get_orders(self, account_id: str):
        try:
            async with AsyncClient(self.token) as client:
                if self.sandbox:
                    orders_response = await client.sandbox.get_sandbox_orders(account_id=account_id)
                else:
                    orders_response = await client.orders.get_orders(account_id=account_id)
                
                active_statuses = [
                    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_NEW,
                    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_PARTIALLYFILL
                ]
                
                active_orders = [
                    order for order in orders_response.orders
                    if order.execution_report_status in active_statuses
                ]
                
                executed_orders = [
                    order for order in orders_response.orders
                    if order.execution_report_status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL
                    and datetime.utcnow() - order.order_date < timedelta(days=7)
                ]
                
                return active_orders, executed_orders
        except Exception as e:
            await log_action("tinkoff_error", f"get_orders: {str(e)}")
            raise TinkoffAPIError(f"Ошибка получения ордеров: {str(e)}")

    async def execute_order(
        self,
        account_id: str,
        figi: str,
        quantity: int,
        price: float,
        direction: OrderDirection
    ):
        try:
            async with AsyncClient(self.token) as client:
                request_params = {
                    "figi": figi,
                    "quantity": quantity,
                    "price": price,
                    "direction": direction,
                    "account_id": account_id,
                    "order_type": OrderType.ORDER_TYPE_LIMIT
                }
                
                if self.sandbox:
                    response = await client.sandbox.post_sandbox_order(**request_params)
                else:
                    response = await client.orders.post_order(**request_params)
                
                await log_action(
                    "order_executed", 
                    f"{direction} {figi} {quantity}@{price}",
                    metadata={"status": response.execution_report_status.name}
                )
                return response
        except Exception as e:
            await log_action("tinkoff_error", f"execute_order: {str(e)}")
            raise TinkoffAPIError(f"Ошибка исполнения ордера: {str(e)}")