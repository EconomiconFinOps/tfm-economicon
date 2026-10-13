#!/usr/bin/env python3
"""Synthetic anomaly dataset for local demonstration: load, inspect and remove it.

The rows are synthetic, are not Azure invoices and do not come from the public dataset. They give one record per
service and day in EUR from 2026-09-01 to 2026-09-21: the two weeks compared by the JUP-030 test query keep their
totals (two alerts, five non-alerts), and one detection with the daily business rule of JUP-114 opens a P1, a P2 and a
P3 episode. `remove` also deletes the anomaly episodes and detection state of a tenant left without other cost data.
Run it inside the processor container so it uses that container's DATABASE_URL:

    docker compose exec -T processor python - apply < scripts/synthetic_anomalies.py

In PowerShell there is no `<`:

    Get-Content -Raw scripts/synthetic_anomalies.py | docker compose exec -T processor python - apply
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable, Mapping, Sequence

PREFIX = "synthetic-jup107-"
DEFAULT_TENANT = "tenant-core"
CREATED_AT = datetime(2026, 9, 15, tzinfo=timezone.utc)
SUBSCRIPTION = PREFIX + "sub-anomalies"
RUN = PREFIX + "run-anomalies"
TENANT_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
LIKE_PATTERN = PREFIX + "%"
# Only a JSON boolean true marks a run; a string or a missing key is not enough.
RUN_FLAG = "COALESCE(request->'synthetic' = 'true'::JSONB, false)"
# A record is synthetic only when its own ingestion run is.
SYNTHETIC_RUNS = "(SELECT id FROM azure_cost_ingestion_runs WHERE id LIKE :pattern AND " + RUN_FLAG + ")"

FIRST_DAY = date(2026, 9, 1)
# Daily EUR cost per service for three weeks; None means no record that day. The first two weeks keep the totals of
# the JUP-030 periods [09-01, 09-08) and [09-08, 09-15); the third week grows Compute to P1 and gives Database a P2.
DAILY = {
    "Compute": ["140"] * 5 + ["150"] * 2 + ["140"] + ["377"] * 4 + ["376"] * 2 + ["377"] * 7,
    "Analytics": ["314"] * 5 + ["315"] * 2 + ["303", "303", "480", "303", "303", "304", "304"] + ["305"] * 7,
    "Storage": ["114"] * 6 + ["116"] + ["117"] * 6 + ["118"] + ["117"] * 7,
    "Database": ["214"] * 5 + ["215"] * 2 + ["171"] * 4 + ["172"] * 3 + ["171", "300", "300", "300", "300", "300", "171"],
    "Tools": ["1"] * 4 + ["2"] * 3 + ["5"] * 2 + ["6"] * 5 + ["6"] * 7,
    "Backup": ["0"] * 7 + ["0", "0", "300", "0", "0", "0", "0"] + ["0"] * 7,
    "Networking": [None] * 13 + ["600"] + ["85"] * 7,
}
# (day, cost, service), all in EUR.
ROWS = tuple(
    (FIRST_DAY + timedelta(days=offset), value + ".00", service)
    for service, values in DAILY.items() for offset, value in enumerate(values) if value is not None
)


class RealDataError(Exception):
    """Real cost rows exist in the tenant at the moment of writing."""


def validate_tenant(tenant: str) -> str:
    if not isinstance(tenant, str) or not TENANT_PATTERN.fullmatch(tenant):
        raise ValueError("El tenant debe ser un identificador en minusculas, digitos y guiones.")
    return tenant


def build_dataset(tenant: str) -> tuple[list[dict], list[dict]]:
    validate_tenant(tenant)
    records: list[dict] = []
    for number, (day, cost, service) in enumerate(ROWS, start=1):
        identifier = f"{PREFIX}rec-{number:03d}"
        records.append({
            "id": identifier, "ingestion_id": RUN, "tenant_id": tenant, "subscription_id": SUBSCRIPTION,
            "usage_date": day, "pretax_cost": Decimal(cost), "currency": "EUR",
            "dimensions": {"synthetic": True}, "source_row_hash": identifier, "created_at": CREATED_AT,
            "resource_group": "Prod", "service_name": service, "project": "Demo", "tags": {},
        })
    runs = [{
        "id": RUN, "tenant_id": tenant, "subscription_id": SUBSCRIPTION,
        "request": {"synthetic": True, "change": "jup-114-anomalies-panel-live"}, "status": "completed",
        "page_count": 1, "retry_count": 0, "row_count": len(records),
        "started_at": CREATED_AT, "completed_at": CREATED_AT,
    }]
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
        "real_runs": real["runs"], "real_records": real["records"], "episodes": store.count_episodes(tenant),
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
    try:
        store.insert(runs, records)
    except RealDataError:
        return {"outcome": "refused", "state": state, "runs": 0, "records": 0,
                "reason": "El tenant recibio datos de coste reales mientras se cargaba; no se carga nada."}
    return {"outcome": "loaded", "state": "present", "runs": len(runs), "records": len(records), "reason": ""}


def remove(store) -> dict:
    attached = store.count_attached()
    if attached:
        return {"runs": 0, "records": 0, "refused": True,
                "reason": f"Hay {attached} registros reales colgando de ingestas sinteticas; no se retira nada hasta resolverlo a mano."}
    return {**store.delete_synthetic(), "refused": False, "reason": ""}


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
                "WHERE id LIKE :pattern AND " + RUN_FLAG), {"pattern": LIKE_PATTERN}).mappings().all()
            records = connection.execute(self._text(
                "SELECT id, tenant_id FROM azure_cost_records WHERE id LIKE :pattern AND ingestion_id IN " + SYNTHETIC_RUNS),
                {"pattern": LIKE_PATTERN}).mappings().all()
        return {"runs": {row["id"]: row["tenant_id"] for row in runs}, "records": {row["id"]: row["tenant_id"] for row in records}}

    def _count_real(self, connection, tenant: str) -> dict:
        row = connection.execute(self._text(
                "SELECT "
                "(SELECT count(*) FROM azure_cost_ingestion_runs WHERE tenant_id = :tenant "
                "AND NOT (id LIKE :pattern AND " + RUN_FLAG + ")) AS runs, "
                "(SELECT count(*) FROM azure_cost_records WHERE tenant_id = :tenant "
                "AND NOT (id LIKE :pattern AND ingestion_id IN " + SYNTHETIC_RUNS + ")) AS records"),
                {"tenant": tenant, "pattern": LIKE_PATTERN}).mappings().one()
        return {"runs": int(row["runs"]), "records": int(row["records"])}

    def count_real(self, tenant: str) -> dict:
        with self.engine.connect() as connection:
            return self._count_real(connection, tenant)

    def count_attached(self) -> int:
        with self.engine.connect() as connection:
            return int(connection.execute(self._text(
                "SELECT count(*) FROM azure_cost_records WHERE NOT id LIKE :pattern AND ingestion_id IN " + SYNTHETIC_RUNS),
                {"pattern": LIKE_PATTERN}).scalar())

    def _anomaly_tables(self, connection) -> bool:
        return int(connection.execute(self._text(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' "
            "AND table_name IN ('anomaly_episodes', 'anomaly_detection_state')")).scalar()) == 2

    def count_episodes(self, tenant: str) -> int:
        with self.engine.connect() as connection:
            if not self._anomaly_tables(connection):
                return 0
            return int(connection.execute(self._text(
                "SELECT count(*) FROM anomaly_episodes WHERE tenant_id = :tenant"), {"tenant": tenant}).scalar())

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
            for tenant in {run["tenant_id"] for run in runs}:
                if sum(self._count_real(connection, tenant).values()):
                    raise RealDataError(tenant)
            for run in runs:
                connection.execute(run_sql, {**run, "request": json.dumps(run["request"])})
            for record in records:
                connection.execute(record_sql, {**record, "dimensions": json.dumps(record["dimensions"]),
                                                "tags": json.dumps(record["tags"])})

    def delete_synthetic(self) -> dict:
        with self.engine.begin() as connection:
            tenants = sorted(connection.execute(self._text(
                "SELECT DISTINCT tenant_id FROM azure_cost_ingestion_runs WHERE id LIKE :pattern AND " + RUN_FLAG),
                {"pattern": LIKE_PATTERN}).scalars())
            records = connection.execute(self._text(
                "DELETE FROM azure_cost_records WHERE id LIKE :pattern AND ingestion_id IN " + SYNTHETIC_RUNS),
                {"pattern": LIKE_PATTERN}).rowcount
            runs = connection.execute(self._text(
                "DELETE FROM azure_cost_ingestion_runs WHERE id LIKE :pattern AND " + RUN_FLAG),
                {"pattern": LIKE_PATTERN}).rowcount
            episodes, kept = 0, []
            if self._anomaly_tables(connection):
                for tenant in tenants:
                    # Episodes of a tenant that still holds other cost data may come from those data: keep them.
                    if sum(self._count_real(connection, tenant).values()):
                        if connection.execute(self._text("SELECT count(*) FROM anomaly_episodes WHERE tenant_id = :t"),
                                              {"t": tenant}).scalar():
                            kept.append(tenant)
                        continue
                    episodes += int(connection.execute(self._text(
                        "DELETE FROM anomaly_episodes WHERE tenant_id = :t"), {"t": tenant}).rowcount or 0)
                    connection.execute(self._text("DELETE FROM anomaly_detection_state WHERE tenant_id = :t"), {"t": tenant})
        return {"runs": int(runs or 0), "records": int(records or 0), "episodes": episodes, "kept_episode_tenants": kept}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Datos de coste sinteticos para ensenar las alertas de anomalias (JUP-107).")
    parser.add_argument("command", choices=("apply", "status", "remove"))
    parser.add_argument("--tenant", default=None)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None,
         store_factory: Callable[[str], object] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    explicit_tenant = args.tenant is not None
    args.tenant = args.tenant if explicit_tenant else DEFAULT_TENANT
    env = os.environ if env is None else env
    url = env.get("DATABASE_URL")
    if not url:
        print("Falta DATABASE_URL en el entorno.")
        return 2
    try:
        validate_tenant(args.tenant)
        if args.command == "remove" and explicit_tenant:
            print("remove retira el conjunto sintetico de todos los tenants y no acepta --tenant; usa status para ver donde esta.")
            return 2
        store = (store_factory or SqlStore)(url)
        if args.command == "apply":
            result = apply(store, args.tenant)
            print(f"{result['outcome']}: {result['runs']} ingestas y {result['records']} registros sinteticos en {args.tenant}. {result['reason']}".strip())
            return 2 if result["outcome"] == "refused" else 0
        if args.command == "remove":
            result = remove(store)
            if result["refused"]:
                print(result["reason"])
                return 2
            print(f"Retiradas {result['runs']} ingestas, {result['records']} registros sinteticos y "
                  f"{result['episodes']} episodios de anomalia derivados de ellos.")
            for tenant in result["kept_episode_tenants"]:
                print(f"Se conservan los episodios de {tenant} porque tiene otros datos de coste.")
            return 0
        report = status(store, args.tenant)
        print(f"{report['tenant']}: estado {report['state']}, {report['runs']} ingestas y {report['records']} registros sinteticos; "
              f"datos reales: {report['real_runs']} ingestas y {report['real_records']} registros; "
              f"{report['episodes']} episodios de anomalia.")
        return 0
    except ValueError as error:
        print(str(error))
        return 2
    except Exception as error:  # the message may carry the connection string
        print(f"No se pudo completar la operacion ({type(error).__name__}).")
        return 2


if __name__ == "__main__":
    sys.exit(main())
