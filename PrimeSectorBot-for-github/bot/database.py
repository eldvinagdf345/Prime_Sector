import aiosqlite

from bot.config import DB_PATH

DEFAULT_SETTINGS = {
    "open_channel_link": "https://t.me/+P35vkTsER3szOTUy",
    "product_channel_link": "https://t.me/+your_private_invite_link",
    "price": "2000",
    "btn_join": "Вступить в Prime Sector 🤝",
    "btn_info": "ℹ️ Информация",
    "btn_suggest": "Предложи недостающий курс 📝",
    "btn_pay_sbp": "🇷🇺 Оплатить через СПБ",
    "btn_pay_crypto": "🪙 Оплатить криптовалютой",
    "btn_check_payment": "✅ Проверить оплату",
    "btn_enter": "Войти",
    "btn_back": "◀️ Назад",
    "info_text": (
        "<b>ℹ️ Информация\n\n• Поддержка: </b><b>@Fleuryqqe</b><b>\n• Политика конфиденциальности: </b>"
        '<a href="https://telegra.ph/Politika-konfidencialnosti-06-21-31"><b>читать</b></a>'
        "<b>\n• Пользовательское соглашение: </b>"
        '<a href="https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19"><b>читать</b></a>'
    ),
    "main_menu_text": "🚀 <b>Prime Sector | Открытый канал 🚀</b>",
    "payment_offer_text": (
        "<b>💵 Стоимость входа </b><b><u>навсегда</u>: 2000₽ | 25$ </b>\n\n"
        "<b>Стань частью комьюнити и получи пожизненный доступ ко всем лучшим и актуальным ресурсам </b>👇"
    ),
    "payment_link_ready_text": (
        "<b>✅ Заявка на оплату сформирована.\n\n"
        "Доступ к ресурсу предоставляется автоматически сразу после оплаты.</b>"
    ),
    "welcome_access_text": "Добро пожаловать!\n\nТвой доступ 👇",
    "suggest_prompt_text": "Напиши, какого курса не хватает — сообщение уйдёт администраторам.",
    "suggest_thanks_text": "Спасибо! Твоё предложение передано администраторам.",
}


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                transaction_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                username TEXT,
                chat_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                payment_method INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                username TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL
            )
            """
        )
        await db.commit()

        for key, value in DEFAULT_SETTINGS.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        await db.commit()


async def get_settings() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT key, value FROM settings") as cursor:
            rows = await cursor.fetchall()
    return {key: value for key, value in rows}


async def set_setting(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await db.commit()


async def create_order(
    transaction_id: str,
    user_id: int,
    username: str | None,
    chat_id: int,
    amount: float,
    currency: str,
    payment_method: int,
    status: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO orders
                (transaction_id, user_id, username, chat_id, amount, currency, payment_method, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (transaction_id, user_id, username, chat_id, amount, currency, payment_method, status),
        )
        await db.commit()


async def get_order(transaction_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE transaction_id = ?", (transaction_id,)
        ) as cursor:
            row = await cursor.fetchone()
    return dict(row) if row else None


async def mark_order_confirmed_once(transaction_id: str) -> bool:
    """Атомарно переводит заказ в CONFIRMED, только если он ещё не был подтверждён.
    Нужно, чтобы фоновый поллер и ручная проверка не выдали доступ дважды."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE orders SET status = 'CONFIRMED' WHERE transaction_id = ? AND status != 'CONFIRMED'",
            (transaction_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def update_order_status(transaction_id: str, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET status = ? WHERE transaction_id = ?",
            (status, transaction_id),
        )
        await db.commit()


async def upsert_admin(username: str, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO admins (username, user_id) VALUES (?, ?) "
            "ON CONFLICT(username) DO UPDATE SET user_id = excluded.user_id",
            (username, user_id),
        )
        await db.commit()


async def get_admin_chat_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM admins") as cursor:
            rows = await cursor.fetchall()
    return [row[0] for row in rows]
