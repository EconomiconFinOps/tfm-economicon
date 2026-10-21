#!/usr/bin/env python3
"""Mediciones de los indicadores de la memoria (JUP-130): cada subcomando escribe un informe `rows-v1` y una tabla.

Los informes se versionan en `docs/evidence/JUP-130/`, se listan en `docs/validation/evaluation-runs.json` y los
carga el comando existente `evaluation-dashboard:load`; esta herramienta no toca la base de datos.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "JUP-130"
EVENTS_PATH = ROOT / "docs" / "validation" / "JUP-130-injected-events.json"
DEFAULT_OUT = ROOT / "docs" / "evidence" / "JUP-130"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)
COMMIT_RE = re.compile(r"[0-9a-f]{7,40}", re.ASCII)
ANOMALY_GROUP = "anomaly_detection"
DATA_GROUP = "data_quality"
ROUND_DIGITS = 6
API_TIMEOUT_SECONDS = 15
DEFAULT_EMAIL = "operator@example.com"
DEFAULT_PASSWORD_ENV = "DEMO_PASSWORD"


class IndicatorError(ValueError):
    pass


class ApiUnavailable(Exception):
    """El API no respondió o rechazó la sesión; el mensaje solo lleva el tipo de fallo, nunca valores."""


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dashboard = _load("economicon_jup130_evaluation_dashboard", ROOT / "tools" / "evaluation-dashboard.py")
dataset = _load("economicon_jup130_demo_dataset", ROOT / "scripts" / "demo_dataset.py")
detector = _load("economicon_jup130_anomaly_episodes", ROOT / "apps" / "backend" / "app" / "services" / "anomaly_episodes.py")


@dataclass
class Match:
    tp: int
    fp: int
    fn: int
    delays: dict[str, int] = field(default_factory=dict)


def read_events() -> dict:
    return json.loads(EVENTS_PATH.read_text("utf-8"))


def _daily_costs() -> tuple[dict, set[date]]:
    daily: dict[tuple, dict[date, Decimal]] = defaultdict(dict)
    observed: set[date] = set()
    for item in dataset.anomaly_rows():
        day = datetime.strptime(item["Date"], dataset.DATE_FORMAT).date()
        daily[(item["BillingCurrencyCode"], item["MeterCategory"])][day] = Decimal(item["CostInBillingCurrency"])
        observed.add(day)
    return daily, observed


def detect(reference: date) -> tuple[date, list]:
    """Corre la planificación real de episodios desde un estado vacío y devuelve el último día evaluado y los episodios."""
    daily, observed = _daily_costs()
    window = detector.detection_window(today=reference, last_evaluated=None, latest_observed=max(observed),
                                       earliest_observed=min(observed))
    plan = detector.plan_detection(window, tenant_id="jup130", observed_days=observed, daily=daily, episodes=[])
    if plan.status != "completed":
        raise IndicatorError(f"la fecha de referencia {reference} no deja ningún día evaluable")
    return window.last_complete_day, plan.opened


def run_detector(reference: date) -> list:
    return detect(reference)[1]


def match_events(events: list[dict], episodes: list, tolerance: int) -> Match:
    """Empareja cada evento con un episodio del mismo servicio abierto entre el día del evento y `tolerance` después."""
    used: set[int] = set()
    delays: dict[str, int] = {}
    for item in sorted(events, key=lambda e: (e["start_date"], e["id"])):
        start = date.fromisoformat(item["start_date"])
        candidates = [(episode.start_date - start).days for episode in episodes]
        best = None
        for index, episode in enumerate(episodes):
            delay = candidates[index]
            if index not in used and episode.service == item["service"] and 0 <= delay <= tolerance:
                if best is None or delay < best[0]:
                    best = (delay, index)
        if best is not None:
            used.add(best[1])
            delays[item["id"]] = best[0]
    tp = len(delays)
    return Match(tp=tp, fp=len(episodes) - tp, fn=len(events) - tp, delays=delays)


def _row(metric_id: str, behavior: str = "all", **fields) -> dict:
    row = {"measure_type": "A", "grp": ANOMALY_GROUP, "metric_id": metric_id, "behavior": behavior}
    row.update(fields)
    row["judgment"] = "automatic"
    return row


def _rate_row(metric_id: str, numerator: int, denominator: int) -> dict:
    if denominator == 0:
        return _row(metric_id, status="not_measured", unit="tasa", denominator=0)
    return _row(metric_id, status="measured", unit="tasa", value=round(numerator / denominator, ROUND_DIGITS),
                numerator=numerator, denominator=denominator)


def _count_row(metric_id: str, value: int, behavior: str = "all") -> dict:
    return _row(metric_id, behavior, status="measured", unit="recuento", value=value)


def build_report(events: list[dict], episodes: list, *, tolerance: int, reference: date, commit: str | None,
                 run_at: str | None) -> dict:
    match = match_events(events, episodes, tolerance)
    designed = [e for e in events if e["detectable_by_design"]]
    designed_hits = sum(1 for e in designed if e["id"] in match.delays)
    results = [
        _rate_row("precision", match.tp, len(episodes)),
        _rate_row("recall_all", match.tp, len(events)),
        _rate_row("recall_designed", designed_hits, len(designed)),
    ]
    if match.delays:
        results.append(_row("detection_delay_days", status="measured", unit="dias",
                            value=round(sum(match.delays.values()) / len(match.delays), ROUND_DIGITS)))
    else:
        results.append(_row("detection_delay_days", status="not_measured", unit="dias"))
    results += [_count_row("events", len(events)), _count_row("episodes", len(episodes)), _count_row("tp", match.tp),
                _count_row("fp", match.fp), _count_row("fn", match.fn)]
    results += [_count_row("event_detected", int(e["id"] in match.delays), e["id"]) for e in events]
    run = {"run_id": f"jup130-anomalies-{reference.isoformat()}", "source": SOURCE, "run_at": run_at, "commit": commit,
           "suite": "jup130-anomalies", "suite_version": "1",
           "suite_sha256": hashlib.sha256(EVENTS_PATH.read_bytes()).hexdigest(), "synthetic": True}
    document = {"contract_version": 1, "run": {k: v for k, v in run.items() if v is not None}, "results": results}
    try:
        dashboard.adapt_rows_v1(document)
    except dashboard.AdapterError as error:
        raise IndicatorError(f"el informe incumple el contrato rows-v1: {error}") from error
    return document


def _percent(row: dict) -> str:
    if row["status"] != "measured":
        return "no medido"
    return f"{row['value'] * 100:.1f}".replace(".", ",") + f" % ({row['numerator']}/{row['denominator']})"


def _result_by_id(report: dict, metric_id: str) -> dict:
    return next(r for r in report["results"] if r["metric_id"] == metric_id and r["behavior"] == "all")


def build_table(report: dict, events: list[dict], episodes: list, match: Match, reference: date, last_day: date) -> str:
    delay = _result_by_id(report, "detection_delay_days")
    delay_text = "no medido" if delay["status"] != "measured" else f"{delay['value']:.1f}".replace(".", ",") + " días"
    lines = [
        "# Calidad del detector de anomalías (JUP-130)",
        "",
        f"Fecha de referencia: {reference.isoformat()} (último día evaluado: {last_day.isoformat()}). "
        f"Comando: `python tools/memory-indicators.py anomalies --reference {reference.isoformat()}`. "
        "Con `--run-at` y `--commit` se fijan la fecha y el commit del informe.",
        "",
        "| Medida | Valor |",
        "| --- | --- |",
        f"| Precisión (episodios con evento / episodios abiertos) | {_percent(_result_by_id(report, 'precision'))} |",
        f"| Recall de todos los eventos | {_percent(_result_by_id(report, 'recall_all'))} |",
        f"| Recall de los eventos detectables por diseño | {_percent(_result_by_id(report, 'recall_designed'))} |",
        f"| Retraso medio hasta la detección | {delay_text} |",
        f"| Verdaderos positivos / falsos positivos / falsos negativos | {match.tp} / {match.fp} / {match.fn} |",
        "",
        "## Eventos inyectados",
        "",
        "| Evento | Servicio | Inicio | Naturaleza | Detectable por diseño | Resultado |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in events:
        by_design = "sí" if item["detectable_by_design"] else "no detectable por diseño"
        outcome = f"detectado, retraso {match.delays[item['id']]} d" if item["id"] in match.delays else "no detectado"
        lines.append(f"| {item['id']} | {item['service']} | {item['start_date']} | {item['nature']} | {by_design} | {outcome} |")
    lines += ["", "## Episodios abiertos", "", "| Servicio | Inicio |", "| --- | --- |"]
    lines += [f"| {e.service} | {e.start_date.isoformat()} |" for e in episodes]
    lines += [
        "",
        "## Qué no demuestra",
        "",
        f"- Son {len(events)} eventos de un conjunto de datos sintéticos: las cifras son ilustrativas y no tienen validez estadística.",
        "- Las etiquetas las escribió quien diseñó los datos y los datos se diseñaron para esta regla, así que una precisión de 1,00 y un retraso de 0 días son en parte esperables.",
        "- Un pico desde cero o la primera aparición de un servicio no se detectan por diseño: la regla exige una semana de referencia con coste positivo.",
        "- No demuestra el comportamiento con facturas reales de Azure ni con otras reglas o umbrales.",
        "",
    ]
    return "\n".join(lines)


def anomaly_report(reference: date, *, commit: str | None, run_at: str | None) -> tuple[dict, str]:
    last_day, episodes = detect(reference)
    document = read_events()
    events = [e for e in document["events"] if date.fromisoformat(e["start_date"]) <= last_day]
    tolerance = document["tolerance_days"]
    report = build_report(events, episodes, tolerance=tolerance, reference=reference, commit=commit, run_at=run_at)
    match = match_events(events, episodes, tolerance)
    return report, build_table(report, events, episodes, match, reference, last_day)


def _source_rows(reference: date):
    """Filas del CSV de la demo con fecha hasta la de referencia, con su inquilino según el manifiesto."""
    manifest = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
    tenant_of = {pair["subscription"]: pair["tenant"] for pair in manifest["pairs"]}
    with dataset.DEMO_PATH.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            day = datetime.strptime(row["Date"], dataset.DATE_FORMAT).date()
            if day <= reference and row["SubscriptionId"] in tenant_of:
                yield tenant_of[row["SubscriptionId"]], day, row["BillingCurrencyCode"], Decimal(row["CostInBillingCurrency"])


def source_totals(reference: date) -> dict[str, dict[str, Decimal]]:
    """Suma decimal exacta del CSV por inquilino y divisa, sin pasar por la normalización del producto."""
    totals: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for tenant, _, currency, cost in _source_rows(reference):
        totals[tenant][currency] += cost
    return {tenant: dict(by_currency) for tenant, by_currency in sorted(totals.items())}


def source_missing_days(reference: date) -> dict[str, int]:
    """Días sin ningún registro entre el primero y el último con datos de cada inquilino; no son días de coste cero."""
    seen: dict[str, set[date]] = defaultdict(set)
    for tenant, day, _, _ in _source_rows(reference):
        seen[tenant].add(day)
    return count_missing_days(seen)


def count_missing_days(seen: dict[str, set[date]]) -> dict[str, int]:
    return {tenant: ((max(days) - min(days)).days + 1) - len(days) for tenant, days in sorted(seen.items())}


def freshness_days(fetch, tenant: str, reference: date, window_start: date) -> int | None:
    """Días entre la fecha de referencia y el último día con datos visibles, por bisección sobre el resumen."""
    def has_data(day: date) -> bool:
        return any(item["record_count"] > 0 for item in fetch(tenant, day, reference + timedelta(days=1)))
    if not has_data(window_start):
        return None
    low, high = window_start, reference
    while low < high:
        middle = low + timedelta(days=((high - low).days + 1) // 2)
        if has_data(middle):
            low = middle
        else:
            high = middle - timedelta(days=1)
    return (reference - low).days


def round_money(value: Decimal) -> Decimal:
    """Un único redondeo ROUND_HALF_UP a dos decimales sobre la suma exacta, como exige el contrato de costes."""
    with localcontext() as context:
        context.prec = max(80, len(value.as_tuple().digits) + 20)
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal("0.00") if rounded == 0 else rounded


def reconcile(source: dict[str, Decimal], fetch, tenant: str, window_start: date, reference: date) -> dict[str, int]:
    """Diferencia fuente menos API por divisa, en unidades menores enteras; cada divisa por separado."""
    api: dict[str, Decimal] = defaultdict(Decimal)
    for item in fetch(tenant, window_start, reference + timedelta(days=1)):
        api[item["currency"]] += Decimal(item["cost"])
    deltas = {}
    for currency in sorted(set(source) | set(api)):
        minor = (round_money(source.get(currency, Decimal(0))) - round_money(api.get(currency, Decimal(0)))) * 100
        if abs(minor) > dashboard.ROW_MAX_INTEGER:
            raise IndicatorError(f"la diferencia de {currency} supera el mayor entero seguro del contrato")
        deltas[currency] = int(minor)
    return deltas


class ApiSession:
    """Sesión de solo lectura contra el backend; la contraseña se usa para entrar y no se guarda."""

    def __init__(self, base_url: str, email: str, password: str):
        self.base = base_url.rstrip("/")
        body = self._request("/auth/login", {"email": email, "password": password})
        try:
            self.token = body["access_token"]
        except (KeyError, TypeError):
            raise ApiUnavailable("respuesta_invalida") from None

    def _request(self, path: str, payload: dict | None = None, headers: dict | None = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise ApiUnavailable(f"http_{error.code}") from None
        except (urllib.error.URLError, OSError):
            raise ApiUnavailable("conexion") from None
        except ValueError:
            raise ApiUnavailable("respuesta_invalida") from None

    def _get(self, path: str, tenant: str | None = None):
        headers = {"Authorization": "Bearer " + self.token}
        if tenant:
            headers["X-Tenant-Id"] = tenant
        return self._request(path, None, headers)

    def reference_date(self) -> date:
        try:
            return date.fromisoformat(self._get("/billing/reference-date")["reference_date"])
        except (KeyError, TypeError, ValueError):
            raise ApiUnavailable("respuesta_invalida") from None

    def summary(self, tenant: str, start: date, end: date) -> list[dict]:
        body = self._get(f"/billing/summary?start_date={start.isoformat()}&end_date={end.isoformat()}", tenant)
        try:
            return [{"currency": t["currency"], "cost": t["cost"], "record_count": t["record_count"]} for t in body["totals"]]
        except (KeyError, TypeError):
            raise ApiUnavailable("respuesta_invalida") from None


def _data_row(metric_id: str, behavior: str, unit: str, value: int | None) -> dict:
    row = {"measure_type": "B", "grp": DATA_GROUP, "metric_id": metric_id, "behavior": behavior}
    if value is None:
        return {**row, "status": "not_measured", "unit": unit}
    return {**row, "status": "measured", "value": value, "unit": unit}


def _api_measurements(fetch, tenants, source, reference: date) -> dict:
    start = dataset.WINDOW_START
    return {
        "freshness": {tenant: freshness_days(fetch, tenant, reference, start) for tenant in tenants},
        "deltas": {tenant: reconcile(source[tenant], fetch, tenant, start, reference) for tenant in tenants},
    }


def data_report(*, fetch, reference_date_from_api: date | None, reference: date, commit: str | None,
                run_at: str | None) -> tuple[dict, str]:
    source = source_totals(reference)
    missing = source_missing_days(reference)
    tenants = list(source)
    measured = None
    if fetch is not None:
        if reference_date_from_api != reference:
            raise IndicatorError("la fecha de referencia del API no coincide con la solicitada")
        try:
            measured = _api_measurements(fetch, tenants, source, reference)
        except ApiUnavailable:
            measured = None
    results = []
    for tenant in tenants:
        results.append(_data_row("freshness_days", tenant, "dias", measured["freshness"][tenant] if measured else None))
        results.append(_data_row("source_missing_days", tenant, "dias", missing[tenant]))
        for currency in source[tenant]:
            behavior = f"{tenant}/{currency}"
            delta = measured["deltas"][tenant].get(currency) if measured else None
            results.append(_data_row("reconciliation_delta_minor", behavior, "centimos", delta))
            results.append(_data_row("reconciled", behavior, "recuento", None if delta is None else int(delta == 0)))
    run = {"run_id": f"jup130-data-{reference.isoformat()}", "source": SOURCE, "run_at": run_at, "commit": commit,
           "suite": "jup130-data", "suite_version": "1", "synthetic": True}
    document = {"contract_version": 1, "run": {k: v for k, v in run.items() if v is not None}, "results": results}
    try:
        dashboard.adapt_rows_v1(document)
    except dashboard.AdapterError as error:
        raise IndicatorError(f"el informe incumple el contrato rows-v1: {error}") from error
    return document, build_data_table(results, reference, measured is not None)


def _cell(row: dict) -> str:
    return "no medido" if row["status"] != "measured" else str(row["value"])


def build_data_table(results: list[dict], reference: date, api_measured: bool) -> str:
    lines = [
        "# Frescura y reconciliación de los datos de coste (JUP-130)",
        "",
        f"Fecha de referencia: {reference.isoformat()}. Comando: `python tools/memory-indicators.py data --reference {reference.isoformat()}`. "
        "Con `--base-url` se mide contra el API de una pila levantada; sin ella la frescura y la reconciliación quedan como no medidas. "
        "Con `--run-at` y `--commit` se fijan la fecha y el commit del informe.",
        "",
    ]
    if not api_measured:
        lines += ["**No se midió contra el API en esta ejecución: frescura y reconciliación figuran como no medidas.**", ""]
    lines += ["## Por inquilino", "", "| Inquilino | Frescura (días) | Días sin registro en la fuente |", "| --- | --- | --- |"]
    by_key = {(r["metric_id"], r["behavior"]): r for r in results}
    tenants = sorted({r["behavior"] for r in results if r["metric_id"] == "freshness_days"})
    for tenant in tenants:
        lines.append(f"| {tenant} | {_cell(by_key[('freshness_days', tenant)])} | {_cell(by_key[('source_missing_days', tenant)])} |")
    lines += ["", "## Reconciliación por inquilino y divisa", "",
              "| Inquilino y divisa | Diferencia (unidades menores) | Reconciliado |", "| --- | --- | --- |"]
    for row in (r for r in results if r["metric_id"] == "reconciliation_delta_minor"):
        flag = by_key[("reconciled", row["behavior"])]
        text = "no medido" if flag["status"] != "measured" else ("sí" if flag["value"] else "no")
        lines.append(f"| {row['behavior']} | {_cell(row)} | {text} |")
    lines += [
        "",
        "## Qué no demuestra",
        "",
        "- La fuente es un conjunto sintético generado por el propio proyecto: reconciliar contra él no demuestra la integridad de datos reales de Azure.",
        "- La frescura se mide contra la fecha de referencia configurada; con una fecha simulada no demuestra puntualidad de una ingesta real.",
        "- Un día sin registro es un hueco de datos, no un día de coste cero; los huecos se cuentan en la fuente.",
        "- Una diferencia de cero demuestra que la suma almacenada coincide con la de la fuente, no que la fuente sea correcta.",
        "",
    ]
    return "\n".join(lines)


def _git_head() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out if COMMIT_RE.fullmatch(out) else None


def _write(directory: Path, name: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(text, encoding="utf-8", newline="\n")


def _pattern(regex: re.Pattern, what: str):
    def check(value: str) -> str:
        if not regex.fullmatch(value):
            raise argparse.ArgumentTypeError(f"{what} no válido")
        return value
    return check


def _run_at(value: str) -> str:
    if not dashboard.RUN_AT_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(f"--run-at {dashboard.RUN_AT_PROBLEM}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    anomalies = commands.add_parser("anomalies", help="precisión, recall y retraso del detector de anomalías")
    anomalies.add_argument("--reference", required=True, type=_pattern(DATE_RE, "la fecha AAAA-MM-DD"))
    anomalies.add_argument("--out", type=Path, default=DEFAULT_OUT)
    anomalies.add_argument("--run-at", type=_run_at)
    anomalies.add_argument("--commit", type=_pattern(COMMIT_RE, "el commit"))
    data = commands.add_parser("data", help="frescura y reconciliación de los datos de coste")
    data.add_argument("--reference", required=True, type=_pattern(DATE_RE, "la fecha AAAA-MM-DD"))
    data.add_argument("--out", type=Path, default=DEFAULT_OUT)
    data.add_argument("--run-at", type=_run_at)
    data.add_argument("--commit", type=_pattern(COMMIT_RE, "el commit"))
    data.add_argument("--base-url", type=_pattern(re.compile(r"https?://\S+", re.ASCII), "la dirección http(s)"))
    data.add_argument("--email", default=DEFAULT_EMAIL)
    data.add_argument("--password-env", default=DEFAULT_PASSWORD_ENV, help="variable de entorno con la contraseña")
    return parser


def _data_command(args, reference: date, commit: str | None) -> tuple[dict, str]:
    fetch, api_reference = None, None
    if args.base_url:
        password = os.environ.get(args.password_env)
        if not password:
            print(f"aviso: la variable {args.password_env} no está definida; la medición contra el API queda como no medida", file=sys.stderr)
        else:
            try:
                session = ApiSession(args.base_url, args.email, password)
                api_reference = session.reference_date()
                fetch = session.summary
            except ApiUnavailable as error:
                print(f"aviso: el API no está disponible ({error}); la medición contra el API queda como no medida", file=sys.stderr)
    return data_report(fetch=fetch, reference_date_from_api=api_reference, reference=reference, commit=commit, run_at=args.run_at)


def main(argv: list[str] | None = None) -> int:
    # La consola de Windows usa cp1252 y los mensajes llevan acentos.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        reference = date.fromisoformat(args.reference)
    except ValueError:
        parser.error("la fecha de referencia no es una fecha real")
    commit = args.commit or _git_head()
    try:
        if args.command == "anomalies":
            report, table = anomaly_report(reference, commit=commit, run_at=args.run_at)
        else:
            report, table = _data_command(args, reference, commit)
    except IndicatorError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    stem = "JUP-130-anomalies" if args.command == "anomalies" else "JUP-130-data"
    _write(args.out, stem + ".rows.json", json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    _write(args.out, stem + ".md", table)
    print(f"{args.command}: informe y tabla escritos en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
