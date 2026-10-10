"""Tenant-scoped exact aggregates over the normalized cost ledger (JUP-027)."""
from sqlalchemy import text

from app.schemas.billing import AmbiguousCostSource


def fetch_showback(database, tenant_id, *, start_date, end_date, dimension):
    # This allowlist is the only source of SQL expressions. Request values are bound.
    def tag(key):
        # Preserve type failures as invalid rather than accepting JSON numbers as IDs.
        return (f"CASE WHEN r.tags -> '{key}' IS NULL THEN NULL "
                f"WHEN jsonb_typeof(r.tags -> '{key}') = 'string' THEN r.tags ->> '{key}' "
                "ELSE 'unknown' END")

    expressions = {
        "owner": tag("owner"),
        "application": tag("application"),
        "cost_center": tag("cost_center"),
        "project": "COALESCE(CASE WHEN r.project ~ '^\\s*$' THEN NULL ELSE r.project END, "
                   + tag("project") + ")",
    }
    expression = expressions[dimension]
    query = text(f"""
        WITH completed AS (
            SELECT r.ingestion_id, r.subscription_id, r.usage_date,
                   r.currency, r.pretax_cost, {expression} AS value
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
                   (SELECT count(*) FROM conflicts) AS ambiguous
        ), aggregates AS (
            SELECT currency, value, sum(pretax_cost) AS cost, count(*) AS record_count
            FROM period_records WHERE NOT EXISTS (SELECT 1 FROM conflicts)
            GROUP BY currency, value
        )
        SELECT a.*, m.undated, m.ambiguous
        FROM metadata m LEFT JOIN aggregates a ON TRUE
        ORDER BY a.currency ASC NULLS LAST, a.value ASC NULLS LAST
    """)
    with database.engine.connect().execution_options(isolation_level="SERIALIZABLE") as connection:
        with connection.begin():
            rows = connection.execute(query, {
                "tenant_id": tenant_id, "start_date": start_date, "end_date": end_date,
            }).mappings().all()
    if rows[0]["ambiguous"]:
        raise AmbiguousCostSource()
    return (
        [dict(row) for row in rows if row["record_count"] is not None],
        int(rows[0]["undated"]),
    )
