from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import StockState
from app.models.provider import DriverType, ScanStatus


class ProviderBase(BaseModel):
    name: str
    url: str
    driver_type: DriverType
    scan_interval_seconds: int = Field(default=300, ge=60, le=86400)
    is_active: bool = True
    config_json: dict = Field(default_factory=dict)


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    scan_interval_seconds: int | None = Field(default=None, ge=60, le=86400)
    is_active: bool | None = None
    config_json: dict | None = None


class ProviderRead(ProviderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_scan_at: datetime | None = None
    last_scan_status: ScanStatus | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    provider_id: int
    location_id: int | None = None
    key: str
    display_name: str
    is_monitored: bool
    last_state: StockState
    last_count: int | None = None


class ProductUpdate(BaseModel):
    is_monitored: bool | None = None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    provider_id: int
    key: str
    display_name: str
    is_monitored: bool
    first_seen_at: datetime
    last_seen_at: datetime | None = None


class LocationUpdate(BaseModel):
    is_monitored: bool | None = None


class DiscoveredItem(BaseModel):
    """Item surfaced by an initial scan, rendered in the dashboard for selection."""

    key: str
    display_name: str
    kind: str  # "product" | "location"
    current_state: StockState | None = None


class InitialScanResponse(BaseModel):
    provider: ProviderRead
    discovered_products: list[DiscoveredItem]
    discovered_locations: list[DiscoveredItem]
    notes: list[str] = Field(default_factory=list)
