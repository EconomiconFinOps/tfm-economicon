from fastapi import APIRouter, Depends

from app.api.dependencies import get_active_tenant, get_database
from app.schemas.billing import BillingSummary


router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/summary", response_model=BillingSummary)
def get_billing_summary(
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
) -> BillingSummary:
    return BillingSummary(**database.fetch_billing_summary(tenant_id))
