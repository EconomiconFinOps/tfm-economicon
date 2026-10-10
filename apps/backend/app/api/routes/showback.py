"""Read-only showback by one organizational dimension."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_active_tenant, get_database
from app.schemas.billing import AmbiguousCostSource
from app.schemas.showback import ShowbackDimension, ShowbackReport
from app.services.showback import build_showback
from app.services.showback_repository import fetch_showback


router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/showback", response_model=ShowbackReport)
def get_showback(
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
    start_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    dimension: ShowbackDimension = "owner",
) -> ShowbackReport:
    try:
        if start_date is None and end_date is None:
            start = datetime.now(timezone.utc).date().replace(day=1)
            end = (start.replace(year=start.year + 1, month=1)
                   if start.month == 12 else start.replace(month=start.month + 1))
        elif start_date is not None and end_date is not None:
            start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        else:
            raise ValueError()
        if start >= end:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid showback period") from None
    try:
        rows, undated = fetch_showback(
            database, tenant_id, start_date=start, end_date=end, dimension=dimension,
        )
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    return build_showback(
        rows, start_date=start, end_date=end, dimension=dimension,
        excluded_undated_count=undated,
    )
