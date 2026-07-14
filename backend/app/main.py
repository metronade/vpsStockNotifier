from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import providers as providers_api
from app.api import settings as settings_api
from app.api import dashboard as dashboard_api
from app.config import settings
from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app.scrapers.runner import shutdown_browser


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
        await shutdown_browser()


app = FastAPI(title="VPS Stock Notifier API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers_api.router)
app.include_router(settings_api.router)
app.include_router(dashboard_api.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "db_url": settings.db_url}
