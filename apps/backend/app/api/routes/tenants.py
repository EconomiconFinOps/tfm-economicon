from fastapi import APIRouter, Depends

from app.api.dependencies import get_database
from app.schemas.tenant import TenantCollection


router = APIRouter(tags=["tenants"])


@router.get("/tenants", response_model=TenantCollection)
def get_tenants(database=Depends(get_database)) -> TenantCollection:
    return TenantCollection(items=database.fetch_tenants())

