from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.models import Order
from db.session import async_session
from datetime import datetime
from sqlalchemy import select
from utils.logger import log_action
from utils.message import safe_reply

async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание нового ордера"""
    try:
        args = context.args
        if len(args) < 4:
            await safe_reply(update, context, "Формат: /order BUY|SELL TICKER КОЛ-ВО ЦЕНА\nПример: /order BUY SBER 10 234.50")
            return
        
        side, symbol, quantity, price = args[0], args[1].upper(), float(args[2]), float(args[3])
        
        if side.upper() not in ["BUY", "SELL"]:
            await safe_reply(update, context, "❌ Неверная сторона ордера. Используйте BUY или SELL")
            return
            
        if quantity <= 0 or price <= 0:
            await safe_reply(update, context, "❌ Количество и цена должны быть положительными числами")
            return

        async with async_session() as session:
            order = Order(
                user_id=update.effective_user.id,
                symbol=symbol,
                side=side.upper(),
                quantity=quantity,
                price=price,
                status="NEW",
                created_at=datetime.utcnow()
            )
            session.add(order)
            await session.commit()
            
            keyboard = [[InlineKeyboardButton("❌ Отменить ордер", callback_data=f"cancel_{order.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await safe_reply(
                update,
                context,
                f"🧾 Ордер #{order.id} создан:\n"
                f"📌 {side.upper()} {quantity} {symbol} по {price} ₽\n"
                f"🔄 Статус: {order.status}",
                reply_markup=reply_markup
            )
            
        await log_action("order_created", f"{side} {symbol} {quantity}@{price}", update.effective_user.id)
        
    except ValueError:
        await safe_reply(update, context, "❌ Неверный формат чисел. Убедитесь, что количество и цена - числа")
    except Exception as e:
        await safe_reply(update, context, f"⚠️ Ошибка при создании ордера: {str(e)}")
        await log_action("order_error", str(e), update.effective_user.id)

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр списка ордеров с кнопками управления"""
    try:
        user_id = update.effective_user.id
        async with async_session() as session:
            stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(10)
            result = await session.execute(stmt)
            orders = result.scalars().all()

        if not orders:
            await safe_reply(update, context, "📭 У вас пока нет ордеров")
            return

        text = "📋 Ваши последние ордера:\n\n"
        keyboard = []
        
        for order in orders:
            status_icon = "🟢" if order.status == "FILLED" else "🟡" if order.status == "NEW" else "🔴"
            text += (
                f"{status_icon} *{order.side} {order.symbol}*\n"
                f"  • Кол-во: {order.quantity} шт\n"
                f"  • Цена: {order.price} ₽\n"
                f"  • Статус: {order.status}\n"
                f"  • Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"  • ID: #{order.id}\n\n"
            )
            
            if order.status in ["NEW", "ACTIVE"]:
                keyboard.append([InlineKeyboardButton(
                    f"❌ Отменить {order.symbol} #{order.id}", 
                    callback_data=f"cancel_{order.id}"
                )])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await safe_reply(update, context, text, parse_mode="Markdown", reply_markup=reply_markup)
        await log_action("orders_listed", f"{len(orders)} orders", user_id)
        
    except Exception as e:
        await safe_reply(update, context, f"⚠️ Ошибка при получении ордеров: {str(e)}")
        await log_action("orders_error", str(e), update.effective_user.id)

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена ордера по ID"""
    try:
        if not context.args:
            await safe_reply(update, context, "Укажите ID ордера: /cancelorder 12")
            return
            
        order_id = int(context.args[0])
        user_id = update.effective_user.id

        async with async_session() as session:
            order = await session.get(Order, order_id)
            if not order or order.user_id != user_id:
                await safe_reply(update, context, "❌ Ордер не найден или не принадлежит вам")
                return

            if order.status in ("FILLED", "CANCELLED"):
                await safe_reply(update, context, f"ℹ️ Ордер #{order_id} уже завершен (статус: {order.status})")
                return

            order.status = "CANCELLED"
            await session.commit()

        await safe_reply(update, context, f"❌ Ордер #{order_id} отменён")
        await log_action("order_cancelled", f"#{order_id}", user_id)
        
    except ValueError:
        await safe_reply(update, context, "❌ Неверный формат ID. Укажите числовой идентификатор ордера")
    except Exception as e:
        await safe_reply(update, context, f"⚠️ Ошибка при отмене ордера: {str(e)}")
        await log_action("cancel_error", str(e), update.effective_user.id)

async def cancel_order_button(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int):
    """Обработка кнопки отмены ордера"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    try:
        async with async_session() as session:
            order = await session.get(Order, order_id)
            if not order or order.user_id != user_id:
                await query.edit_message_text("❌ Ордер не найден или не принадлежит вам")
                return

            if order.status in ("FILLED", "CANCELLED"):
                await query.edit_message_text(f"ℹ️ Ордер #{order_id} уже завершен (статус: {order.status})")
                return

            order.status = "CANCELLED"
            await session.commit()

        await query.edit_message_text(
            f"❌ Ордер #{order_id} отменён\n"
            f"📌 {order.side} {order.quantity} {order.symbol} по {order.price} ₽"
        )
        await log_action("order_cancelled", f"#{order_id}", user_id)
        
    except Exception as e:
        await query.edit_message_text(f"⚠️ Ошибка при отмене ордера: {str(e)}")
        await log_action("cancel_error", str(e), user_id)

async def api_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает активные и исполненные ордера через API Tinkoff"""
    try:
        from config import USE_SANDBOX, PRIMARY_ACCOUNT_ID
        from tinkoff_api.client import TinkoffClient
        from utils.formatters import format_orders
        from tinkoff_api.accounts import get_or_create_sandbox_account

        account_id = await get_or_create_sandbox_account() if USE_SANDBOX else PRIMARY_ACCOUNT_ID
        client = TinkoffClient(sandbox=USE_SANDBOX)
        active_orders, executed_orders = await client.get_orders(account_id)
        text = format_orders(active_orders, executed_orders)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="api_orders")],
            [InlineKeyboardButton("📋 Мои ордера", callback_data="orders")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await safe_reply(update, context, text, reply_markup=reply_markup)
        await log_action("api_orders", "success", update.effective_user.id)
        
    except Exception as e:
        await safe_reply(update, context, f"⚠️ Ошибка при получении ордеров: {str(e)}")
        await log_action("api_orders_error", str(e), update.effective_user.id)