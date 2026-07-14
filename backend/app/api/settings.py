from fastapi import APIRouter

from app.notifications import (
    TelegramError,
    TelegramNotifier,
    get_telegram_settings,
    set_telegram_settings,
)
from app.schemas.setting import TelegramSettings, TelegramTestResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/telegram", response_model=TelegramSettings)
def get_telegram() -> TelegramSettings:
    bot_token, chat_id = get_telegram_settings()
    return TelegramSettings(bot_token=bot_token, chat_id=chat_id)


@router.put("/telegram", response_model=TelegramSettings)
def update_telegram(payload: TelegramSettings) -> TelegramSettings:
    set_telegram_settings(payload.bot_token.strip(), payload.chat_id.strip())
    return payload


@router.post("/telegram/test", response_model=TelegramTestResponse)
async def test_telegram(payload: TelegramSettings) -> TelegramTestResponse:
    token = payload.bot_token.strip() or get_telegram_settings()[0]
    chat_id = payload.chat_id.strip() or get_telegram_settings()[1]
    if not token or not chat_id:
        return TelegramTestResponse(ok=False, error="bot_token and chat_id required")
    try:
        notifier = TelegramNotifier(token, chat_id)
        await notifier.test_connection()
    except TelegramError as exc:
        return TelegramTestResponse(ok=False, error=str(exc))
    except Exception as exc:
        return TelegramTestResponse(ok=False, error=f"Unexpected error: {exc}")
    return TelegramTestResponse(ok=True)
