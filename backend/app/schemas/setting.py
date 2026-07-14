from pydantic import BaseModel


class TelegramSettings(BaseModel):
    bot_token: str = ""
    chat_id: str = ""


class TelegramTestResponse(BaseModel):
    ok: bool
    error: str | None = None
