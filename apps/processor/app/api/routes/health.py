from fastapi import APIRouter, Depends

from app.api.dependencies import get_database, get_queue


router = APIRouter(tags=["health"])


@router.get("/health")
def health(database=Depends(get_database), queue=Depends(get_queue)) -> dict:
    return {
        "status": "ok" if database.ping() and queue.ping() else "degraded",
        "services": {
            "database": "ok" if database.ping() else "failed",
            "rabbitmq": "ok" if queue.ping() else "failed",
        },
        "jobs": database.fetch_job_counts(),
    }
