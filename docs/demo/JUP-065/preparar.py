"""Prepara referencias offline desde objetos Git fijados; no conecta ni carga el MVP."""
import argparse
import csv
import hashlib
import io
import json
import subprocess
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = "de0d62e7c0028f35a81c5087f531d19031a90e81"
SUBSCRIPTION = "64e355d7-997c-491d-b0c1-8414dccfcf42"
SELECTED = ["JUP-069-001", "JUP-069-004", "JUP-069-003", "JUP-069-023", "JUP-069-025"]


def prepare(repo, output):
    def read(path):
        return subprocess.run(["git", "-C", str(repo), "show", f"{BASE}:{path}"],
                              check=True, capture_output=True).stdout

    def write(path, value):
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not isinstance(value, bytes):
            value = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
        target.write_bytes(value)

    fixture = "fixtures/azure-cost/EA-Cost-Actual.sample.csv"
    suite_path = "docs/validation/JUP-069-questions.json"
    suite = json.loads(read(suite_path))
    paths = [fixture, "fixtures/azure-cost/LICENSE.microsoft-finops-toolkit.txt",
             "fixtures/azure-cost/manifest.json", suite_path,
             "docs/assistant-corpus/manifest.yaml", "tools/validation-questions.mjs"]
    paths += [item["path"] for item in suite["sources"].values()]
    paths += ["docs/assistant-corpus/glossary/glossary.md"]
    hashes = {}
    for path in paths:
        data = read(path)
        hashes[path] = hashlib.sha256(data).hexdigest()
        write("sources/" + path, data)
    for source in suite["sources"].values():
        data = read(source["path"]).decode().replace("\r\n", "\n").encode()
        if hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("La fuente de JUP-069 ha cambiado")

    # Referencia independiente: solo csv, Decimal y fechas, sin importar el producto.
    rows = list(csv.DictReader(io.StringIO(read(fixture).decode("utf-8-sig"))))
    rows = [r for r in rows if r["SubscriptionId"].lower() == SUBSCRIPTION
            and "2024-06-01" <= datetime.strptime(r["Date"], "%m/%d/%Y").date().isoformat() < "2024-06-20"]
    records = defaultdict(Decimal)
    for r in rows:
        key = (r["ResourceId"], r["ResourceGroup"], r["Date"], r["BillingCurrencyCode"])
        records[key] += Decimal(r["CostInBillingCurrency"])
    totals = defaultdict(Decimal)
    counts = defaultdict(int)
    groups = defaultdict(Decimal)
    group_counts = defaultdict(int)
    labels = defaultdict(set)
    for (_, group, _, currency), cost in records.items():
        totals[currency] += cost
        counts[currency] += 1
        groups[(group.lower(), currency)] += cost
        group_counts[(group.lower(), currency)] += 1
        labels[(group.lower(), currency)].add(group)
    def money(value):
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return "0.00" if not rounded else str(rounded)
    expected = {
        "scope": "Muestra pública Microsoft; API Azure simulada, no factura real ni mes completo",
        "subscription_id": SUBSCRIPTION, "tenant_id": "tenant-core",
        "start_date": "2024-06-01", "end_date_exclusive": "2024-06-20",
        "csv_rows_selected": len(rows), "persisted_record_count": len(records),
        "totals": [{"currency": c, "exact_csv_sum": str(v), "cost": money(v), "record_count": counts[c]}
                   for c, v in sorted(totals.items())],
        "groups": [{"value": min(labels[(g, c)]), "currency": c, "cost": money(v), "record_count": group_counts[(g, c)]}
                   for (g, c), v in sorted(groups.items())],
        "group_by": "resource_group", "data_status": "available",
        "savings_identified": None, "missing_dimension_count": 0,
        "excluded_undated_count": 0,
        "precondition": "Solo esta ingesta completada en tenant-core; sin cargas previas/solapadas",
    }
    write("costes-esperados.json", expected)
    definition = {
        "type": "ActualCost", "timeframe": "Custom",
        "timePeriod": {"from": "2024-06-01T00:00:00Z", "to": "2024-06-20T00:00:00Z"},
        "dataset": {"granularity": "Daily", "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                    "grouping": [{"type": "Dimension", "name": "ResourceId"}, {"type": "Dimension", "name": "ResourceGroup"}]}}
    write("consulta-costes.json", definition)
    cases = {c["id"]: c for c in suite["cases"]}
    write("prompts.json", {"cases": [{"id": cid, "prompt": "Contexto de prueba (datos sintéticos):\n" + cases[cid]["context"] + "\n\nPregunta:\n" + cases[cid]["question"]} for cid in SELECTED]})
    write("rubricas-privadas.json", {"cases": [cases[cid] for cid in SELECTED], "sources": suite["sources"]})
    write("procedencia.json", {"jup": "JUP-065", "base_commit": BASE,
                              "source_sha256": hashes, "selected_cases": SELECTED,
                              "warning": "Preparación offline. No acredita carga, ejecución LLM ni aceptación funcional."})
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "generado")
    args = parser.parse_args()
    print(json.dumps(prepare(args.repo, args.output), indent=2, ensure_ascii=False))
