"""Per-provider scan orchestration: load DB row, run driver, diff, log, notify.

Notification policy (no-spam):
    - State changes are logged to StockHistory unconditionally.
    - Telegram is dispatched ONLY on the OUT_OF_STOCK/UNKNOWN -> IN_STOCK
      transition, AND only for items the user has marked is_monitored=True.
    - New locations notify if is_monitored=True (default for new locations).
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.location import Location
from app.models.product import Product, StockState
from app.models.provider import Provider, ScanStatus
from app.models.stock_history import EventType, StockHistory
from app.notifications import get_notifier
from app.scrapers import get_driver_class
from app.scrapers.runner import run_check_stock


def _log_event(
    db: Session,
    *,
    provider_id: int,
    event_type: EventType,
    product_id: int | None = None,
    location_id: int | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        StockHistory(
            provider_id=provider_id,
            product_id=product_id,
            location_id=location_id,
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            details=details or {},
        )
    )


def _format_stock_message(
    provider: Provider, product: Product, count: int | None
) -> str:
    count_str = f" ({count} available)" if count else ""
    return (
        f"<b>{provider.name}</b>\n"
        f"{product.display_name} is now in stock{count_str}.\n"
        f'<a href="{provider.url}">Open page</a>'
    )


def _format_new_location_message(provider: Provider, location: Location) -> str:
    return (
        f"<b>{provider.name}</b>\n"
        f"New location detected: {location.display_name}\n"
        f'<a href="{provider.url}">Open page</a>'
    )


async def scan_provider(provider_id: int) -> None:
    db = SessionLocal()
    try:
        provider = db.get(Provider, provider_id)
        if provider is None or not provider.is_active:
            return

        driver_cls = get_driver_class(provider.driver_type)
        driver = driver_cls(provider.config_json)

        try:
            snapshot = await run_check_stock(provider, driver)
        except Exception as exc:
            provider.last_scan_at = datetime.utcnow()
            provider.last_scan_status = ScanStatus.ERROR
            provider.last_error = str(exc)[:500]
            _log_event(
                db,
                provider_id=provider.id,
                event_type=EventType.SCAN_ERROR,
                new_state="error",
                details={"error": str(exc)},
            )
            db.commit()
            return

        notifier = get_notifier()
        now = datetime.utcnow()

        # Map existing location keys to ids; update as we add new ones.
        loc_key_to_id: dict[str, int] = {loc.key: loc.id for loc in provider.locations}
        loc_key_to_obj: dict[str, Location] = {loc.key: loc for loc in provider.locations}

        # --- New-location detection ---
        for loc in snapshot.locations_seen:
            existing = loc_key_to_obj.get(loc.key)
            if existing is not None:
                existing.last_seen_at = now
                continue
            new_loc = Location(
                provider_id=provider.id,
                key=loc.key,
                display_name=loc.display_name,
                is_monitored=True,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(new_loc)
            db.flush()
            loc_key_to_id[new_loc.key] = new_loc.id
            loc_key_to_obj[new_loc.key] = new_loc
            _log_event(
                db,
                provider_id=provider.id,
                location_id=new_loc.id,
                event_type=EventType.NEW_LOCATION,
                new_state="visible",
                details={"display_name": loc.display_name},
            )
            if notifier is not None:
                try:
                    await notifier.send(_format_new_location_message(provider, new_loc))
                except Exception:
                    pass  # don't let a Telegram outage break the scan loop

        # --- Product state changes ---
        known_products = {p.key: p for p in provider.products}
        for prod in snapshot.products:
            existing = known_products.get(prod.key)
            if existing is None:
                # First time we see this product — record with current state, no notify
                # (user must opt-in via is_monitored before notifications kick in).
                new_prod = Product(
                    provider_id=provider.id,
                    location_id=loc_key_to_id.get(prod.location_key) if prod.location_key else None,
                    key=prod.key,
                    display_name=prod.display_name,
                    is_monitored=False,
                    last_state=prod.current_state,
                    last_count=prod.current_count,
                )
                db.add(new_prod)
                db.flush()
                _log_event(
                    db,
                    provider_id=provider.id,
                    product_id=new_prod.id,
                    event_type=EventType.STATE_CHANGE,
                    previous_state=None,
                    new_state=prod.current_state.value,
                    details={"initial": True},
                )
                continue

            if existing.last_state == prod.current_state:
                # No change — maybe update count if reported.
                existing.last_count = prod.current_count
                continue

            previous = existing.last_state
            should_notify = (
                existing.is_monitored
                and prod.current_state == StockState.IN_STOCK
                and previous in (StockState.OUT_OF_STOCK, StockState.UNKNOWN)
            )
            existing.last_state = prod.current_state
            existing.last_count = prod.current_count
            _log_event(
                db,
                provider_id=provider.id,
                product_id=existing.id,
                event_type=EventType.STATE_CHANGE,
                previous_state=previous.value if previous else None,
                new_state=prod.current_state.value,
                details={"count": prod.current_count},
            )
            if should_notify and notifier is not None:
                try:
                    await notifier.send(
                        _format_stock_message(provider, existing, prod.current_count)
                    )
                except Exception:
                    pass

        provider.last_scan_at = now
        provider.last_scan_status = ScanStatus.OK
        provider.last_error = None
        db.commit()
    finally:
        db.close()
