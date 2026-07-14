"""Telegram Bot API client."""
import httpx

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramError(Exception):
    pass


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        if not bot_token or not chat_id:
            raise TelegramError("bot_token and chat_id are required")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._base = f"{TELEGRAM_API_BASE}/bot{bot_token}"

    async def send(self, text: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self._base}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
        if resp.status_code != 200:
            raise TelegramError(
                f"Telegram API {resp.status_code}: {resp.text[:200]}"
            )

    async def test_connection(self) -> None:
        """Raises TelegramError on failure."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{self._base}/sendMessage", json={
                "chat_id": self.chat_id,
                "text": "VPS Stock Notifier: Telegram connection works.",
                "disable_web_page_preview": True,
            })
        if resp.status_code != 200:
            raise TelegramError(f"Telegram API {resp.status_code}: {resp.text[:200]}")
