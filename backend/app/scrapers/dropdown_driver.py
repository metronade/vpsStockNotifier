"""Dynamic-Dropdown driver (e.g. Aluy).

Page shape:
    <select class="location-selector">
      <option value="">Select location...</option>
      <option value="switzerland">Switzerland</option>
      <option value="hong-kong">Hong Kong</option>
      ...
    </select>
    ...after selecting an option:
    <div class="order-btn disabled">Out of stock</div>
    OR
    <div class="order-btn">Order now</div>

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
    dropdown_selector: str = "select.location-selector, select[name='location']"

    # Custom-dropdown path (used only if dropdown_selector doesn't match a <select>)
    dropdown_opener_selector: str = ""
    dropdown_option_selector: str = ""
    option_key_attribute: str = "data-key"   # empty string → use inner_text slug

    # Stock-state detection after a location is selected
    out_of_stock_text: str = "Out of stock"
    out_of_stock_selector: str = ".order-btn.disabled, .btn.disabled, .out-of-stock"
    in_stock_selector: str = ".order-btn:not(.disabled), .btn-primary:not(.disabled)"

    # Timeouts / waits
    nav_timeout_ms: int = 15000
    post_select_wait_ms: int = 500
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
            selected = await self._select_location(page, loc.key)
            if not selected:
                continue
            await page.wait_for_timeout(self.config.post_select_wait_ms)
            state, count = await self._read_stock_state(page)
            products.append(
                DiscoveredProduct(
                    key=loc.key,
                    display_name=loc.display_name,
                    current_state=state,
                    current_count=count,
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

    async def _select_location(self, page: Page, key: str) -> bool:
        select_el = await page.query_selector(self.config.dropdown_selector)
        if select_el:
            tag = await select_el.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                await select_el.select_option(value=key)
                return True
        # Custom dropdown: open, click the matching option
        if self.config.dropdown_opener_selector:
            opener = await page.query_selector(self.config.dropdown_opener_selector)
            if opener:
                await opener.click()
                await page.wait_for_timeout(300)
        opts = await page.query_selector_all(self.config.dropdown_option_selector)
        for opt in opts:
            opt_key = (
                (await opt.get_attribute(self.config.option_key_attribute)) or ""
                if self.config.option_key_attribute
                else _slugify((await opt.inner_text()).strip())
            )
            if opt_key == key:
                await opt.click()
                return True
        return False

    async def _read_stock_state(self, page: Page) -> tuple[StockState, int | None]:
        # Positive signal first — if a clearly-enabled order button is present,
        # the location is orderable.
        if self.config.in_stock_selector:
            in_stock = await page.query_selector(self.config.in_stock_selector)
            if in_stock:
                return StockState.IN_STOCK, None
        # Negative signals
        if self.config.out_of_stock_selector:
            oos_el = await page.query_selector(self.config.out_of_stock_selector)
            if oos_el:
                return StockState.OUT_OF_STOCK, 0
        # Fall back to body text scan (catches overlay text without dedicated classes)
        body_text = await page.evaluate("() => document.body.innerText") or ""
        if self.config.out_of_stock_text.lower() in body_text.lower():
            return StockState.OUT_OF_STOCK, 0
        return StockState.UNKNOWN, None


def _slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
