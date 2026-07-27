import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMIN_USERNAMES
from bot.database import get_admin_chat_ids, get_settings, upsert_admin
from bot.keyboards import back_to_menu_kb, main_menu_kb
from bot.states import SuggestCourse

router = Router()


def _is_admin(username: str | None) -> bool:
    return bool(username) and username in ADMIN_USERNAMES


async def _main_menu_text(settings: dict) -> str:
    link = html.escape(settings["open_channel_link"], quote=True)
    # main_menu_text уже приходит как безопасный HTML (сохранён через message.html_text
    # в админке), поэтому повторно не экранируем — иначе сломаем жирный текст/эмодзи-теги
    text = settings["main_menu_text"]
    return f'<a href="{link}">{text}</a>'


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    username = message.from_user.username
    if _is_admin(username):
        await upsert_admin(username, message.from_user.id)

    settings = await get_settings()
    await message.answer(
        await _main_menu_text(settings),
        reply_markup=main_menu_kb(settings, _is_admin(username)),
    )


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    settings = await get_settings()
    username = callback.from_user.username
    await callback.message.edit_text(
        await _main_menu_text(settings),
        reply_markup=main_menu_kb(settings, _is_admin(username)),
    )
    await callback.answer()


@router.callback_query(F.data == "info")
async def cb_info(callback: CallbackQuery) -> None:
    settings = await get_settings()
    await callback.message.edit_text(
        settings["info_text"],
        reply_markup=back_to_menu_kb(settings),
    )
    await callback.answer()


@router.callback_query(F.data == "suggest")
async def cb_suggest(callback: CallbackQuery, state: FSMContext) -> None:
    settings = await get_settings()
    await state.set_state(SuggestCourse.waiting_text)
    await callback.message.edit_text(
        settings["suggest_prompt_text"],
        reply_markup=back_to_menu_kb(settings),
    )
    await callback.answer()


@router.message(SuggestCourse.waiting_text)
async def process_suggestion(message: Message, state: FSMContext) -> None:
    await state.clear()
    admin_ids = await get_admin_chat_ids()
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    for admin_id in admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                f"💡 Предложение курса от {username} (id {message.from_user.id}):\n\n{message.text}",
            )
        except Exception:
            continue

    settings = await get_settings()
    await message.answer(
        settings["suggest_thanks_text"],
        reply_markup=back_to_menu_kb(settings),
    )
