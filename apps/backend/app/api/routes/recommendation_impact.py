from fastapi import APIRouter, Depends

from app.api.dependencies import get_active_tenant
from app.schemas.recommendation_impact import ImpactReport, ImpactRequest
from app.services.recommendation_impact import evaluate_recommendation_impact


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/impact/evaluate", response_model=ImpactReport)
def evaluate_impact(body: ImpactRequest, tenant_id: str = Depends(get_active_tenant)) -> ImpactReport:
    return evaluate_recommendation_impact(body, tenant_id)
