#!/usr/bin/env python3
"""Single entry point for the demo cost data: generate it, load it through the ingestion, inspect it and remove it.

The rows are synthetic or public rows with shifted dates, are not Azure invoices and are loaded only through the
ingestion of the processor, never by inserting into the cost tables. Run it where the processor code and DATABASE_URL
are available, with the simulated API serving fixtures/azure-cost/demo/demo-cost.csv at AZURE_COST_API_BASE_URL:

    python scripts/demo_data.py apply
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import demo_dataset as dataset  # noqa: E402

ROOT = dataset.ROOT
LOADING_ENVIRONMENTS = ("development", "test")


def manifest() -> dict:
    return json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))


def pairs_by_tenant(data: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for pair in data["pairs"]:
        grouped.setdefault(pair["tenant"], []).append(pair)
    return grouped


def tenant_state(store, tenant: str, pairs: list[dict]) -> dict:
    counts = store.subscription_counts(tenant)
    listed = {pair["subscription"] for pair in pairs}
    # Another ingestion of a listed subscription (for example the original public dataset) is foreign data too.
    foreign = sum((item["records"] + item["runs"] if sub not in listed else 0) + item.get("foreign", 0)
                  for sub, item in counts.items())
    states = {}
    for pair in pairs:
        found = counts.get(pair["subscription"], {"runs": 0, "records": 0})
        if not found["runs"] and not found["records"]:
            states[pair["subscription"]] = "absent"
        elif found["runs"] >= 1 and found["records"] == pair["stored_rows"]:
            states[pair["subscription"]] = "present"
        else:
            states[pair["subscription"]] = "partial"
    values = set(states.values())
    if foreign:
        state = "other-data"
    elif values == {"present"}:
        state = "present"
    elif values == {"absent"}:
        state = "absent"
    else:
        state = "partial"
    return {"tenant": tenant, "state": state, "subscriptions": states, "foreign": foreign}


def all_states(store, data: dict) -> list[dict]:
    return [tenant_state(store, tenant, pairs) for tenant, pairs in pairs_by_tenant(data).items()]


def apply(store, data: dict, ingest: Callable[[str, str], bool]) -> dict:
    states = all_states(store, data)
    foreign = [item["tenant"] for item in states if item["state"] == "other-data"]
    if foreign:
        return {"outcome": "refused", "code": 2,
                "reason": "Estado other-data en " + ", ".join(foreign) + ": hay datos de coste ajenos al conjunto; no se carga nada."}
    if all(item["state"] == "present" for item in states):
        return {"outcome": "already-present", "code": 0, "loaded": 0, "reason": ""}
    if any(item["state"] != "absent" for item in states):
        names = ", ".join(f"{item['tenant']} ({item['state']})" for item in states if item["state"] != "absent")
        return {"outcome": "refused", "code": 2,
                "reason": f"Estado partial en {names}: ejecuta remove antes de volver a cargar el conjunto."}
    loaded = 0
    for pair in data["pairs"]:
        if not ingest(pair["tenant"], pair["subscription"]):
            return {"outcome": "failed", "code": 1, "loaded": loaded,
                    "reason": f"La ingesta de {pair['subscription']} en {pair['tenant']} fallo; el estado queda partial, ejecuta remove."}
        loaded += 1
    return {"outcome": "loaded", "code": 0, "loaded": loaded, "reason": ""}


def remove(store, data: dict) -> dict:
    runs = records = episodes = 0
    kept = []
    for tenant, pairs in pairs_by_tenant(data).items():
        removed = store.remove_subscriptions(tenant, [pair["subscription"] for pair in pairs])
        runs, records = runs + removed["runs"], records + removed["records"]
        # Episodes and detection state derive from the cost rows: drop them only when no other cost row is left.
        if store.tenant_cost_records(tenant):
            kept.append(tenant)
        else:
            episodes += store.drop_derived_state(tenant)
    return {"runs": runs, "records": records, "episodes": episodes, "kept_episode_tenants": kept}


def processor_directory(env: Mapping[str, str]) -> Path:
    configured = env.get("PROCESSOR_APP_DIR")
    if configured:
        return Path(configured)
    return Path("/app") if Path("/app/app/run_azure_cost_ingestion.py").exists() else ROOT / "apps" / "processor"


def run_ingestion(env: Mapping[str, str], data: dict) -> Callable[[str, str], bool]:
    definitions = {(pair["tenant"], pair["subscription"]): dataset.DEMO_DIR / pair["definition"] for pair in data["pairs"]}

    def ingest(tenant: str, subscription: str) -> bool:
        result = subprocess.run(
            [sys.executable, "-m", "app.run_azure_cost_ingestion", "--tenant-id", tenant, "--subscription-id", subscription,
             "--definition-file", str(definitions[(tenant, subscription)])],
            cwd=processor_directory(env), env=dict(env), capture_output=True, text=True)
        return result.returncode == 0
    return ingest


class SqlStore:
    """State of the demo rows; an ingestion is the demo's only when its stored request is one of the demo definitions."""

    def __init__(self, url: str | None = None, engine=None, definitions: Sequence[dict] = ()):
        if engine is None:
            from sqlalchemy import create_engine
            engine = create_engine(url, future=True)
        self.engine = engine
        self.definitions = [json.dumps(definition, sort_keys=True) for definition in definitions]

    @staticmethod
    def _text(sql: str):
        from sqlalchemy import text
        return text(sql)

    def _ours(self) -> tuple[str, dict]:
        """SQL condition on a run alias `i` that holds for the demo's ingestions, and its parameters."""
        names = [f"d{n}" for n in range(len(self.definitions))]
        condition = " OR ".join(f"i.request = CAST(:{name} AS JSONB)" for name in names) or "FALSE"
        return f"({condition})", dict(zip(names, self.definitions))

    def subscription_counts(self, tenant: str) -> dict:
        ours, definitions = self._ours()
        with self.engine.connect() as connection:
            runs = connection.execute(self._text(
                f"SELECT i.subscription_id, count(*) FILTER (WHERE {ours}) AS ours, count(*) FILTER (WHERE NOT ({ours})) AS other "
                "FROM azure_cost_ingestion_runs i WHERE i.tenant_id = :t GROUP BY 1"),
                {"t": tenant, **definitions}).mappings().all()
            records = connection.execute(self._text(
                f"SELECT r.subscription_id, count(*) FILTER (WHERE {ours}) AS ours, count(*) FILTER (WHERE NOT ({ours})) AS other "
                "FROM azure_cost_records r JOIN azure_cost_ingestion_runs i ON i.id = r.ingestion_id AND i.tenant_id = r.tenant_id "
                "WHERE r.tenant_id = :t GROUP BY 1"),
                {"t": tenant, **definitions}).mappings().all()
        counts: dict[str, dict] = {}
        for kind, rows in (("runs", runs), ("records", records)):
            for row in rows:
                item = counts.setdefault(row["subscription_id"], {"runs": 0, "records": 0, "foreign": 0})
                item[kind] += int(row["ours"])
                item["foreign"] += int(row["other"])
        return counts

    def tenant_cost_records(self, tenant: str) -> int:
        with self.engine.connect() as connection:
            return int(connection.execute(self._text(
                "SELECT (SELECT count(*) FROM azure_cost_records WHERE tenant_id = :t) "
                "+ (SELECT count(*) FROM azure_cost_ingestion_runs WHERE tenant_id = :t)"), {"t": tenant}).scalar())

    def remove_subscriptions(self, tenant: str, subscriptions: Sequence[str]) -> dict:
        from sqlalchemy import bindparam
        ours, definitions = self._ours()
        parameters = {"t": tenant, "subs": list(subscriptions), **definitions}
        runs_of_ours = ("SELECT i.id FROM azure_cost_ingestion_runs i "
                        f"WHERE i.tenant_id = :t AND i.subscription_id IN :subs AND {ours}")
        with self.engine.begin() as connection:
            records = connection.execute(self._text(
                f"DELETE FROM azure_cost_records WHERE tenant_id = :t AND ingestion_id IN ({runs_of_ours})"
            ).bindparams(bindparam("subs", expanding=True)), parameters).rowcount
            runs = connection.execute(self._text(
                f"DELETE FROM azure_cost_ingestion_runs WHERE tenant_id = :t AND id IN ({runs_of_ours})"
            ).bindparams(bindparam("subs", expanding=True)), parameters).rowcount
        return {"runs": int(runs or 0), "records": int(records or 0)}

    def drop_derived_state(self, tenant: str) -> int:
        with self.engine.begin() as connection:
            present = int(connection.execute(self._text(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' "
                "AND table_name IN ('anomaly_episodes', 'anomaly_detection_state')")).scalar())
            if present != 2:
                return 0
            episodes = connection.execute(self._text("DELETE FROM anomaly_episodes WHERE tenant_id = :t"), {"t": tenant}).rowcount
            connection.execute(self._text("DELETE FROM anomaly_detection_state WHERE tenant_id = :t"), {"t": tenant})
        return int(episodes or 0)


