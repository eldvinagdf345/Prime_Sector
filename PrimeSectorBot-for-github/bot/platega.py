import aiohttp

from bot.config import CURRENCY, PLATEGA_BASE_URL, PLATEGA_MERCHANT_ID, PLATEGA_SECRET


class PlategaError(Exception):
    pass


def _headers() -> dict:
    return {
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_SECRET,
        "Content-Type": "application/json",
    }


async def create_transaction(
    payment_method: int,
    amount: float,
    description: str,
    payload: str = "",
) -> dict:
    body = {
        "paymentMethod": payment_method,
        "paymentDetails": {"amount": amount, "currency": CURRENCY},
        "description": description,
        "payload": payload,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{PLATEGA_BASE_URL}/transaction/process",
            json=body,
            headers=_headers(),
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise PlategaError(f"Platega create_transaction failed: {resp.status} {data}")
            return data


async def get_transaction_status(transaction_id: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{PLATEGA_BASE_URL}/transaction/{transaction_id}",
            headers=_headers(),
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise PlategaError(f"Platega get_transaction_status failed: {resp.status} {data}")
            return data
