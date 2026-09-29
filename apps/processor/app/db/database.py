import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.migration_runner import MigrationRunner


class Database:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def initialize(self) -> None:
        runner = MigrationRunner(
            self.engine,
            "app.db.migrations",
            Path(__file__).with_name("migrations"),
            version_table="processor_schema_migrations",
        )
        runner.run()

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def fetch_authorized_job(self, job_id: str, *, tenant_id: str, created_by: str) -> dict | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT j.id, j.tenant_id, j.created_by, j.source, j.artifact_uri,
                           j.payload, j.status, j.result
                    FROM jobs j
                    JOIN users u ON u.id = j.created_by
                    JOIN user_tenants ut ON ut.user_id = u.id AND ut.tenant_id = j.tenant_id
                    WHERE j.id = :job_id AND j.tenant_id = :tenant_id AND j.created_by = :created_by
                    """
                ),
                {"job_id": job_id, "tenant_id": tenant_id, "created_by": created_by},
            ).mappings().first()
        return dict(row) if row else None

    def update_job_status(
        self, job_id: str, status: str, result: dict | None = None,
        *, tenant_id: str, created_by: str,
    ) -> None:
        with self.engine.begin() as connection:
            updated = connection.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = :status,
                        result = :result,
                        updated_at = :updated_at
                    WHERE id = :job_id AND tenant_id = :tenant_id AND created_by = :created_by
                      AND status <> 'completed'
                    """
                ),
                {
                    "job_id": job_id,
                    "tenant_id": tenant_id,
                    "created_by": created_by,
                    "status": status,
                    "result": json.dumps(result) if result is not None else None,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            if updated.rowcount != 1:
                raise PermissionError("Job transition rejected.")

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
