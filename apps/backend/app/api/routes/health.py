from fastapi import APIRouter, Depends

from app.api.dependencies import get_database, get_queue
from app.schemas.health import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(database=Depends(get_database), queue=Depends(get_queue)) -> HealthResponse:
    database_status = "ok" if database.ping() else "failed"
    rabbitmq_status = "ok" if queue.ping() else "failed"
    status = "ok" if database_status == "ok" and rabbitmq_status == "ok" else "degraded"
    return HealthResponse(
        status=status,
        services={"database": database_status, "rabbitmq": rabbitmq_status},
    )
