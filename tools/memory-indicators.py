#!/usr/bin/env python3
"""Mediciones de los indicadores de la memoria (JUP-130): cada subcomando escribe un informe `rows-v1` y una tabla.

Los informes se versionan en `docs/evidence/JUP-130/`, se listan en `docs/validation/evaluation-runs.json` y los
carga el comando existente `evaluation-dashboard:load`; esta herramienta no toca la base de datos.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "JUP-130"
EVENTS_PATH = ROOT / "docs" / "validation" / "JUP-130-injected-events.json"
DEFAULT_OUT = ROOT / "docs" / "evidence" / "JUP-130"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)
COMMIT_RE = re.compile(r"[0-9a-f]{7,40}", re.ASCII)
ANOMALY_GROUP = "anomaly_detection"
ROUND_DIGITS = 6


class IndicatorError(ValueError):
    pass


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
    return parser


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
    try:
        report, table = anomaly_report(reference, commit=args.commit or _git_head(), run_at=args.run_at)
    except IndicatorError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    _write(args.out, "JUP-130-anomalies.rows.json", json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    _write(args.out, "JUP-130-anomalies.md", table)
    print(f"anomalías: informe y tabla escritos en {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
