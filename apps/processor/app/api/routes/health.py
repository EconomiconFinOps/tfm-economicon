from fastapi import APIRouter, Depends

from app.api.dependencies import get_database, get_queue, get_vector_store


router = APIRouter(tags=["health"])


@router.get("/health")
def health(database=Depends(get_database), queue=Depends(get_queue), vector_store=Depends(get_vector_store)) -> dict:
    database_status = "ok" if database.ping() else "failed"
    rabbitmq_status = "ok" if queue.ping() else "failed"
    vector_store_status = "ok" if vector_store.ping() else "failed"
    try:
        jobs = database.fetch_job_counts()
    except Exception:
        # jobs is backend-owned and is absent until the backend has migrated.
        jobs = None

    healthy = database_status == "ok" and rabbitmq_status == "ok" and vector_store_status == "ok"
    return {
        "status": "ok" if healthy and jobs is not None else "degraded",
        "services": {
            "database": database_status,
            "rabbitmq": rabbitmq_status,
            "vector_store": vector_store_status,
        },
        "jobs": jobs,
    }
