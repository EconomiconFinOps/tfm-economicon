from app.db.database import Database


class JobRepository:
    def __init__(self, database: Database):
        self.database = database

    def mark_running(self, job_id: str) -> None:
        self.database.update_job_status(job_id, "running")

    def mark_completed(self, job_id: str, result: dict) -> None:
        self.database.update_job_status(job_id, "completed", result=result)

    def mark_failed(self, job_id: str, error_message: str) -> None:
        self.database.update_job_status(job_id, "failed", result={"error": error_message})

