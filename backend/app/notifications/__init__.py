"""Settings access helpers + notifier factory.

Settings live in the key/value `settings` table. Telegram creds in particular
are configured via the dashboard (or seeded from env) and read here on every
notification dispatch — no in-memory caching, so updates take effect immediately.
"""
from app.database import SessionLocal
from app.models.setting import Setting
from app.notifications.telegram import TelegramError, TelegramNotifier

TELEGRAM_BOT_TOKEN_KEY = "telegram_bot_token"
TELEGRAM_CHAT_ID_KEY = "telegram_chat_id"


def get_setting(key: str, default: str = "") -> str:
    db = SessionLocal()
    try:
        row = db.get(Setting, key)
        return row.value if row else default
    finally:
        db.close()


def set_setting(key: str, value: str) -> None:
    db = SessionLocal()
    try:
        row = db.get(Setting, key)
        if row is not None:
            row.value = value
        else:
            db.add(Setting(key=key, value=value))
        db.commit()
    finally:
        db.close()


def get_telegram_settings() -> tuple[str, str]:
    return (
        get_setting(TELEGRAM_BOT_TOKEN_KEY),
        get_setting(TELEGRAM_CHAT_ID_KEY),
    )


def set_telegram_settings(bot_token: str, chat_id: str) -> None:
    set_setting(TELEGRAM_BOT_TOKEN_KEY, bot_token)
    set_setting(TELEGRAM_CHAT_ID_KEY, chat_id)


def get_notifier() -> TelegramNotifier | None:
    """Returns None if Telegram isn't configured — caller should treat that as
    'notifications disabled', not an error."""
    token, chat_id = get_telegram_settings()
    if not token or not chat_id:
        return None
    try:
        return TelegramNotifier(token, chat_id)
    except TelegramError:
        return None


__all__ = [
    "TelegramError",
    "TelegramNotifier",
    "get_setting",
    "set_setting",
    "get_telegram_settings",
    "set_telegram_settings",
    "get_notifier",
]
