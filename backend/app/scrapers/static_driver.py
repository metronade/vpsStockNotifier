"""Static-HTML driver for WHMCS-style product pages (e.g. Frantech / BuyVM).

Page shape:
    <div class="package">
      <h3 class="package-title">CH RYZEN KVM 1GB</h3>
      ...
      <span class="package-stock">0 Available</span>   <!-- or "Out of Stock" -->
    </div>

All selectors are overridable via the provider's config_json so the same driver
adapts to other WHMCS themes without code changes.
"""
import re

from playwright.async_api import Page
from pydantic import Field

from app.models.product import StockState
from app.scrapers.base import (
    BaseDriver,
    BaseDriverConfig,
    DiscoveredProduct,
    InitialScan,
    StockSnapshot,
)


class StaticHTMLConfig(BaseDriverConfig):
    product_container_selector: str = ".package, .product-package, .product-card"
    product_name_selector: str = ".package-title, .product-title, h2, h3"
    stock_text_selector: str = ".package-stock, .stock, .availability"
    # Regex with one capture group for the count.
    stock_pattern: str = r"(\d+)\s*Available"
    out_of_stock_text: str = "Out of Stock"
    # If non-empty, check_stock only reports these keys (the rest are skipped).
    monitored_keys: list[str] = Field(default_factory=list)
    nav_timeout_ms: int = 15000


class StaticHTMLDriver(BaseDriver):
    name = "static_html"
    config_model = StaticHTMLConfig

    async def discover(self, page: Page) -> InitialScan:
        await page.wait_for_selector(
            self.config.product_container_selector,
            timeout=self.config.nav_timeout_ms,
        )
        products = await self._extract_products(page)
        notes: list[str] = []
        if not products:
            notes.append(
                f"No products matched '{self.config.product_container_selector}'."
            )
        return InitialScan(products=products, notes=notes)

    async def check_stock(self, page: Page) -> StockSnapshot:
        products = await self._extract_products(page)
        if self.config.monitored_keys:
            monitored = set(self.config.monitored_keys)
            products = [p for p in products if p.key in monitored]
        return StockSnapshot(products=products)

    async def _extract_products(self, page: Page) -> list[DiscoveredProduct]:
        containers = await page.query_selector_all(self.config.product_container_selector)
        out: list[DiscoveredProduct] = []
        for container in containers:
            name_el = await container.query_selector(self.config.product_name_selector)
            if not name_el:
                continue
            name = (await name_el.inner_text()).strip()
            if not name:
                continue

            stock_text = ""
            stock_el = await container.query_selector(self.config.stock_text_selector)
            if stock_el:
                stock_text = (await stock_el.inner_text()).strip()

            state, count = self._parse_stock_text(stock_text)
            out.append(
                DiscoveredProduct(
                    key=name,
                    display_name=name,
                    current_state=state,
                    current_count=count,
                )
            )
        return out

    def _parse_stock_text(self, text: str) -> tuple[StockState, int | None]:
        if not text:
            return StockState.UNKNOWN, None
        if self.config.out_of_stock_text.lower() in text.lower():
            return StockState.OUT_OF_STOCK, 0
        match = re.search(self.config.stock_pattern, text, re.IGNORECASE)
        if match:
            count = int(match.group(1))
            return (
                StockState.IN_STOCK if count > 0 else StockState.OUT_OF_STOCK,
                count,
            )
        return StockState.UNKNOWN, None
