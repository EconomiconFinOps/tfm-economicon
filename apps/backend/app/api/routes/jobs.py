import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse

from app.api.dependencies import get_active_tenant, get_current_user, get_database, get_queue
from app.core.metrics import ingest_jobs_total
from app.schemas.jobs import IngestJobRequest, IngestJobResponse


router = APIRouter(prefix="/jobs", tags=["jobs"])


def _publication_error(code: str, job_id: str | None, outcome: str | None = None) -> JSONResponse:
    body = {
        "detail": "Unable to publish the job into RabbitMQ.",
        "code": code, "job_id": job_id, "retryable": False,
    }
    if outcome is not None:
        body["publication_outcome"] = outcome
    return JSONResponse(body, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@router.post("/ingest", response_model=IngestJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_ingest_job(
    payload: IngestJobRequest,
    current_user=Depends(get_current_user),
    tenant_id: str = Depends(get_active_tenant),
    database=Depends(get_database),
    queue=Depends(get_queue),
) -> IngestJobResponse | JSONResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload tenant_id must match X-Tenant-Id.",
        )

    reservation = queue.reserve()
    if getattr(reservation, "outcome", None) == "not_sent":
        return _publication_error("publish_not_sent", None)
    try:
        job = database.create_job(payload.model_dump(), created_by=current_user["id"])
        request_id = structlog.contextvars.get_contextvars().get("request_id")
        if request_id is not None:
            job["request_id"] = request_id
        published = queue.publish(job, reservation=reservation)
        outcome = published.outcome
        # Only fixed contract values may enter the response or persisted diagnostic.
        if outcome not in {"confirmed", "not_sent", "rejected", "unknown"}:
            raise RuntimeError("Invalid publication outcome.")
        try:
            database.finalize_job_publication(
                job["id"], tenant_id=tenant_id, created_by=current_user["id"],
                outcome=outcome, code=published.code,
            )
        except Exception:
            return _publication_error("publication_state_unavailable", job["id"], outcome)
        if outcome != "confirmed":
            return _publication_error("publish_" + outcome, job["id"])
    finally:
        queue.cancel(reservation)

    ingest_jobs_total.inc()

    return IngestJobResponse(
        job_id=job["id"],
        status="queued",
        queue=queue.queue_name,
    )
