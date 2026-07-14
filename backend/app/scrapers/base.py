"""Driver abstractions for the three scraper strategies.

Each provider in the DB is associated with one DriverType (see app.models.provider).
The orchestrator picks the corresponding BaseDriver subclass from DRIVER_REGISTRY,
hands it a Playwright Page that has already navigated to provider.url, and calls
discover() (first run) or check_stock() (every interval thereafter).

Drivers should be stateless across calls — all persistent state lives in the DB.
Per-call state (selectors, wait times, monitored keys) is held in the driver's
config instance, which is a typed pydantic model validated from provider.config_json.
"""
import abc
from dataclasses import dataclass, field
from typing import Any, ClassVar

from playwright.async_api import Page
from pydantic import BaseModel, ConfigDict

from app.models.product import StockState


@dataclass
class DiscoveredProduct:
    """A stockable item the driver found on the page.

    For static-HTML drivers, `location_key` is None.
    For dropdown/SPA drivers, `location_key` ties the product to a discovered
    location so the orchestrator can set Product.location_id correctly.
    """
    key: str
    display_name: str
    current_state: StockState = StockState.UNKNOWN
    current_count: int | None = None
    location_key: str | None = None


@dataclass
class DiscoveredLocation:
    """A dropdown option or sidebar entry. Carries no stock state — the
    orchestrator checks whether the key is new in the DB to fire NEW_LOCATION."""
    key: str
    display_name: str


@dataclass
class InitialScan:
    """Result of the very first scan. Surfaced in the dashboard so the user
    can pick which items to monitor before the scheduler takes over."""
    products: list[DiscoveredProduct] = field(default_factory=list)
    locations: list[DiscoveredLocation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class StockSnapshot:
    """Result of a periodic scan."""
    products: list[DiscoveredProduct] = field(default_factory=list)
    # Full list of currently-present locations; orchestrator diffs against DB.
    locations_seen: list[DiscoveredLocation] = field(default_factory=list)
    error: str | None = None


class BaseDriverConfig(BaseModel):
    """Subclass per driver to declare its typed config fields."""

    model_config = ConfigDict(extra="forbid")


class BaseDriver(abc.ABC):
    """Common interface for all scraper drivers.

    Class attributes:
        name: matches a DriverType enum value (used by DRIVER_REGISTRY).
        config_model: the pydantic config class for this driver.

    Instance attributes:
        config: validated config instance.
    """

    name: ClassVar[str]
    config_model: ClassVar[type[BaseDriverConfig]]

    def __init__(self, config_dict: dict[str, Any] | None = None) -> None:
        self.config = self.config_model.model_validate(config_dict or {})

    @abc.abstractmethod
    async def discover(self, page: Page) -> InitialScan:
        """Enumerate every product/location on the page. Used once after a
        provider is added, and again on each interval to detect new locations."""
        ...

    @abc.abstractmethod
    async def check_stock(self, page: Page) -> StockSnapshot:
        """Re-discover, then for each monitored item read its current stock state.
        `locations_seen` should be populated for dropdown/SPA drivers so the
        orchestrator can detect new locations."""
        ...
