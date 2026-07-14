from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.location import Location
from app.models.product import Product
from app.models.provider import Provider, ScanStatus
from app.models.stock_history import EventType, StockHistory
from app.schemas.provider import (
    DiscoveredItem,
    InitialScanResponse,
    LocationRead,
    LocationUpdate,
    ProductRead,
    ProductUpdate,
    ProviderCreate,
    ProviderRead,
    ProviderUpdate,
)
from app.schemas.scan import ScanNowResponse, StockHistoryRead
from app.scheduler import schedule_provider, unschedule_provider
from app.scheduler.orchestrator import scan_provider
from app.scrapers import get_driver_class
from app.scrapers.runner import run_initial_scan

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=list[ProviderRead])
def list_providers(db: Session = Depends(get_db)) -> list[Provider]:
    return db.query(Provider).order_by(Provider.created_at.desc()).all()


@router.post("", response_model=InitialScanResponse, status_code=201)
async def create_provider(
    payload: ProviderCreate, db: Session = Depends(get_db)
) -> InitialScanResponse:
    provider = Provider(**payload.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)

    driver_cls = get_driver_class(provider.driver_type)
    driver = driver_cls(provider.config_json)
    try:
        scan = await run_initial_scan(provider, driver)
    except Exception as exc:
        provider.last_scan_status = ScanStatus.ERROR
        provider.last_error = str(exc)[:500]
        db.commit()
        db.refresh(provider)
        return InitialScanResponse(
            provider=ProviderRead.model_validate(provider),
            discovered_products=[],
            discovered_locations=[],
            notes=[f"Initial scan failed: {exc}"],
        )

    now = datetime.utcnow()
    for loc in scan.locations:
        db.add(
            Location(
                provider_id=provider.id,
                key=loc.key,
                display_name=loc.display_name,
                is_monitored=True,
                first_seen_at=now,
                last_seen_at=now,
            )
        )
    for prod in scan.products:
        db.add(
            Product(
                provider_id=provider.id,
                key=prod.key,
                display_name=prod.display_name,
                is_monitored=False,
                last_state=prod.current_state,
                last_count=prod.current_count,
            )
        )
    db.commit()
    db.refresh(provider)

    schedule_provider(provider)

    return InitialScanResponse(
        provider=ProviderRead.model_validate(provider),
        discovered_products=[
            DiscoveredItem(
                key=p.key,
                display_name=p.display_name,
                kind="product",
                current_state=p.current_state,
            )
            for p in scan.products
        ],
        discovered_locations=[
            DiscoveredItem(
                key=l.key,
                display_name=l.display_name,
                kind="location",
            )
            for l in scan.locations
        ],
        notes=scan.notes,
    )


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(provider_id: int, db: Session = Depends(get_db)) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.patch("/{provider_id}", response_model=ProviderRead)
def update_provider(
    provider_id: int,
    payload: ProviderUpdate,
    db: Session = Depends(get_db),
) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(provider, key, value)
    db.commit()
    db.refresh(provider)
    # Reschedule: interval or active flag may have changed
    schedule_provider(provider)
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(provider_id: int, db: Session = Depends(get_db)) -> None:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    unschedule_provider(provider_id)
    db.delete(provider)
    db.commit()


@router.get("/{provider_id}/products", response_model=list[ProductRead])
def list_products(provider_id: int, db: Session = Depends(get_db)) -> list[Product]:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider.products


@router.patch(
    "/{provider_id}/products/{product_id}", response_model=ProductRead
)
def update_product(
    provider_id: int,
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.provider_id != provider_id:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.is_monitored is not None:
        product.is_monitored = payload.is_monitored
    db.commit()
    db.refresh(product)
    return product


@router.get("/{provider_id}/locations", response_model=list[LocationRead])
def list_locations(
    provider_id: int, db: Session = Depends(get_db)
) -> list[Location]:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider.locations


@router.patch(
    "/{provider_id}/locations/{location_id}", response_model=LocationRead
)
def update_location(
    provider_id: int,
    location_id: int,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
) -> Location:
    location = db.get(Location, location_id)
    if location is None or location.provider_id != provider_id:
        raise HTTPException(status_code=404, detail="Location not found")
    if payload.is_monitored is not None:
        location.is_monitored = payload.is_monitored
    db.commit()
    db.refresh(location)
    return location


@router.post("/{provider_id}/scan", response_model=ScanNowResponse)
async def scan_now(
    provider_id: int, db: Session = Depends(get_db)
) -> ScanNowResponse:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    before_changes = (
        db.query(StockHistory)
        .filter(StockHistory.provider_id == provider_id)
        .count()
    )
    try:
        await scan_provider(provider_id)
    except Exception as exc:
        return ScanNowResponse(status="error", error=str(exc)[:500])
    db.expire_all()
    after_changes = (
        db.query(StockHistory)
        .filter(StockHistory.provider_id == provider_id)
        .count()
    )
    new_events = after_changes - before_changes
    return ScanNowResponse(
        status="ok",
        state_changes=new_events,
    )


@router.get(
    "/{provider_id}/history",
    response_model=list[StockHistoryRead],
)
def provider_history(
    provider_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[StockHistory]:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return (
        db.query(StockHistory)
        .filter(StockHistory.provider_id == provider_id)
        .order_by(StockHistory.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
