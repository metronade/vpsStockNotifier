"""Dynamic-Dropdown driver (e.g. Aluy).

Treats presence in the dropdown as IN_STOCK: sites like Aluy hide OOS
locations entirely, so a visible option is by definition orderable.

Page shape:
    <select class="aluy-select w-full">
      <option value="ch">Switzerland</option>
      <option value="hk">Hong Kong</option>
      ...
    </select>

Absence — a previously-seen option disappearing — is handled by the
orchestrator, which transitions the corresponding Product to OUT_OF_STOCK.

Also supports custom (non-<select>) dropdowns via dropdown_opener_selector +
dropdown_option_selector.
"""
from playwright.async_api import Page
from pydantic import Field

from app.models.product import StockState
from app.scrapers.base import (
    BaseDriver,
    BaseDriverConfig,
    DiscoveredLocation,
    DiscoveredProduct,
    InitialScan,
    StockSnapshot,
)


class DropdownConfig(BaseDriverConfig):
    # Native <select> path
    dropdown_selector: str = "select.aluy-select, select.location-selector, select[name='location']"

    # Custom-dropdown path (used only if dropdown_selector doesn't match a <select>)
    dropdown_opener_selector: str = ""
    dropdown_option_selector: str = ""
    option_key_attribute: str = "data-key"   # empty string → use inner_text slug

    # Timeouts / waits
    nav_timeout_ms: int = 15000
    monitored_location_keys: list[str] = Field(default_factory=list)


class DropdownDriver(BaseDriver):
    name = "dynamic_dropdown"
    config_model = DropdownConfig

    async def discover(self, page: Page) -> InitialScan:
        locations = await self._read_locations(page)
        notes: list[str] = []
        if not locations:
            notes.append("No dropdown options found — check dropdown_selector.")
        return InitialScan(locations=locations, notes=notes)

    async def check_stock(self, page: Page) -> StockSnapshot:
        locations = await self._read_locations(page)
        products: list[DiscoveredProduct] = []
        for loc in locations:
            # Skip locations the user didn't enable, unless none are configured
            # (in which case we check everything).
            if (
                self.config.monitored_location_keys
                and loc.key not in self.config.monitored_location_keys
            ):
                continue
            products.append(
                DiscoveredProduct(
                    key=loc.key,
                    display_name=loc.display_name,
                    current_state=StockState.IN_STOCK,
                    current_count=None,
                    location_key=loc.key,
                )
            )
        return StockSnapshot(products=products, locations_seen=locations)

    async def _read_locations(self, page: Page) -> list[DiscoveredLocation]:
        select_el = await page.query_selector(self.config.dropdown_selector)
        if select_el:
            tag = await select_el.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                return await self._read_native_select(select_el)
        return await self._read_custom_dropdown(page)

    async def _read_native_select(self, select_el) -> list[DiscoveredLocation]:
        options = await select_el.query_selector_all("option")
        out: list[DiscoveredLocation] = []
        for opt in options:
            value = (await opt.get_attribute("value")) or ""
            text = (await opt.inner_text()).strip()
            if not value or not text:
                continue   # skip placeholder options
            out.append(DiscoveredLocation(key=value, display_name=text))
        return out

    async def _read_custom_dropdown(self, page: Page) -> list[DiscoveredLocation]:
        if self.config.dropdown_opener_selector:
            opener = await page.query_selector(self.config.dropdown_opener_selector)
            if opener:
                await opener.click()
                await page.wait_for_timeout(300)
        if not self.config.dropdown_option_selector:
            return []
        opts = await page.query_selector_all(self.config.dropdown_option_selector)
        out: list[DiscoveredLocation] = []
        for opt in opts:
            key: str
            if self.config.option_key_attribute:
                key = (await opt.get_attribute(self.config.option_key_attribute)) or ""
            else:
                key = ""
            text = (await opt.inner_text()).strip()
            if not key:
                key = _slugify(text)
            if not text:
                continue
            out.append(DiscoveredLocation(key=key, display_name=text))
        return out


def _slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
