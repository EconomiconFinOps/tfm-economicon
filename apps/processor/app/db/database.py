import json
from datetime import datetime, timezone

from sqlalchemy import create_engine, text


class Database:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def initialize(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS jobs (
                        id STRING PRIMARY KEY,
                        tenant_id STRING NOT NULL,
                        source STRING NOT NULL,
                        artifact_uri STRING,
                        payload JSONB NOT NULL,
                        status STRING NOT NULL,
                        result JSONB,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
            )

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def update_job_status(self, job_id: str, status: str, result: dict | None = None) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = :status,
                        result = :result,
                        updated_at = :updated_at
                    WHERE id = :job_id
                    """
                ),
                {
                    "job_id": job_id,
                    "status": status,
                    "result": json.dumps(result) if result is not None else None,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

    def fetch_job_counts(self) -> dict[str, int]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT status, count(*) AS total
                    FROM jobs
                    GROUP BY status
                    """
                )
            )
            data = {row.status: int(row.total) for row in rows}
        return {
            "queued": data.get("queued", 0),
            "running": data.get("running", 0),
            "failed": data.get("failed", 0),
            "completed": data.get("completed", 0),
        }

    def dispose(self) -> None:
        self.engine.dispose()

