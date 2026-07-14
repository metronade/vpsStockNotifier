from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.provider import Provider
from app.schemas.dashboard import DashboardProvider

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=list[DashboardProvider])
def get_dashboard(db: Session = Depends(get_db)) -> list[Provider]:
    # SQLAlchemy relationships populate the nested products/locations fields on
    # DashboardProvider via from_attributes — one query (plus lazy loads) is
    # enough to render the whole dashboard.
    return (
        db.query(Provider)
        .order_by(Provider.created_at.desc())
        .all()
    )
