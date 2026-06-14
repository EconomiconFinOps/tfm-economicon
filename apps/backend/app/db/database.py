import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.security import hash_password
from app.db.migration_runner import MigrationRunner


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

USER_SEED = {
    "id": "user-finops-admin",
    "email": "operator@finops.local",
    "password": "secret",
    "full_name": "FinOps Operator",
    "role": "admin",
}


class Database:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def initialize(self) -> None:
        runner = MigrationRunner(
            self.engine,
            "app.db.migrations",
            Path(__file__).with_name("migrations"),
        )
        runner.run()
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        now = datetime.now(timezone.utc)
        password_hash = hash_password(USER_SEED["password"])

        with self.engine.begin() as connection:
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

            connection.execute(
                text(
                    """
                    UPSERT INTO users (id, email, password_hash, full_name, role, created_at)
                    VALUES (:id, :email, :password_hash, :full_name, :role, :created_at)
                    """
                ),
                {
                    "id": USER_SEED["id"],
                    "email": USER_SEED["email"],
                    "password_hash": password_hash,
                    "full_name": USER_SEED["full_name"],
                    "role": USER_SEED["role"],
                    "created_at": now,
                },
            )

            for tenant in TENANT_SEED:
                connection.execute(
                    text(
                        """
                        UPSERT INTO user_tenants (user_id, tenant_id, role, created_at)
                        VALUES (:user_id, :tenant_id, :role, :created_at)
                        """
                    ),
                    {
                        "user_id": USER_SEED["id"],
                        "tenant_id": tenant["id"],
                        "role": USER_SEED["role"],
                        "created_at": now,
                    },
                )

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def fetch_user_by_email(self, email: str) -> dict | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, email, password_hash, full_name, role
                    FROM users
                    WHERE email = :email
                    """
                ),
                {"email": email},
            ).mappings().first()
        return dict(row) if row else None

    def fetch_user_by_id(self, user_id: str) -> dict | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, email, full_name, role
                    FROM users
                    WHERE id = :user_id
                    """
                ),
                {"user_id": user_id},
            ).mappings().first()
        return dict(row) if row else None

    def fetch_tenants(self, user_id: str) -> list[dict]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT t.id, t.name, t.slug, t.plan
                    FROM tenants t
                    JOIN user_tenants ut ON ut.tenant_id = t.id
                    WHERE ut.user_id = :user_id
                    ORDER BY t.name
                    """
                ),
                {"user_id": user_id},
            )
            return [dict(row._mapping) for row in rows]

    def user_has_tenant(self, user_id: str, tenant_id: str) -> bool:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM user_tenants
                    WHERE user_id = :user_id AND tenant_id = :tenant_id
                    """
                ),
                {"user_id": user_id, "tenant_id": tenant_id},
            ).first()
        return row is not None

    def fetch_billing_summary(self, tenant_id: str) -> dict:
        with self.engine.connect() as connection:
            job_count = connection.execute(
                text("SELECT count(*) FROM jobs WHERE tenant_id = :tenant_id"),
                {"tenant_id": tenant_id},
            ).scalar_one()
        return {
            "monthly_spend": 184250,
            "savings_identified": 23500,
            "open_ingestions": int(job_count),
            "currency": "USD",
        }

    def create_job(self, payload: dict, created_by: str) -> dict:
        now = datetime.now(timezone.utc)
        job = {
            "id": str(uuid.uuid4()),
            "tenant_id": payload["tenant_id"],
            "created_by": created_by,
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
                        id, tenant_id, created_by, source, artifact_uri, payload, status, result, created_at, updated_at
                    ) VALUES (
                        :id, :tenant_id, :created_by, :source, :artifact_uri, :payload, :status, :result, :created_at, :updated_at
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

    def create_conversation(self, tenant_id: str, user_id: str, title: str) -> dict:
        now = datetime.now(timezone.utc)
        conversation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO conversations (id, tenant_id, user_id, title, created_at, updated_at)
                    VALUES (:id, :tenant_id, :user_id, :title, :created_at, :updated_at)
                    """
                ),
                conversation,
            )
        return conversation

    def fetch_conversations(self, tenant_id: str, user_id: str) -> list[dict]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, tenant_id, user_id, title, created_at, updated_at
                    FROM conversations
                    WHERE tenant_id = :tenant_id AND user_id = :user_id
                    ORDER BY updated_at DESC
                    """
                ),
                {"tenant_id": tenant_id, "user_id": user_id},
            )
            return [dict(row._mapping) for row in rows]

    def fetch_conversation(self, conversation_id: str, tenant_id: str, user_id: str) -> dict | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, tenant_id, user_id, title, created_at, updated_at
                    FROM conversations
                    WHERE id = :conversation_id AND tenant_id = :tenant_id AND user_id = :user_id
                    """
                ),
                {
                    "conversation_id": conversation_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                },
            ).mappings().first()
        return dict(row) if row else None

    def append_message(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        user_id: str | None,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        message = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "created_at": now,
        }
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO messages (id, conversation_id, tenant_id, user_id, role, content, metadata, created_at)
                    VALUES (:id, :conversation_id, :tenant_id, :user_id, :role, :content, :metadata, :created_at)
                    """
                ),
                message,
            )
            connection.execute(
                text(
                    """
                    UPDATE conversations
                    SET updated_at = :updated_at
                    WHERE id = :conversation_id
                    """
                ),
                {"updated_at": now, "conversation_id": conversation_id},
            )
        return {
            "id": message["id"],
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": now,
        }

    def fetch_messages(self, conversation_id: str) -> list[dict]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, role, content, metadata, created_at
                    FROM messages
                    WHERE conversation_id = :conversation_id
                    ORDER BY created_at ASC
                    """
                ),
                {"conversation_id": conversation_id},
            )
            return [
                {
                    "id": row.id,
                    "role": row.role,
                    "content": row.content,
                    "metadata": json.loads(row.metadata) if row.metadata else {},
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    def dispose(self) -> None:
        self.engine.dispose()
