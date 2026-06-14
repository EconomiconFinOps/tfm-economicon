from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_database, get_queue
from app.schemas.jobs import IngestJobRequest, IngestJobResponse


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/ingest", response_model=IngestJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_ingest_job(
    payload: IngestJobRequest,
    database=Depends(get_database),
    queue=Depends(get_queue),
) -> IngestJobResponse:
    job = database.create_job(payload.model_dump())
    published = queue.publish(job)

    if not published:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to publish the job into RabbitMQ.",
        )

    return IngestJobResponse(
        job_id=job["id"],
        status=job["status"],
        queue=queue.queue_name,
    )
