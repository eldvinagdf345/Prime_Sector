import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from bot.config import CURRENCY, POLL_INTERVAL_SECONDS, POLL_MAX_ATTEMPTS
from bot.database import (
    create_order,
    get_order,
    get_settings,
    mark_order_confirmed_once,
    update_order_status,
)
from bot.keyboards import enter_channel_kb, payment_check_kb, payment_methods_kb
from bot.platega import PlategaError, create_transaction, get_transaction_status

router = Router()
logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"CONFIRMED", "CANCELED", "CHARGEBACKED"}


@router.callback_query(F.data == "join")
async def cb_join(callback: CallbackQuery) -> None:
    settings = await get_settings()
    text = settings["payment_offer_text"].replace("{price}", settings["price"])
    await callback.message.edit_text(text, reply_markup=payment_methods_kb(settings))
    await callback.answer()


@router.callback_query(F.data.startswith("pay:"))
async def cb_pay(callback: CallbackQuery) -> None:
    payment_method = int(callback.data.split(":")[1])
    settings = await get_settings()
    price = float(settings["price"])
    user = callback.from_user

    username_str = f"@{user.username}" if user.username else "no username"
    try:
        result = await create_transaction(
            payment_method=payment_method,
            amount=price,
            description=f"Доступ Prime Sector, user {user.id} ({username_str})",
            payload=str(user.id),
        )
    except PlategaError:
        logger.exception("Platega create_transaction failed")
        await callback.answer("Не удалось создать платёж, попробуй позже.", show_alert=True)
        return

    transaction_id = result["transactionId"]
    redirect_url = result["redirect"]

    await create_order(
        transaction_id=transaction_id,
        user_id=user.id,
        username=user.username,
        chat_id=callback.message.chat.id,
        amount=price,
        currency=CURRENCY,
        payment_method=payment_method,
        status=result.get("status", "PENDING"),
    )

    await callback.message.edit_text(
        settings["payment_link_ready_text"],
        reply_markup=payment_check_kb(settings, redirect_url, transaction_id),
    )
    await callback.answer()

    asyncio.create_task(_poll_payment(callback.bot, transaction_id))


async def _deliver_access(bot: Bot, chat_id: int, transaction_id: str) -> None:
    if not await mark_order_confirmed_once(transaction_id):
        return  # уже выдали доступ ранее
    settings = await get_settings()
    await bot.send_message(
        chat_id,
        settings["welcome_access_text"],
        reply_markup=enter_channel_kb(settings),
    )


async def _poll_payment(bot: Bot, transaction_id: str) -> None:
    order = await get_order(transaction_id)
    if not order:
        return
    for _ in range(POLL_MAX_ATTEMPTS):
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        try:
            data = await get_transaction_status(transaction_id)
        except PlategaError:
            logger.exception("Platega get_transaction_status failed for %s", transaction_id)
            continue

        status = data.get("status")
        if status == "CONFIRMED":
            await _deliver_access(bot, order["chat_id"], transaction_id)
            return
        if status in ("CANCELED", "CHARGEBACKED"):
            await update_order_status(transaction_id, status)
            return


@router.callback_query(F.data.startswith("check:"))
async def cb_check_payment(callback: CallbackQuery) -> None:
    transaction_id = callback.data.split(":", 1)[1]
    order = await get_order(transaction_id)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    if order["status"] == "CONFIRMED":
        await callback.answer("Оплата уже подтверждена, доступ выдан.", show_alert=True)
        return

    try:
        data = await get_transaction_status(transaction_id)
    except PlategaError:
        logger.exception("Platega get_transaction_status failed for %s", transaction_id)
        await callback.answer("Не удалось проверить статус, попробуй ещё раз чуть позже.", show_alert=True)
        return

    status = data.get("status")
    if status == "CONFIRMED":
        await _deliver_access(callback.bot, order["chat_id"], transaction_id)
        await callback.answer("Оплата подтверждена!")
    elif status in ("CANCELED", "CHARGEBACKED"):
        await update_order_status(transaction_id, status)
        await callback.answer("Платёж отменён. Попробуй создать оплату заново.", show_alert=True)
    else:
        await callback.answer("Оплата пока не поступила, подожди немного.", show_alert=True)
