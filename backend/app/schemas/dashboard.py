from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.product import StockState
from app.models.provider import DriverType, ScanStatus
from app.schemas._base import VPSBaseModel


class DashboardProduct(VPSBaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    display_name: str
    last_state: StockState
    last_count: int | None = None
    is_monitored: bool
    location_id: int | None = None


class DashboardLocation(VPSBaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    display_name: str
    is_monitored: bool
    last_seen_at: datetime | None = None


class DashboardProvider(VPSBaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    url: str
    driver_type: DriverType
    is_active: bool
    last_scan_at: datetime | None = None
    last_scan_status: ScanStatus | None = None
    products: list[DashboardProduct]
    locations: list[DashboardLocation]
