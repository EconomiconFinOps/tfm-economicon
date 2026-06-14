import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text


TENANT_SEED = [
    {
        "id": "tenant-core",
        "name": "Core Finance",
        "slug": "core-finance",
        "plan": "enterprise",
    },
    {
        "id": "tenant-growth",
        "name": "Growth Ops",
        "slug": "growth-ops",
        "plan": "growth",
    },
]


class Database:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def initialize(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS tenants (
                        id STRING PRIMARY KEY,
                        name STRING NOT NULL,
                        slug STRING UNIQUE NOT NULL,
                        plan STRING NOT NULL
                    )
                    """
                )
            )
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
            for tenant in TENANT_SEED:
                connection.execute(
                    text(
                        """
                        UPSERT INTO tenants (id, name, slug, plan)
                        VALUES (:id, :name, :slug, :plan)
                        """
                    ),
                    tenant,
                )

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def fetch_tenants(self) -> list[dict]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text("SELECT id, name, slug, plan FROM tenants ORDER BY name")
            )
            return [dict(row._mapping) for row in rows]

    def fetch_billing_summary(self) -> dict:
        with self.engine.connect() as connection:
            job_count = connection.execute(text("SELECT count(*) FROM jobs")).scalar_one()
        return {
            "monthly_spend": 184250,
            "savings_identified": 23500,
            "open_ingestions": int(job_count),
            "currency": "USD",
        }

    def create_job(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        job = {
            "id": str(uuid.uuid4()),
            "tenant_id": payload["tenant_id"],
            "source": payload["source"],
            "artifact_uri": payload.get("artifact_uri"),
            "payload": json.dumps(payload),
            "status": "queued",
            "result": None,
            "created_at": now,
            "updated_at": now,
        }
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO jobs (
                        id, tenant_id, source, artifact_uri, payload, status, result, created_at, updated_at
                    ) VALUES (
                        :id, :tenant_id, :source, :artifact_uri, :payload, :status, :result, :created_at, :updated_at
                    )
                    """
                ),
                job,
            )
        return {
            "id": job["id"],
            "tenant_id": job["tenant_id"],
            "source": job["source"],
            "artifact_uri": job["artifact_uri"],
            "status": job["status"],
            "payload": payload,
        }

    def dispose(self) -> None:
        self.engine.dispose()

