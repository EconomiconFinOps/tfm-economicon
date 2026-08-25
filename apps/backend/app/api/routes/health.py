from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.dependencies import get_database, get_queue, get_vector_store
from app.schemas.health import HealthResponse


UTC = timezone.utc
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    database=Depends(get_database),
    queue=Depends(get_queue),
    vector_store=Depends(get_vector_store),
) -> HealthResponse:
    database_status = "ok" if database.ping() else "failed"
    rabbitmq_status = "ok" if queue.ping() else "failed"
    vector_store_status = "ok" if vector_store.ping() else "failed"
    status = (
        "ok"
        if database_status == "ok" and rabbitmq_status == "ok" and vector_store_status == "ok"
        else "degraded"
    )
    return HealthResponse(
        status=status,
        services={
            "database": database_status,
            "rabbitmq": rabbitmq_status,
            "vector_store": vector_store_status,
        },
        checked_at=datetime.now(UTC),
    )
