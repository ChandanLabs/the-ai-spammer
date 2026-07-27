import logging
from typing import Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


async def send_telegram_message(
    telegram_id: str,
    text: str,
    parse_mode: str = "Markdown",
) -> Optional[int]:
    """
    Send a message to a Telegram user by their chat ID.
    Returns the Telegram message ID on success, None on failure.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured — skipping send")
        return None

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()
            if data.get("ok"):
                msg_id = data["result"]["message_id"]
                logger.info(f"Message sent to {telegram_id}, msg_id={msg_id}")
                return msg_id
            else:
                logger.error(f"Telegram API error: {data.get('description')}")
                return None
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {telegram_id}: {e}")
            return None
