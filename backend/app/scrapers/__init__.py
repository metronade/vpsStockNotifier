from app.models.provider import DriverType
from app.scrapers.base import (
    BaseDriver,
    BaseDriverConfig,
    DiscoveredLocation,
    DiscoveredProduct,
    InitialScan,
    StockSnapshot,
)
from app.scrapers.dropdown_driver import DropdownConfig, DropdownDriver
from app.scrapers.spa_driver import ComplexSPADriver, SpaConfig
from app.scrapers.static_driver import StaticHTMLConfig, StaticHTMLDriver

DRIVER_REGISTRY: dict[DriverType, type[BaseDriver]] = {
    DriverType.STATIC_HTML: StaticHTMLDriver,
    DriverType.DYNAMIC_DROPDOWN: DropdownDriver,
    DriverType.COMPLEX_SPA: ComplexSPADriver,
}

CONFIG_REGISTRY: dict[DriverType, type[BaseDriverConfig]] = {
    DriverType.STATIC_HTML: StaticHTMLConfig,
    DriverType.DYNAMIC_DROPDOWN: DropdownConfig,
    DriverType.COMPLEX_SPA: SpaConfig,
}


def get_driver_class(driver_type: DriverType) -> type[BaseDriver]:
    try:
        return DRIVER_REGISTRY[driver_type]
    except KeyError as exc:
        raise ValueError(f"No driver registered for {driver_type!r}") from exc


def get_driver_config_class(driver_type: DriverType) -> type[BaseDriverConfig]:
    try:
        return CONFIG_REGISTRY[driver_type]
    except KeyError as exc:
        raise ValueError(f"No config registered for {driver_type!r}") from exc


__all__ = [
    "BaseDriver",
    "BaseDriverConfig",
    "DiscoveredLocation",
    "DiscoveredProduct",
    "InitialScan",
    "StockSnapshot",
    "StaticHTMLDriver",
    "StaticHTMLConfig",
    "DropdownDriver",
    "DropdownConfig",
    "ComplexSPADriver",
    "SpaConfig",
    "DRIVER_REGISTRY",
    "CONFIG_REGISTRY",
    "get_driver_class",
    "get_driver_config_class",
]
