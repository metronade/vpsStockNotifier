from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Location(TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint(
            "provider_id", "key", name="uq_locations_provider_key"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )

    # Stable identifier (slug or option value from the dropdown).
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # "Notify me when this location is added" — default true for dropdown/SPA drivers.
    is_monitored: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    # First time we saw this location (used for "new location" detection).
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    provider = relationship("Provider", back_populates="locations")
    products = relationship("Product", back_populates="location")
