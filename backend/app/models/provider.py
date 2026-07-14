import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class DriverType(str, enum.Enum):
    """Maps directly to the three scraper driver classes built in step 3."""

    STATIC_HTML = "static_html"          # WHMCS-style, e.g. Frantech
    DYNAMIC_DROPDOWN = "dynamic_dropdown"  # e.g. Aluy
    COMPLEX_SPA = "complex_spa"            # slider/hover/sidebar, e.g. Kyun


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    OK = "ok"
    ERROR = "error"


class Provider(TimestampMixin, Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    driver_type: Mapped[DriverType] = mapped_column(
        Enum(DriverType, name="driver_type"), nullable=False
    )
    scan_interval_seconds: Mapped[int] = mapped_column(
        Integer, default=300, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_scan_status: Mapped[ScanStatus | None] = mapped_column(
        Enum(ScanStatus, name="scan_status"), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Driver-specific config: selectors, chosen product keys, slider coords, etc.
    # Typed/validated per driver in step 3.
    config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    products = relationship(
        "Product", back_populates="provider", cascade="all, delete-orphan"
    )
    locations = relationship(
        "Location", back_populates="provider", cascade="all, delete-orphan"
    )
