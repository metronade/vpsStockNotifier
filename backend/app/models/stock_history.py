import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventType(str, enum.Enum):
    STATE_CHANGE = "state_change"      # product went in-stock/out-of-stock
    NEW_LOCATION = "new_location"      # previously unseen location appeared
    SCAN_ERROR = "scan_error"          # driver raised an exception


class StockHistory(Base):
    """Immutable audit log. One row per notable event (no edits, no updates)."""

    __tablename__ = "stock_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"), nullable=False
    )
    # Free-form strings (not the enum) because state values vary across event types.
    previous_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
