from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.stock_history import EventType


class StockHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    provider_id: int
    product_id: int | None = None
    location_id: int | None = None
    event_type: EventType
    previous_state: str | None = None
    new_state: str | None = None
    details: dict
    created_at: datetime


class ScanNowResponse(BaseModel):
    status: str  # "ok" | "error"
    error: str | None = None
    state_changes: int = 0
    new_locations: int = 0
