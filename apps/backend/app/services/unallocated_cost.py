"""Disjoint metadata-defect buckets, aggregated before rounding (JUP-028)."""
from decimal import Decimal, ROUND_HALF_UP, localcontext

from sqlalchemy import text

from app.core.tag_policy import POLICY_VERSION, REQUIRED_TAGS, tag_rule_sql
from app.schemas.billing import AmbiguousCostSource


def fetch_unallocated_cost(engine, tenant_id: str, *, start_date, end_date) -> dict:
    # A signature represents a set of defects, not one copy of cost per defect.
    # SQL fragments come only from the closed policy, never from the request.
    signature = " + ".join(
        f"CASE WHEN {tag_rule_sql(key)} THEN 0 ELSE {1 << index} END"
        for index, key in enumerate(REQUIRED_TAGS)
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
            SELECT *, ({signature}) AS signature FROM completed
            WHERE usage_date >= :start_date AND usage_date < :end_date
        ), conflicts AS (
            SELECT subscription_id, usage_date FROM period_records
            GROUP BY subscription_id, usage_date
            HAVING count(DISTINCT ingestion_id) > 1
        ), metadata AS (
            SELECT (SELECT count(*) FROM completed WHERE usage_date IS NULL) AS undated,
                   (SELECT count(*) FROM conflicts) AS ambiguous
        ), aggregates AS (
            SELECT currency, signature, count(*) AS record_count,
                   sum(CASE WHEN pretax_cost > 0 THEN pretax_cost ELSE 0 END) AS positive,
                   sum(CASE WHEN pretax_cost < 0 THEN pretax_cost ELSE 0 END) AS negative
            FROM period_records WHERE NOT EXISTS (SELECT 1 FROM conflicts)
            GROUP BY currency, signature
        )
        SELECT a.*, m.undated, m.ambiguous
        FROM metadata m LEFT JOIN aggregates a ON TRUE
        ORDER BY a.currency ASC NULLS LAST, a.signature
    """)
    with engine.connect().execution_options(isolation_level="SERIALIZABLE") as connection:
        with connection.begin():
            rows = connection.execute(query, {
                "tenant_id": tenant_id, "start_date": start_date, "end_date": end_date,
            }).mappings().all()
    if rows[0]["ambiguous"]:
        raise AmbiguousCostSource()
    currencies = {}
    for row in rows:
        if row["currency"] is not None:
            currencies.setdefault(row["currency"], []).append(row)
    # At most 32 signatures per currency; raw billing rows never leave SQL.
    results = [_currency(currency, buckets) for currency, buckets in currencies.items()]
    undated = int(rows[0]["undated"])
    return {
        "contract_version": 1, "policy_version": POLICY_VERSION,
        "detection_basis": "observed_required_tags", "allocation_status": "not_evaluated",
        "required_tags": list(REQUIRED_TAGS),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "timezone": "UTC"},
        "data_status": "partial" if undated else ("available" if results else "empty"),
        "excluded_undated_count": undated, "currencies": results,
    }


def _currency(currency: str, rows) -> dict:
    with localcontext() as context:
        context.prec = max(80, *(len(row[key].as_tuple().digits) + 20
                                for row in rows for key in ("positive", "negative")))

        def display(value):
            rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return "0.00" if rounded == 0 else format(rounded, ".2f")

        zero = Decimal(0)
        positive = sum((row["positive"] for row in rows), zero)
        negative = sum((row["negative"] for row in rows), zero)
        allocated = sum((row["positive"] for row in rows if row["signature"] == 0), zero)
        allocated_negative = sum((row["negative"] for row in rows if row["signature"] == 0), zero)
        unallocated, unallocated_negative = positive - allocated, negative - allocated_negative
        # Match JUP-017's displayed complement, retaining exact weights until here.
        allocated_percent = ((100 * allocated / positive).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                             if positive > 0 else None)
        groups = []
        for row in rows:
            mask = int(row["signature"])
            if mask == 0:
                continue
            missing = [key for index, key in enumerate(REQUIRED_TAGS) if mask & (1 << index)]
            has_owner_defect = "owner" in missing
            reason = ("no_owner_and_unclassified" if has_owner_defect and len(missing) > 1
                      else "no_owner" if has_owner_defect else "unclassified")
            groups.append({
                "missing_or_invalid_tags": missing, "reason": reason,
                "record_count": int(row["record_count"]),
                "positive_cost": display(row["positive"]),
                "negative_adjustments": display(row["negative"]),
                "net_cost": display(row["positive"] + row["negative"]),
            })
        return {
            "currency": currency, "record_count": sum(int(row["record_count"]) for row in rows),
            "candidate_record_count": sum(group["record_count"] for group in groups),
            "positive_cost": display(positive), "complete_metadata_cost": display(allocated),
            "candidate_cost": display(unallocated), "negative_adjustments": display(negative),
            "complete_metadata_negative_adjustments": display(allocated_negative),
            "candidate_negative_adjustments": display(unallocated_negative),
            "net_cost": display(positive + negative),
            "complete_metadata_net_cost": display(allocated + allocated_negative),
            "candidate_net_cost": display(unallocated + unallocated_negative),
            "candidate_percent": display(100 - allocated_percent) if allocated_percent is not None else None,
            "no_positive_cost_reason": (None if positive > 0 else
                ("negative_adjustments_only" if negative < 0 else "zero_cost_only")),
            "groups": groups,
        }
