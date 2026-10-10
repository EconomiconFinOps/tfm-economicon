from datetime import date, datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_active_tenant, get_database
from app.schemas.billing import AmbiguousCostSource, BillingGrouping, BillingSummary
from app.schemas.budget import BudgetDefinition, BudgetEvaluation
from app.services.budget import evaluate_budget
from app.schemas.recommendations import RecommendationReport
from app.services.recommendations import generate_recommendations


router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/recommendations", response_model=RecommendationReport)
def get_billing_recommendations(
    start_date: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> RecommendationReport:
    """Generate evidence-backed proposals; never apply changes or calculate savings."""
    try:
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        if not 0 < (end - start).days <= 366:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid recommendation period") from None
    try:
        result = database.fetch_billing_summary(
            tenant_id, start_date=start, end_date=end, group_by="project", tag_key=None,
        )
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    return generate_recommendations(BillingSummary(**result), tenant_id=tenant_id)


@router.post("/budget/evaluate", response_model=BudgetEvaluation)
def evaluate_billing_budget(
    budget: BudgetDefinition,
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> BudgetEvaluation:
    try:
        result = database.fetch_billing_summary(
            tenant_id, start_date=budget.start_date, end_date=budget.end_date,
            group_by="subscription", tag_key=None,
        )
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    return evaluate_budget(budget, BillingSummary(**result))


def _canonical_tag_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")
    aliases = {
        "costcenter": "cost_center",
        "cost_centre": "cost_center",
        "env": "environment",
        "org": "organization",
    }
    return aliases.get(normalized, normalized)


@router.get("/summary", response_model=BillingSummary)
def get_billing_summary(
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
    start_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    group_by: BillingGrouping = "subscription",
    tag_key: str | None = None,
) -> BillingSummary:
    try:
        if start_date is None and end_date is None:
            start = datetime.now(timezone.utc).date().replace(day=1)
            end = (start.replace(year=start.year + 1, month=1) if start.month == 12
                   else start.replace(month=start.month + 1))
        elif start_date is not None and end_date is not None:
            start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        else:
            raise ValueError()
        if start >= end:
            raise ValueError()
        if group_by == "tag":
            if tag_key is None or any(ord(char) < 32 or ord(char) == 127 for char in tag_key):
                raise ValueError()
            tag_key = _canonical_tag_key(tag_key)
            if not tag_key:
                raise ValueError()
        elif tag_key is not None:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid billing selection") from None

    try:
        result = database.fetch_billing_summary(
            tenant_id, start_date=start, end_date=end, group_by=group_by, tag_key=tag_key,
        )
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    return BillingSummary(**result)
