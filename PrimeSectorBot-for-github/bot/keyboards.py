from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import PAY_METHOD_CRYPTO, PAY_METHOD_SBP


def main_menu_kb(settings: dict, is_admin: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=settings["btn_join"], callback_data="join")
    builder.button(text=settings["btn_info"], callback_data="info")
    builder.button(text=settings["btn_suggest"], callback_data="suggest")
    builder.adjust(1)
    if is_admin:
        builder.row(InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel"))
    return builder.as_markup()


def back_to_menu_kb(settings: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=settings["btn_back"], callback_data="back_to_menu")
    return builder.as_markup()


def payment_methods_kb(settings: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=settings["btn_pay_sbp"], callback_data=f"pay:{PAY_METHOD_SBP}")
    builder.button(text=settings["btn_pay_crypto"], callback_data=f"pay:{PAY_METHOD_CRYPTO}")
    builder.button(text=settings["btn_back"], callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_check_kb(settings: dict, redirect_url: str, transaction_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Перейти к оплате", url=redirect_url))
    builder.row(
        InlineKeyboardButton(
            text=settings["btn_check_payment"], callback_data=f"check:{transaction_id}"
        )
    )
    builder.row(InlineKeyboardButton(text=settings["btn_back"], callback_data="join"))
    return builder.as_markup()


def enter_channel_kb(settings: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=settings["btn_enter"], url=settings["product_channel_link"])
    return builder.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Изменить цену", callback_data="admin:price")
    builder.button(text="🔗 Ссылка на открытый канал", callback_data="admin:open_link")
    builder.button(text="🔗 Ссылка на закрытый канал (продукт)", callback_data="admin:product_link")
    builder.button(text="✏️ Тексты кнопок", callback_data="admin:buttons")
    builder.button(text="📝 Тексты сообщений", callback_data="admin:messages")
    builder.button(text="◀️ Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


BUTTON_SETTING_KEYS = {
    "btn_join": "«Вступить в Prime Sector»",
    "btn_info": "«Информация»",
    "btn_suggest": "«Предложи недостающий курс»",
    "btn_pay_sbp": "«Оплатить СБП»",
    "btn_pay_crypto": "«Оплатить криптовалютой»",
    "btn_enter": "«Войти» (в сообщении о доступе)",
}


def admin_buttons_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in BUTTON_SETTING_KEYS.items():
        builder.button(text=label, callback_data=f"admin:btn:{key}")
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()


MESSAGE_SETTING_KEYS = {
    "main_menu_text": "Текст в /start (со ссылкой на открытый канал)",
    "info_text": "Раздел «Информация»",
    "payment_offer_text": "Сообщение с предложением оплаты (можно использовать {price})",
    "payment_link_ready_text": "Сообщение «Ссылка на оплату готова»",
    "welcome_access_text": "Сообщение «Добро пожаловать» после оплаты",
    "suggest_prompt_text": "Запрос текста в «Предложи недостающий курс»",
    "suggest_thanks_text": "Благодарность после предложения курса",
}


def admin_messages_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in MESSAGE_SETTING_KEYS.items():
        builder.button(text=label, callback_data=f"admin:msg:{key}")
    builder.button(text="◀️ Назад", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()
