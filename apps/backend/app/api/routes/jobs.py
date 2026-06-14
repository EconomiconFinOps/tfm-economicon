from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_active_tenant, get_current_user, get_database, get_queue
from app.schemas.jobs import IngestJobRequest, IngestJobResponse


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/ingest", response_model=IngestJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_ingest_job(
    payload: IngestJobRequest,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
    queue=Depends(get_queue),
) -> IngestJobResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload tenant_id must match X-Tenant-Id.",
        )

    job = database.create_job(payload.model_dump(), created_by=current_user["id"])
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
