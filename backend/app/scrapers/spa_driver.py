"""Complex-SPA driver (e.g. Kyun) — sliders, hover-revealed controls, sidebars.

Strategy:
    1. Try the sidebar route first — look for a clickable location list
       (buttons/links with location names). This is more reliable than hover.
    2. If the sidebar isn't found, fall back to the slider: hover at configured
       coordinates to reveal the controls, then look for the same sidebar.

Once a location button is clicked, wait for the "System Specs" area to update
and look for any of:
    - explicit "Out of stock" text
    - disabled / greyed-out buttons
    - `pointer-events: none` or similar deactivation classes
"""
from playwright.async_api import ElementHandle, Page
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


class SpaConfig(BaseDriverConfig):
    # Sidebar route
    location_button_selector: str = (
        ".location-list button, .locations a, [data-location]"
    )
    location_name_attribute: str = ""          # empty → use inner_text
    # Slider route (fallback)
    slider_selector: str = ""
    slider_hover_offset_x: float = 0.0
    slider_hover_offset_y: float = 0.0
    hover_reveal_wait_ms: int = 700

    # Stock detection
    spec_container_selector: str = ".system-specs, .specs, .product-config"
    out_of_stock_text: str = "Out of stock"
    out_of_stock_selectors: list[str] = Field(
        default_factory=lambda: [
            ".out-of-stock",
            ".disabled",
            '[style*="pointer-events: none"]',
            ".btn-disabled",
        ]
    )
    in_stock_selectors: list[str] = Field(default_factory=list)

    # Timing
    nav_timeout_ms: int = 20000
    post_click_wait_ms: int = 500
    monitored_location_keys: list[str] = Field(default_factory=list)


class ComplexSPADriver(BaseDriver):
    name = "complex_spa"
    config_model = SpaConfig

    async def discover(self, page: Page) -> InitialScan:
        await self._ensure_controls_visible(page)
        locations = await self._read_locations(page)
        notes: list[str] = []
        if not locations:
            notes.append(
                "No location buttons matched "
                f"'{self.config.location_button_selector}'."
            )
        return InitialScan(locations=locations, notes=notes)

    async def check_stock(self, page: Page) -> StockSnapshot:
        await self._ensure_controls_visible(page)
        locations = await self._read_locations(page)
        products: list[DiscoveredProduct] = []
        for loc in locations:
            if (
                self.config.monitored_location_keys
                and loc.key not in self.config.monitored_location_keys
            ):
                continue
            clicked = await self._click_location(page, loc.key)
            if not clicked:
                continue
            await page.wait_for_timeout(self.config.post_click_wait_ms)
            state = await self._read_stock_state(page)
            products.append(
                DiscoveredProduct(
                    key=loc.key,
                    display_name=loc.display_name,
                    current_state=state,
                    current_count=None,
                    location_key=loc.key,
                )
            )
        return StockSnapshot(products=products, locations_seen=locations)

    async def _ensure_controls_visible(self, page: Page) -> None:
        """Reveal the sidebar — try directly first, fall back to slider hover."""
        existing = await page.query_selector(self.config.location_button_selector)
        if existing:
            return
        if not self.config.slider_selector:
            return
        slider = await page.query_selector(self.config.slider_selector)
        if not slider:
            return
        box = await slider.bounding_box()
        if not box:
            return
        await page.mouse.move(
            box["x"] + self.config.slider_hover_offset_x,
            box["y"] + self.config.slider_hover_offset_y,
        )
        await page.wait_for_timeout(self.config.hover_reveal_wait_ms)

    async def _read_locations(self, page: Page) -> list[DiscoveredLocation]:
        buttons = await page.query_selector_all(self.config.location_button_selector)
        out: list[DiscoveredLocation] = []
        seen_keys: set[str] = set()
        for btn in buttons:
            name = await self._extract_name(btn)
            if not name:
                continue
            key = _slugify(name)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            out.append(DiscoveredLocation(key=key, display_name=name))
        return out

    async def _extract_name(self, el: ElementHandle) -> str:
        if self.config.location_name_attribute:
            value = await el.get_attribute(self.config.location_name_attribute)
            if value:
                return value.strip()
        try:
            return (await el.inner_text()).strip()
        except Exception:
            return ""

    async def _click_location(self, page: Page, key: str) -> bool:
        buttons = await page.query_selector_all(self.config.location_button_selector)
        for btn in buttons:
            name = await self._extract_name(btn)
            if not name:
                continue
            if _slugify(name) == key:
                await btn.click()
                return True
        return False

    async def _read_stock_state(self, page: Page) -> StockState:
        # Spec container must be present — its absence means the click didn't load anything.
        try:
            await page.wait_for_selector(
                self.config.spec_container_selector,
                timeout=self.config.nav_timeout_ms,
            )
        except Exception:
            return StockState.UNKNOWN

        # Positive signals
        for sel in self.config.in_stock_selectors:
            if await page.query_selector(sel):
                return StockState.IN_STOCK

        # Negative signals — selectors first
        for sel in self.config.out_of_stock_selectors:
            if await page.query_selector(sel):
                return StockState.OUT_OF_STOCK

        # Body-text fallback
        body_text = (await page.evaluate("() => document.body.innerText")) or ""
        if self.config.out_of_stock_text.lower() in body_text.lower():
            return StockState.OUT_OF_STOCK

        # No negative signal found → assume in stock
        return StockState.IN_STOCK


def _slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
