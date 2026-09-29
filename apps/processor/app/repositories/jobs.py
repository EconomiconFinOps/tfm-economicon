from app.core.metrics import ingest_jobs_failed_total
from app.db.database import Database


class JobRepository:
    def __init__(self, database: Database):
        self.database = database

    def fetch_authorized_job(self, job_id: str, *, tenant_id: str, created_by: str) -> dict | None:
        return self.database.fetch_authorized_job(job_id, tenant_id=tenant_id, created_by=created_by)

    def mark_running(self, job_id: str, *, tenant_id: str, created_by: str) -> None:
        self.database.update_job_status(job_id, "running", tenant_id=tenant_id, created_by=created_by)

    def mark_completed(self, job_id: str, result: dict, *, tenant_id: str, created_by: str) -> None:
        self.database.update_job_status(job_id, "completed", result=result, tenant_id=tenant_id, created_by=created_by)

    def mark_failed(self, job_id: str, error_message: str, *, tenant_id: str, created_by: str) -> None:
        self.database.update_job_status(job_id, "failed", result={"error": error_message}, tenant_id=tenant_id, created_by=created_by)
        ingest_jobs_failed_total.inc()
