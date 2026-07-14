"""Playwright runner — owns the browser lifecycle and hands Pages to drivers.

One shared Chromium instance for the whole process; each scan gets its own
incognito-equivalent BrowserContext so cookies/cache don't leak between providers
or between scans.
"""
from playwright.async_api import (
    AsyncPlaywright,
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)

from app.config import settings
from app.models.provider import Provider
from app.scrapers.base import BaseDriver, InitialScan, StockSnapshot

_playwright: AsyncPlaywright | None = None
_browser: Browser | None = None

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


async def _ensure_browser() -> Browser:
    global _playwright, _browser
    if _browser is not None:
        return _browser
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=settings.playwright_headless,
        args=["--disable-blink-features=AutomationControlled"],
    )
    return _browser


async def _new_context() -> BrowserContext:
    browser = await _ensure_browser()
    return await browser.new_context(
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        user_agent=_UA,
    )


async def _open(page: Page, provider: Provider) -> None:
    await page.goto(
        provider.url,
        wait_until="domcontentloaded",
        timeout=settings.playwright_default_timeout_ms,
    )


async def run_initial_scan(provider: Provider, driver: BaseDriver) -> InitialScan:
    ctx = await _new_context()
    page = await ctx.new_page()
    try:
        await _open(page, provider)
        return await driver.discover(page)
    finally:
        await ctx.close()


async def run_check_stock(provider: Provider, driver: BaseDriver) -> StockSnapshot:
    ctx = await _new_context()
    page = await ctx.new_page()
    try:
        await _open(page, provider)
        return await driver.check_stock(page)
    finally:
        await ctx.close()


async def shutdown_browser() -> None:
    global _playwright, _browser
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
