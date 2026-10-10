from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_active_tenant, get_database
from app.db.forecast import fetch_forecast_history
from app.schemas.billing import AmbiguousCostSource
from app.schemas.forecast import BillingForecast, ForecastGrouping
from app.services.forecast import forecast_spend

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/forecast", response_model=BillingForecast)
def get_billing_forecast(
    start_date: date, end_date: date,
    group_by: ForecastGrouping = "subscription",
    horizon_months: int = Query(default=1, ge=1, le=3),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> BillingForecast:
    length = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
    if (start_date.day != 1 or end_date.day != 1 or not 1 <= length <= 24
            or end_date > datetime.now(timezone.utc).date().replace(day=1)):
        raise HTTPException(status_code=422, detail="Select 1-24 closed calendar months, with exclusive end_date")
    try:
        history = fetch_forecast_history(database, tenant_id, start_date=start_date,
                                         end_date=end_date, group_by=group_by)
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    return forecast_spend(history, start_date=start_date, end_date=end_date,
                          group_by=group_by, horizon_months=horizon_months)
