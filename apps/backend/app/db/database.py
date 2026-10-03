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

    def fetch_billing_summary(
        self, tenant_id: str, *, start_date, end_date,
        group_by: str = "subscription", tag_key: str | None = None,
    ) -> dict:
        from decimal import Decimal, ROUND_HALF_UP, localcontext

        from app.schemas.billing import AmbiguousCostSource

        def present(expression: str) -> str:
            return f"CASE WHEN {expression} ~ '^\\s*$' THEN NULL ELSE {expression} END"

        project_tag = present("r.tags ->> 'project'")
        dimensions = {
            "subscription": present("r.subscription_id"),
            "resource_group": present("r.resource_group"),
            "service": present("r.service_name"),
            "project": f"COALESCE({present('r.project')}, {project_tag})",
            "tag": present("r.tags ->> :tag_key"),
        }
        dimension = dimensions[group_by]
        subscription = (present("r.subscription_id") if group_by in {"subscription", "resource_group"}
                        else "CAST(NULL AS STRING)")
        group_value = "lower(value)" if group_by == "resource_group" else "value"
        display_value = "min(value)" if group_by == "resource_group" else "value"
        # Only enum-selected expressions enter SQL; all request values are bound.
        query = text(f"""
            WITH completed AS (
                SELECT r.ingestion_id, r.subscription_id, r.usage_date,
                       r.currency, r.pretax_cost, {dimension} AS value,
                       {subscription} AS group_subscription
                FROM azure_cost_records r
                JOIN azure_cost_ingestion_runs i
                  ON i.id = r.ingestion_id AND i.tenant_id = r.tenant_id
                 AND i.subscription_id = r.subscription_id
                WHERE r.tenant_id = :tenant_id AND i.tenant_id = :tenant_id
                  AND i.status = 'completed'
            ), period_records AS (
                SELECT * FROM completed
                WHERE usage_date >= :start_date AND usage_date < :end_date
            ), conflicts AS (
                SELECT subscription_id, usage_date FROM period_records
                GROUP BY subscription_id, usage_date
                HAVING count(DISTINCT ingestion_id) > 1
            ), metadata AS (
                SELECT (SELECT count(*) FROM completed WHERE usage_date IS NULL) AS undated,
                       (SELECT count(*) FROM period_records WHERE value IS NULL) AS missing,
                       (SELECT count(*) FROM conflicts) AS ambiguous
            ), aggregates AS (
                SELECT 'total' AS kind, currency, CAST(NULL AS STRING) AS subscription_id,
                       CAST(NULL AS STRING) AS value, sum(pretax_cost) AS cost,
                       count(*) AS record_count
                FROM period_records WHERE NOT EXISTS (SELECT 1 FROM conflicts)
                GROUP BY currency
                UNION ALL
                SELECT 'group', currency, group_subscription, {display_value}, sum(pretax_cost), count(*)
                FROM period_records WHERE NOT EXISTS (SELECT 1 FROM conflicts)
                GROUP BY currency, group_subscription, {group_value}
            )
            SELECT a.*, m.undated, m.missing, m.ambiguous
            FROM metadata m LEFT JOIN aggregates a ON TRUE
            ORDER BY a.currency ASC NULLS LAST, a.subscription_id ASC NULLS LAST,
                     a.value ASC NULLS LAST, a.kind
        """)
        with self.engine.connect().execution_options(isolation_level="SERIALIZABLE") as connection:
            with connection.begin():
                rows = connection.execute(query, {
                    "tenant_id": tenant_id, "start_date": start_date, "end_date": end_date,
                    "tag_key": tag_key,
                }).mappings().all()
                job_count = connection.execute(
                    text("SELECT count(*) FROM jobs WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id},
                ).scalar_one()

        metadata = rows[0]
        if metadata["ambiguous"]:
            raise AmbiguousCostSource()

        def money(value: Decimal) -> str:
            with localcontext() as context:
                context.prec = max(50, len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 2)
                rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                return "0.00" if rounded == 0 else format(rounded, ".2f")

        totals, groups = [], []
        for row in rows:
            if row["kind"] is None:
                continue
            item = {"currency": row["currency"], "cost": money(row["cost"]),
                    "record_count": int(row["record_count"])}
            if row["kind"] == "total":
                totals.append(item)
            else:
                groups.append({**item, "subscription_id": row["subscription_id"], "value": row["value"]})
        missing, undated = int(metadata["missing"]), int(metadata["undated"])
        return {
            "contract_version": 2,
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "timezone": "UTC"},
            "group_by": group_by, "tag_key": tag_key,
            "data_status": "partial" if missing or undated else ("available" if totals else "empty"),
            "totals": totals, "groups": groups,
            "missing_dimension_count": missing, "excluded_undated_count": undated,
            "monthly_spend": totals[0]["cost"] if len(totals) == 1 else None,
            "currency": totals[0]["currency"] if len(totals) == 1 else None,
            "savings_identified": None, "open_ingestions": int(job_count),
        }

    def fetch_tag_coverage(self, tenant_id: str, *, start_date, end_date) -> dict:
        from decimal import Decimal, ROUND_HALF_UP, localcontext

        from app.core.tag_policy import POLICY_VERSION, REQUIRED_TAGS, tag_rule_sql
        from app.schemas.billing import AmbiguousCostSource

        rules = {key: tag_rule_sql(key) for key in REQUIRED_TAGS}
        compliant = " AND ".join(f"({rule})" for rule in rules.values())
        defects = ", ".join(
            f"sum(CASE WHEN NOT ({rule}) THEN 1 ELSE 0 END) AS invalid_{key}"
            for key, rule in rules.items()
        )
        query = text(f"""
            WITH completed AS (
                SELECT r.ingestion_id, r.subscription_id, r.usage_date,
                       r.currency, r.pretax_cost, r.tags
                FROM azure_cost_records r
                JOIN azure_cost_ingestion_runs i
                  ON i.id = r.ingestion_id AND i.tenant_id = r.tenant_id
                 AND i.subscription_id = r.subscription_id
                WHERE r.tenant_id = :tenant_id AND i.tenant_id = :tenant_id
                  AND i.status = 'completed'
            ), period_records AS (
                SELECT *, ({compliant}) AS compliant FROM completed
                WHERE usage_date >= :start_date AND usage_date < :end_date
            ), conflicts AS (
                SELECT subscription_id, usage_date FROM period_records
                GROUP BY subscription_id, usage_date
                HAVING count(DISTINCT ingestion_id) > 1
            ), metadata AS (
                SELECT (SELECT count(*) FROM completed WHERE usage_date IS NULL) AS undated,
                       (SELECT count(*) FROM conflicts) AS ambiguous
            ), aggregates AS (
                SELECT currency, count(*) AS record_count,
                       sum(CASE WHEN compliant THEN 1 ELSE 0 END) AS compliant_count,
                       sum(CASE WHEN pretax_cost > 0 THEN pretax_cost ELSE 0 END) AS positive,
                       sum(CASE WHEN pretax_cost > 0 AND compliant THEN pretax_cost ELSE 0 END) AS compliant_positive,
                       sum(CASE WHEN pretax_cost < 0 THEN pretax_cost ELSE 0 END) AS negative,
                       sum(CASE WHEN pretax_cost < 0 AND compliant THEN pretax_cost ELSE 0 END) AS compliant_negative,
                       {defects}
                FROM period_records WHERE NOT EXISTS (SELECT 1 FROM conflicts)
                GROUP BY currency
            )
            SELECT a.*, m.undated, m.ambiguous
            FROM metadata m LEFT JOIN aggregates a ON TRUE
            ORDER BY a.currency ASC NULLS LAST
        """)
        with self.engine.connect().execution_options(isolation_level="SERIALIZABLE") as connection:
            with connection.begin():
                rows = connection.execute(query, {
                    "tenant_id": tenant_id, "start_date": start_date, "end_date": end_date,
                }).mappings().all()
        if rows[0]["ambiguous"]:
            raise AmbiguousCostSource()
        currencies = []
        for row in rows:
            if row["currency"] is None:
                continue
            # Retain SQL aggregate precision, including tiny costs and amounts > 2**53.
            with localcontext() as context:
                context.prec = max(80, *(len(row[key].as_tuple().digits) + 20
                                        for key in ("positive", "compliant_positive", "negative", "compliant_negative")))
                def display(value):
                    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    return "0.00" if rounded == 0 else format(rounded, ".2f")
                p, t = row["positive"], row["compliant_positive"]
                c, ct = row["negative"], row["compliant_negative"]
                u, cu = p - t, c - ct
                percent = ((100 * t / p).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                           if p > 0 else None)
                currencies.append({
                    "currency": row["currency"], "record_count": int(row["record_count"]),
                    "compliant_record_count": int(row["compliant_count"]),
                    "noncompliant_record_count": int(row["record_count"] - row["compliant_count"]),
                    "positive_cost": display(p), "compliant_cost": display(t),
                    "noncompliant_cost": display(u), "negative_adjustments": display(c),
                    "compliant_negative_adjustments": display(ct),
                    "noncompliant_negative_adjustments": display(cu),
                    "net_cost": display(p + c), "compliant_net_cost": display(t + ct),
                    "noncompliant_net_cost": display(u + cu),
                    "compliant_percent": display(percent) if percent is not None else None,
                    "noncompliant_percent": display(Decimal(100) - percent) if percent is not None else None,
                    "no_positive_cost_reason": (None if p > 0 else
                        ("negative_adjustments_only" if c < 0 else "zero_cost_only")),
                    "missing_or_invalid_tag_counts": {key: int(row[f"invalid_{key}"]) for key in REQUIRED_TAGS},
                })
        undated = int(rows[0]["undated"])
        return {
            "contract_version": 1, "policy_version": POLICY_VERSION, "required_tags": list(REQUIRED_TAGS),
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "timezone": "UTC"},
            "data_status": "partial" if undated else ("available" if currencies else "empty"),
            "excluded_undated_count": undated, "currencies": currencies,
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
