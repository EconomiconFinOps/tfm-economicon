import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.runtime_secrets import DemoRotationRequired
from app.core.security import hash_password, verify_password
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
    "email": "operator@example.com",
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
        settings = get_settings()
        now = datetime.now(timezone.utc)

        with self.engine.begin() as connection:
            existing = connection.execute(
                text("SELECT id, email, password_hash FROM users WHERE id = :id OR email = :email"),
                {"id": USER_SEED["id"], "email": USER_SEED["email"]},
            ).mappings().all()
            if settings.runtime_environment != "test" and any(
                verify_password("secret", user["password_hash"]) for user in existing
            ):
                raise DemoRotationRequired()
            if not settings.demo_seed_enabled:
                return
            # Never attach demo associations to a different existing identity.
            if any(user["id"] != USER_SEED["id"] or user["email"] != USER_SEED["email"] for user in existing):
                return
            for tenant in TENANT_SEED:
                connection.execute(
                    text(
                        """
                        INSERT INTO tenants (id, name, slug, plan)
                        VALUES (:id, :name, :slug, :plan)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    tenant,
                )

            connection.execute(
                text(
                    """
                    INSERT INTO users (id, email, password_hash, full_name, role, created_at)
                    VALUES (:id, :email, :password_hash, :full_name, :role, :created_at)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "id": USER_SEED["id"],
                    "email": USER_SEED["email"],
                    "password_hash": hash_password(settings.demo_password.get_secret_value()) if not existing else existing[0]["password_hash"],
                    "full_name": USER_SEED["full_name"],
                    "role": USER_SEED["role"],
                    "created_at": now,
                },
            )

            for tenant in TENANT_SEED:
                connection.execute(
                    text(
                        """
                        INSERT INTO user_tenants (user_id, tenant_id, role, created_at)
                        VALUES (:user_id, :tenant_id, :role, :created_at)
                        ON CONFLICT DO NOTHING
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
            "status": "publish_pending",
            "result": json.dumps({"publication": {"outcome": "pending", "code": "awaiting_publisher"}}),
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
            "created_by": job["created_by"],
            "source": job["source"],
            "artifact_uri": job["artifact_uri"],
            "status": "queued",
            "payload": payload,
        }

    def finalize_job_publication(
        self, job_id: str, *, tenant_id: str, created_by: str, outcome: str, code: str
    ) -> None:
        targets = {
            "confirmed": "queued", "not_sent": "publish_failed",
            "rejected": "publish_failed", "unknown": "publish_unknown",
        }
        codes = {
            "confirmed": {"confirmed"},
            "not_sent": {"capacity", "stopping", "owner_unavailable", "deadline_before_send",
                         "connect_failed", "serialization_failed"},
            "rejected": {"broker_nack", "unroutable"},
            "unknown": {"confirm_timeout", "connection_lost", "shutdown_in_flight", "cancelled_in_flight"},
        }
        try:
            if outcome not in codes or code not in codes[outcome]:
                raise ValueError()
            scope = {"id": job_id, "tenant_id": tenant_id, "created_by": created_by}
            with self.engine.begin() as connection:
                updated = connection.execute(
                    text("""
                        UPDATE jobs SET status = :status, result = :result, updated_at = :updated_at
                        WHERE id = :id AND tenant_id = :tenant_id AND created_by = :created_by
                          AND status = 'publish_pending'
                    """),
                    {**scope, "status": targets[outcome],
                     "result": json.dumps({"publication": {"outcome": outcome, "code": code}}),
                     "updated_at": datetime.now(timezone.utc)},
                )
                if updated.rowcount == 1:
                    return
                if updated.rowcount != 0:
                    raise RuntimeError()
                row = connection.execute(
                    text("""
                        SELECT status, result FROM jobs
                        WHERE id = :id AND tenant_id = :tenant_id AND created_by = :created_by
                    """), scope,
                ).mappings().first()
                if row is None:
                    raise LookupError()
                if row["status"] in {"running", "completed", "failed"}:
                    return
                result = json.loads(row["result"]) if isinstance(row["result"], str) else row["result"]
                publication = result.get("publication") if isinstance(result, dict) else None
                if isinstance(publication, dict):
                    previous = publication.get("outcome")
                    if (previous in codes and publication.get("code") in codes[previous]
                            and row["status"] == targets[previous]):
                        return
                raise RuntimeError()
        except Exception:
            raise RuntimeError("Job publication state unavailable.") from None

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
        requester_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        if not requester_id or (user_id is not None and user_id != requester_id):
            raise PermissionError("Conversation not found.")
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
            inserted = connection.execute(
                text(
                    """
                    INSERT INTO messages (id, conversation_id, tenant_id, user_id, role, content, metadata, created_at)
                    SELECT :id, :conversation_id, :tenant_id, :user_id, :role, :content, :metadata, :created_at
                    FROM conversations
                    WHERE id = :conversation_id AND tenant_id = :tenant_id
                      AND user_id = :requester_id
                    """
                ),
                {**message, "requester_id": requester_id},
            )
            if inserted.rowcount != 1:
                raise PermissionError("Conversation not found.")
            updated = connection.execute(
                text(
                    """
                    UPDATE conversations
                    SET updated_at = :updated_at
                    WHERE id = :conversation_id AND tenant_id = :tenant_id
                      AND user_id = :requester_id
                    """
                ),
                {"updated_at": now, "conversation_id": conversation_id,
                 "tenant_id": tenant_id, "requester_id": requester_id},
            )
            if updated.rowcount != 1:
                raise PermissionError("Conversation not found.")
        return {
            "id": message["id"],
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": now,
        }

    def fetch_messages(self, conversation_id: str, tenant_id: str, user_id: str) -> list[dict]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT m.id, m.role, m.content, m.metadata, m.created_at
                    FROM messages m
                    JOIN conversations c ON c.id = m.conversation_id AND c.tenant_id = m.tenant_id
                    WHERE c.id = :conversation_id AND c.tenant_id = :tenant_id
                      AND c.user_id = :user_id AND m.tenant_id = :tenant_id
                    ORDER BY m.created_at ASC
                    """
                ),
                {"conversation_id": conversation_id, "tenant_id": tenant_id, "user_id": user_id},
            )
            return [
                {
                    "id": row.id,
                    "role": row.role,
                    "content": row.content,
                    "metadata": (json.loads(row.metadata) if isinstance(row.metadata, str)
                                 else row.metadata) or {},
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    def dispose(self) -> None:
        self.engine.dispose()
