"""Tenant-scoped monthly observations for JUP-031; no forecast or imputation."""
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.schemas.billing import AmbiguousCostSource


def fetch_forecast_history(
    database, tenant_id: str, *, start_date: date, end_date: date, group_by: str,
) -> dict:
    """Read one consistent aggregate of completed cost ingestions in [start, end).

    Undated rows are counted across this tenant because they cannot be assigned
    to a period. Missing dimensions remain explicit, and absent months are not
    fabricated as zero. The API owns the maximum allowed history length.
    """
    def present(expression: str) -> str:
        return f"CASE WHEN {expression} ~ '^\\s*$' THEN NULL ELSE {expression} END"

    project_tag = present("r.tags ->> 'project'")
    dimensions = {
        "subscription": present("r.subscription_id"),
        "service": present("r.service_name"),
        "project": f"COALESCE({present('r.project')}, {project_tag})",
    }
    if group_by not in dimensions or start_date >= end_date:
        raise ValueError("Invalid forecast history selection")
    # Only allowlisted expressions enter SQL. Tenant and period are parameters.
    query = text(f"""
        WITH completed AS (
            SELECT r.ingestion_id, r.subscription_id, r.usage_date,
                   r.currency, r.pretax_cost, {dimensions[group_by]} AS value
            FROM azure_cost_records r
            JOIN azure_cost_ingestion_runs i
              ON i.id = r.ingestion_id AND i.tenant_id = r.tenant_id
             AND i.subscription_id = r.subscription_id
            WHERE r.tenant_id = :tenant_id AND i.tenant_id = :tenant_id
              AND i.status = 'completed'
              AND (r.usage_date IS NULL OR
                   (r.usage_date >= :start_date AND r.usage_date < :end_date))
        ), period_records AS (
            SELECT * FROM completed WHERE usage_date IS NOT NULL
        ), conflicts AS (
            SELECT subscription_id, usage_date FROM period_records
            GROUP BY subscription_id, usage_date
            HAVING count(DISTINCT ingestion_id) > 1
        ), metadata AS (
            SELECT (SELECT count(*) FROM completed WHERE usage_date IS NULL) AS undated,
                   (SELECT count(*) FROM period_records WHERE value IS NULL) AS missing,
                   (SELECT count(*) FROM conflicts) AS ambiguous
        ), aggregates AS (
            SELECT CAST(date_trunc('month', usage_date) AS DATE) AS month,
                   value, currency, sum(pretax_cost) AS cost, count(*) AS record_count
            FROM period_records WHERE NOT EXISTS (SELECT 1 FROM conflicts)
            GROUP BY CAST(date_trunc('month', usage_date) AS DATE), value, currency
        )
        SELECT a.*, m.undated, m.missing, m.ambiguous
        FROM metadata m LEFT JOIN aggregates a ON TRUE
        ORDER BY a.month ASC NULLS LAST, a.value ASC NULLS LAST, a.currency ASC NULLS LAST
    """)
    with database.engine.connect().execution_options(isolation_level="SERIALIZABLE") as connection:
        with connection.begin():
            rows = connection.execute(query, {
                "tenant_id": tenant_id, "start_date": start_date, "end_date": end_date,
            }).mappings().all()
    metadata = rows[0]
    if metadata["ambiguous"]:
        raise AmbiguousCostSource()
    return {
        "rows": [
            {"month": row["month"], "value": row["value"], "currency": row["currency"],
             "cost": Decimal(row["cost"]), "record_count": int(row["record_count"])}
            for row in rows if row["month"] is not None
        ],
        "excluded_undated_count": int(metadata["undated"]),
        "missing_dimension_count": int(metadata["missing"]),
    }
