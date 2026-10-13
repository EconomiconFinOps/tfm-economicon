from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import get_active_tenant, get_current_user, get_database
from app.schemas.anomaly_episodes import (
    AnomalyDetectionRun, AnomalyEpisode, AnomalyEpisodeList, EpisodeStatusChange,
)
from app.services.anomaly_episodes import (
    DetectionConflict, EpisodeConflict, EpisodeNotFound, StatusChangeConflict,
)
from app.schemas.billing import AmbiguousCostSource, BillingGrouping, BillingSummary, canonical_tag_key
from app.schemas.tag_coverage import TagCoverage
from app.schemas.budget import BudgetDefinition, BudgetEvaluation
from app.services.budget import evaluate_budget
from app.schemas.anomalies import AnomalyDefinition, AnomalyEvaluation
from app.services import reference_date
from app.services.anomalies import evaluate_anomalies


router = APIRouter(prefix="/billing", tags=["billing"])


def _billing_period(start_date: str | None, end_date: str | None) -> tuple[date, date]:
    if start_date is None and end_date is None:
        start = reference_date.today().replace(day=1)
        end = (start.replace(year=start.year + 1, month=1) if start.month == 12
               else start.replace(month=start.month + 1))
    elif start_date is not None and end_date is not None:
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    else:
        raise ValueError()
    if start >= end:
        raise ValueError()
    return start, end


@router.get("/tag-coverage", response_model=TagCoverage)
def get_tag_coverage(
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
    start_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
) -> TagCoverage:
    try:
        start, end = _billing_period(start_date, end_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid billing selection") from None
    try:
        result = database.fetch_tag_coverage(tenant_id, start_date=start, end_date=end)
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    return TagCoverage(**result)


@router.post("/anomalies/evaluate", response_model=AnomalyEvaluation)
def evaluate_billing_anomalies(
    definition: AnomalyDefinition,
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> AnomalyEvaluation:
    def read(start, end):
        return BillingSummary(**database.fetch_billing_summary(
            tenant_id, start_date=start, end_date=end, group_by=definition.group_by, tag_key=None,
        ))

    try:
        current = read(definition.start_date, definition.end_date)
        period = definition.baseline_period
        baseline = read(period.start_date, period.end_date) if period is not None else None
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    return evaluate_anomalies(definition, current, baseline, tenant_id=tenant_id)


async def _no_body(request: Request, tenant_id: str = Depends(get_active_tenant)) -> None:
    # Detection always uses the stored business rules; caller-supplied rules belong to /evaluate.
    if await request.body():
        raise HTTPException(status_code=422, detail="Detection does not accept a request body")


_EPISODE_NOT_FOUND = {"code": "anomaly_episode_not_found"}


@router.post("/anomalies/detect", response_model=AnomalyDetectionRun, dependencies=[Depends(_no_body)])
def detect_anomaly_episodes(
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> AnomalyDetectionRun:
    try:
        result = database.run_anomaly_detection(tenant_id, today=reference_date.today())
    except AmbiguousCostSource:
        raise HTTPException(status_code=409, detail={"code": "ambiguous_cost_source"}) from None
    except DetectionConflict:
        raise HTTPException(status_code=409, detail={"code": "detection_conflict"}) from None
    return AnomalyDetectionRun(**result)


@router.get("/anomalies/episodes", response_model=AnomalyEpisodeList)
def list_anomaly_episodes(
    scope: Literal["open", "all"] = "open",
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> AnomalyEpisodeList:
    return AnomalyEpisodeList(scope=scope, **database.fetch_anomaly_episode_list(tenant_id, scope=scope))


@router.get("/anomalies/episodes/{episode_id}", response_model=AnomalyEpisode)
def read_anomaly_episode(
    episode_id: str,
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> AnomalyEpisode:
    episode = database.fetch_anomaly_episode(tenant_id, episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail=_EPISODE_NOT_FOUND)
    return AnomalyEpisode(**episode)


@router.patch("/anomalies/episodes/{episode_id}", response_model=AnomalyEpisode)
def change_anomaly_episode_status(
    episode_id: str,
    change: EpisodeStatusChange,
    tenant_id: str = Depends(get_active_tenant),
    current_user: dict = Depends(get_current_user),
    database=Depends(get_database),
) -> AnomalyEpisode:
    try:
        episode = database.change_anomaly_episode_status(
            tenant_id, episode_id, status=change.status, reason=change.reason, actor=current_user["id"],
        )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=_EPISODE_NOT_FOUND) from None
    except EpisodeConflict:
        raise HTTPException(status_code=409, detail={"code": "invalid_status_transition"}) from None
    except StatusChangeConflict:
        raise HTTPException(status_code=409, detail={"code": "status_change_conflict"}) from None
    return AnomalyEpisode(**episode)


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
    return canonical_tag_key(value)


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
        start, end = _billing_period(start_date, end_date)
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