def demo_definitions(data: dict) -> list[dict]:
    names = sorted({pair["definition"] for pair in data["pairs"]})
    return [json.loads((dataset.DEMO_DIR / name).read_text("utf-8")) for name in names]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Datos de coste de demostracion por una sola ruta: generar, cargar, ver y retirar.")
    parser.add_argument("command", choices=("generate", "apply", "status", "remove"))
    parser.add_argument("--tenant", default=None)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None,
         store_factory: Callable[[str], object] | None = None,
         ingest: Callable[[str, str], bool] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    env = os.environ if env is None else env
    try:
        if args.command == "generate":
            for path in dataset.write_all():
                print(path.relative_to(ROOT).as_posix())
            return 0
        if args.tenant is not None:
            print("Los comandos actuan sobre todos los tenants del manifiesto y no aceptan --tenant.")
            return 2
        if args.command in ("apply", "remove") and env.get("RUNTIME_ENVIRONMENT") not in LOADING_ENVIRONMENTS:
            print("Los datos de demostracion solo se cargan o se retiran con RUNTIME_ENVIRONMENT=development o test "
                  "(valor exacto, en minusculas).")
            return 2
        url = env.get("DATABASE_URL")
        if not url:
            print("Falta DATABASE_URL en el entorno.")
            return 2
        data = manifest()
        store = store_factory(url) if store_factory else SqlStore(url, definitions=demo_definitions(data))
        if args.command == "apply":
            result = apply(store, data, ingest or run_ingestion(env, data))
            print(f"{result['outcome']}: {result.get('loaded', 0)} parejas tenant/suscripcion con datos sinteticos "
                  f"o de fechas desplazadas, no son facturas de Azure. {result['reason']}".strip())
            return result["code"]
        if args.command == "remove":
            result = remove(store, data)
            print(f"Retirados {result['runs']} ingestas, {result['records']} registros y "
                  f"{result['episodes']} episodios de anomalia derivados de ellos.")
            for tenant in result["kept_episode_tenants"]:
                print(f"Se conservan los episodios de {tenant} porque tiene otros datos de coste.")
            return 0
        for item in all_states(store, data):
            detail = ", ".join(f"{sub[:24]}={state}" for sub, state in item["subscriptions"].items())
            print(f"{item['tenant']}: {item['state']} ({detail}); datos ajenos: {item['foreign']}")
        return 0
    except ValueError as error:
        print(str(error))
        return 2
    except Exception as error:  # the message may carry the connection string
        print(f"No se pudo completar la operacion ({type(error).__name__}).")
        return 2


if __name__ == "__main__":
    sys.exit(main())
