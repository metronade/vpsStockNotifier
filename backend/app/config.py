from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_path: Path = Path("/app/data/app.db")
    log_dir: Path = Path("/app/logs")

    # Telegram defaults — usually configured per-app via the dashboard,
    # but can be seeded from environment for unattended setups.
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    # Playwright
    playwright_headless: bool = True
    playwright_default_timeout_ms: int = 15000

    # Scheduler
    default_scan_interval_seconds: int = 300

    # Display timezone for absolute timestamps rendered in the UI. The backend
    # always serialises timestamps as UTC with offset; this setting only governs
    # how the frontend formats absolute times (e.g. "last scan at 15:45").
    display_timezone: str = "Europe/Berlin"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    def ensure_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
