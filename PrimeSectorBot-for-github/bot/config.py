import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

PLATEGA_MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID")
PLATEGA_SECRET = os.getenv("PLATEGA_SECRET")
PLATEGA_BASE_URL = "https://app.platega.io"

DB_PATH = os.getenv("DB_PATH", "primesector.db")

# Telegram usernames (без @) пользователей с доступом к админ-панели.
# Добавляй/убирай username прямо здесь.
ADMIN_USERNAMES = {
    "Fleuryqqe",
}

# Коды методов оплаты Platega
PAY_METHOD_SBP = 2
PAY_METHOD_CRYPTO = 13

CURRENCY = "RUB"

# Как часто и сколько раз бот сам проверяет статус оплаты в фоне
POLL_INTERVAL_SECONDS = 7
POLL_MAX_ATTEMPTS = 130  # ~15 минут, под стандартный expiresIn Platega
