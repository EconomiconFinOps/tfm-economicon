#!/usr/bin/env python3
"""Synthetic Azure cost dataset for local validation: load, inspect and remove it.

The rows are synthetic, are not Azure invoices and do not come from the public dataset.
Run it inside the processor container so it uses that container's DATABASE_URL:

    docker compose exec -T processor python - apply < scripts/synthetic_costs.py
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Callable, Mapping, Sequence

PREFIX = "synthetic-jup106-"
DEFAULT_TENANT = "tenant-growth"
CREATED_AT = datetime(2026, 7, 31, tzinfo=timezone.utc)
SUBSCRIPTION_A = PREFIX + "sub-a"
SUBSCRIPTION_B = PREFIX + "sub-b"
RUN_A = PREFIX + "run-a"
RUN_B = PREFIX + "run-b"
TENANT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
LIKE_PATTERN = PREFIX + "%"
# A record is synthetic only when its own ingestion run is.
SYNTHETIC_RUNS = "(SELECT id FROM azure_cost_ingestion_runs WHERE id LIKE :pattern AND COALESCE(request->>'synthetic', 'false') = 'true')"

# (day, cost, resource group, service, project, tags); None day is the undated row.
EUR_ROWS = (
    (date(2026, 1, 15), "60.00", "Web", "Compute", "Alpha", {"cost_center": "finance", "environment": "prod"}),
    (date(2026, 1, 20), "40.00", "web", "Compute", "Alpha", {"cost_center": "finance"}),
    (date(2026, 2, 10), "0.00", "Data", "Storage", "Beta", {"cost_center": "ops"}),
    (date(2026, 4, 12), "30.00", "Data", "Storage", "Beta", {"cost_center": "ops"}),
    (date(2026, 4, 18), "10.00", None, None, None, {}),
    (date(2026, 5, 5), "-50.00", "Data", "Credits", "Beta", {"cost_center": "ops"}),
    (None, "7.77", "Web", "Compute", "Alpha", {"cost_center": "finance"}),
)
USD_ROWS = (
    (date(2026, 2, 14), "10.50", "Analytics", "Compute", "Alpha", {"cost_center": "finance"}),
    (date(2026, 6, 9), "25.25", "Analytics", "Storage", "Beta", {"cost_center": "ops"}),
    (date(2026, 7, 20), "9007199254740993.01", "Analytics", "Storage", "Beta", {"cost_center": "ops"}),
)


def validate_tenant(tenant: str) -> str:
    if not isinstance(tenant, str) or not TENANT_PATTERN.match(tenant):
        raise ValueError("El tenant debe ser un identificador en minúsculas, dígitos y guiones.")
    return tenant


def build_dataset(tenant: str) -> tuple[list[dict], list[dict]]:
    validate_tenant(tenant)
    plan = ((RUN_A, SUBSCRIPTION_A, "EUR", EUR_ROWS), (RUN_B, SUBSCRIPTION_B, "USD", USD_ROWS))
    runs: list[dict] = []
    records: list[dict] = []
    number = 0
    for run_id, subscription, currency, rows in plan:
        for day, cost, group, service, project, tags in rows:
            number += 1
            identifier = f"{PREFIX}rec-{number:02d}"
            records.append({
                "id": identifier, "ingestion_id": run_id, "tenant_id": tenant, "subscription_id": subscription,
                "usage_date": day, "pretax_cost": Decimal(cost), "currency": currency,
                "dimensions": {"synthetic": True}, "source_row_hash": identifier, "created_at": CREATED_AT,
                "resource_group": group, "service_name": service, "project": project, "tags": dict(tags),
            })
        runs.append({
            "id": run_id, "tenant_id": tenant, "subscription_id": subscription,
            "request": {"synthetic": True, "change": "jup-106-synthetic-cost-data"}, "status": "completed",
            "page_count": 1, "retry_count": 0, "row_count": len(rows),
            "started_at": CREATED_AT, "completed_at": CREATED_AT,
        })
    return runs, records


def status(store, tenant: str) -> dict:
    validate_tenant(tenant)
    runs, records = build_dataset(tenant)
    found = store.list_synthetic()
    real = store.count_real(tenant)
    expected_runs, expected_records = {r["id"] for r in runs}, {r["id"] for r in records}
    tenants = set(found["runs"].values()) | set(found["records"].values())
    if not found["runs"] and not found["records"]:
        state = "absent"
    elif tenants != {tenant}:
        state = "other-tenant"
    elif set(found["runs"]) == expected_runs and set(found["records"]) == expected_records:
        state = "present"
    else:
        state = "partial"
    return {
        "tenant": tenant, "state": state, "runs": len(found["runs"]), "records": len(found["records"]),
        "real_runs": real["runs"], "real_records": real["records"],
    }


def apply(store, tenant: str) -> dict:
    report = status(store, tenant)
    state = report["state"]
    if report["real_runs"] or report["real_records"]:
        return {"outcome": "refused", "state": state, "runs": 0, "records": 0,
                "reason": "El tenant ya tiene datos de coste reales; no se carga nada."}
    if state == "present":
        return {"outcome": "already-present", "state": state, "runs": report["runs"], "records": report["records"], "reason": ""}
    if state != "absent":
        return {"outcome": "refused", "state": state, "runs": 0, "records": 0,
                "reason": f"Estado {state}: ejecuta remove antes de volver a cargar el conjunto."}
    runs, records = build_dataset(tenant)
    store.insert(runs, records)
    return {"outcome": "loaded", "state": "present", "runs": len(runs), "records": len(records), "reason": ""}


def remove(store) -> dict:
    return store.delete_synthetic()


class SqlStore:
    def __init__(self, url: str | None = None, engine=None):
        if engine is None:
            from sqlalchemy import create_engine
            engine = create_engine(url, future=True)
        self.engine = engine

    @staticmethod
    def _text(sql: str):
        from sqlalchemy import text
        return text(sql)

    def list_synthetic(self) -> dict:
        with self.engine.connect() as connection:
            runs = connection.execute(self._text(
                "SELECT id, tenant_id FROM azure_cost_ingestion_runs "
                "WHERE id LIKE :pattern AND COALESCE(request->>'synthetic', 'false') = 'true'"), {"pattern": LIKE_PATTERN}).mappings().all()
            records = connection.execute(self._text(
                "SELECT id, tenant_id FROM azure_cost_records WHERE id LIKE :pattern AND ingestion_id IN " + SYNTHETIC_RUNS),
                {"pattern": LIKE_PATTERN}).mappings().all()
        return {"runs": {row["id"]: row["tenant_id"] for row in runs}, "records": {row["id"]: row["tenant_id"] for row in records}}

    def count_real(self, tenant: str) -> dict:
        with self.engine.connect() as connection:
            row = connection.execute(self._text(
                "SELECT "
                "(SELECT count(*) FROM azure_cost_ingestion_runs WHERE tenant_id = :tenant "
                "AND NOT (id LIKE :pattern AND COALESCE(request->>'synthetic', 'false') = 'true')) AS runs, "
                "(SELECT count(*) FROM azure_cost_records WHERE tenant_id = :tenant "
                "AND NOT (id LIKE :pattern AND ingestion_id IN " + SYNTHETIC_RUNS + ")) AS records"),
                {"tenant": tenant, "pattern": LIKE_PATTERN}).mappings().one()
        return {"runs": int(row["runs"]), "records": int(row["records"])}

    def insert(self, runs: Sequence[Mapping], records: Sequence[Mapping]) -> None:
        import json
        run_sql = self._text(
            "INSERT INTO azure_cost_ingestion_runs (id, tenant_id, subscription_id, request, status, page_count, "
            "retry_count, row_count, started_at, completed_at) VALUES (:id, :tenant_id, :subscription_id, "
            "CAST(:request AS JSONB), :status, :page_count, :retry_count, :row_count, :started_at, :completed_at)")
        record_sql = self._text(
            "INSERT INTO azure_cost_records (id, ingestion_id, tenant_id, subscription_id, usage_date, pretax_cost, "
            "currency, dimensions, source_row_hash, created_at, resource_group, service_name, project, tags) "
            "VALUES (:id, :ingestion_id, :tenant_id, :subscription_id, :usage_date, :pretax_cost, :currency, "
            "CAST(:dimensions AS JSONB), :source_row_hash, :created_at, :resource_group, :service_name, :project, "
            "CAST(:tags AS JSONB))")
        with self.engine.begin() as connection:
            for run in runs:
                connection.execute(run_sql, {**run, "request": json.dumps(run["request"])})
            for record in records:
                connection.execute(record_sql, {**record, "dimensions": json.dumps(record["dimensions"]),
                                                "tags": json.dumps(record["tags"])})

    def delete_synthetic(self) -> dict:
        with self.engine.begin() as connection:
            records = connection.execute(self._text(
                "DELETE FROM azure_cost_records WHERE id LIKE :pattern AND ingestion_id IN " + SYNTHETIC_RUNS),
                {"pattern": LIKE_PATTERN}).rowcount
            runs = connection.execute(self._text(
                "DELETE FROM azure_cost_ingestion_runs WHERE id LIKE :pattern AND COALESCE(request->>'synthetic', 'false') = 'true'"),
                {"pattern": LIKE_PATTERN}).rowcount
        return {"runs": int(runs or 0), "records": int(records or 0)}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Datos de coste sintéticos para validar la funcionalidad de costes (JUP-106).")
    parser.add_argument("command", choices=("apply", "status", "remove"))
    parser.add_argument("--tenant", default=DEFAULT_TENANT)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None,
         store_factory: Callable[[str], object] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    env = os.environ if env is None else env
    url = env.get("DATABASE_URL")
    if not url:
        print("Falta DATABASE_URL en el entorno.")
        return 2
    try:
        validate_tenant(args.tenant)
        store = (store_factory or SqlStore)(url)
        if args.command == "apply":
            result = apply(store, args.tenant)
            print(f"{result['outcome']}: {result['runs']} ingestas y {result['records']} registros en {args.tenant}. {result['reason']}".strip())
            return 2 if result["outcome"] == "refused" else 0
        if args.command == "remove":
            result = remove(store)
            print(f"Retiradas {result['runs']} ingestas y {result['records']} registros sintéticos.")
            return 0
        report = status(store, args.tenant)
        print(f"{report['tenant']}: estado {report['state']}, {report['runs']} ingestas y {report['records']} registros sintéticos; "
              f"datos reales: {report['real_runs']} ingestas y {report['real_records']} registros.")
        return 0
    except ValueError as error:
        print(str(error))
        return 2
    except Exception as error:  # the message may carry the connection string
        print(f"No se pudo completar la operación ({type(error).__name__}).")
        return 2


if __name__ == "__main__":
    sys.exit(main())
