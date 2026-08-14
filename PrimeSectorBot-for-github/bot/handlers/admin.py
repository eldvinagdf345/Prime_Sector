from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMIN_USERNAMES
from bot.database import get_settings, set_setting
from bot.keyboards import (
    BUTTON_SETTING_KEYS,
    MESSAGE_SETTING_KEYS,
    admin_buttons_kb,
    admin_menu_kb,
    admin_messages_kb,
    cancel_edit_kb,
)
from bot.states import AdminEdit

router = Router()


def _is_admin(username: str | None) -> bool:
    return bool(username) and username in ADMIN_USERNAMES


router.message.filter(lambda message: _is_admin(message.from_user.username))
router.callback_query.filter(lambda callback: _is_admin(callback.from_user.username))


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("⚙️ Админ-панель", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "admin:price")
async def cb_admin_price(callback: CallbackQuery, state: FSMContext) -> None:
    settings = await get_settings()
    await state.set_state(AdminEdit.price)
    await callback.message.edit_text(
        f"Текущая цена: {settings['price']} руб.\nВведи новую цену числом (только цифры):",
        reply_markup=cancel_edit_kb("admin_panel"),
    )
    await callback.answer()


@router.message(AdminEdit.price)
async def process_price(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Нужно целое число, например 2000. Попробуй ещё раз:")
        return
    await set_setting("price", message.text.strip())
    await state.clear()
    await message.answer("Цена обновлена ✅", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin:open_link")
async def cb_admin_open_link(callback: CallbackQuery, state: FSMContext) -> None:
    settings = await get_settings()
    await state.set_state(AdminEdit.open_link)
    await callback.message.edit_text(
        f"Текущая ссылка на открытый канал:\n{settings['open_channel_link']}\n\n"
        "Пришли новую ссылку:",
        reply_markup=cancel_edit_kb("admin_panel"),
    )
    await callback.answer()


@router.message(AdminEdit.open_link)
async def process_open_link(message: Message, state: FSMContext) -> None:
    link = (message.text or "").strip()
    if not link.startswith("http"):
        await message.answer("Похоже, это не ссылка. Пришли корректный URL (начинается с http):")
        return
    await set_setting("open_channel_link", link)
    await state.clear()
    await message.answer("Ссылка на открытый канал обновлена ✅", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin:product_link")
async def cb_admin_product_link(callback: CallbackQuery, state: FSMContext) -> None:
    settings = await get_settings()
    await state.set_state(AdminEdit.product_link)
    await callback.message.edit_text(
        f"Текущая ссылка на закрытый канал (продукт):\n{settings['product_channel_link']}\n\n"
        "Пришли новую ссылку:",
        reply_markup=cancel_edit_kb("admin_panel"),
    )
    await callback.answer()


@router.message(AdminEdit.product_link)
async def process_product_link(message: Message, state: FSMContext) -> None:
    link = (message.text or "").strip()
    if not link.startswith("http"):
        await message.answer("Похоже, это не ссылка. Пришли корректный URL (начинается с http):")
        return
    await set_setting("product_channel_link", link)
    await state.clear()
    await message.answer("Ссылка на закрытый канал обновлена ✅", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin:buttons")
async def cb_admin_buttons(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Какую кнопку изменить?", reply_markup=admin_buttons_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:btn:"))
async def cb_admin_btn_edit(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 2)[2]
    if key not in BUTTON_SETTING_KEYS:
        await callback.answer("Неизвестная кнопка", show_alert=True)
        return
    settings = await get_settings()
    await state.set_state(AdminEdit.text_field)
    await state.update_data(key=key, return_to="buttons")
    await callback.message.edit_text(
        f"Текущий текст кнопки {BUTTON_SETTING_KEYS[key]}: {settings[key]}\n\nПришли новый текст:",
        reply_markup=cancel_edit_kb("admin:buttons"),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:messages")
async def cb_admin_messages(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Какой текст изменить?", reply_markup=admin_messages_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:msg:"))
async def cb_admin_msg_edit(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 2)[2]
    if key not in MESSAGE_SETTING_KEYS:
        await callback.answer("Неизвестный текст", show_alert=True)
        return
    settings = await get_settings()
    await state.set_state(AdminEdit.text_field)
    await state.update_data(key=key, return_to="messages")
    await callback.message.edit_text(
        f"Текущий текст «{MESSAGE_SETTING_KEYS[key]}»:\n\n{settings[key]}\n\n"
        "Пришли новый текст. Можно выделить жирным/курсивом/подчёркиванием через "
        "форматирование Telegram (выдели текст при наборе и нажми Ж/К/etc), "
        "а если у тебя Telegram Premium — можно вставить премиум-эмодзи. "
        "Всё это сохранится как есть.",
        reply_markup=cancel_edit_kb("admin:messages"),
    )
    await callback.answer()


@router.message(AdminEdit.text_field)
async def process_text_field(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("key")
    return_to = data.get("return_to")
    if not key:
        await state.clear()
        return
    if return_to == "messages":
        # html_text сохраняет форматирование (жирный, курсив, премиум-эмодзи и т.д.)
        new_value = message.html_text or ""
    else:
        # у кнопок нет форматирования — сохраняем как обычный текст
        new_value = message.text or ""
    await set_setting(key, new_value)
    await state.clear()
    if return_to == "buttons":
        await message.answer("Текст кнопки обновлён ✅", reply_markup=admin_buttons_kb())
    elif return_to == "messages":
        await message.answer("Текст обновлён ✅", reply_markup=admin_messages_kb())
    else:
        await message.answer("Текст обновлён ✅", reply_markup=admin_menu_kb())
