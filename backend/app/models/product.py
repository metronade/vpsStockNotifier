import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class StockState(str, enum.Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint(
            "provider_id", "key", name="uq_products_provider_key"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )
    # For dropdown/SPA drivers: which location this product belongs to.
    # NULL for static-HTML providers where products are not location-scoped.
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=True
    )

    # Stable identifier the driver extracts (e.g. "CH RYZEN KVM 1GB" or a slug).
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_monitored: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    last_state: Mapped[StockState] = mapped_column(
        Enum(StockState, name="stock_state"),
        default=StockState.UNKNOWN,
        nullable=False,
    )
    last_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    provider = relationship("Provider", back_populates="products")
    location = relationship("Location", back_populates="products")
