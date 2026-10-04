"""Reference calculator for the technical metrics of the assistant (JUP-067).

It validates a results file against the question bank (JUP-069), the retrieval
labels (JUP-022) and the metric catalogue, and computes every catalogue metric
offline, with the standard library only and deterministically. It never opens a
network connection or a database, and the results format cannot carry the text of
questions, responses or fragments, nor credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "docs" / "validation" / "JUP-067-metrics-catalogue.json"
BANK_PATH = ROOT / "docs" / "validation" / "JUP-069-questions.json"
LABELS_PATH = ROOT / "docs" / "validation" / "JUP-022-retrieval-labels.json"

RESULTS_VERSION = 1
OUTCOMES = ("pass", "fail", "blocked", "not_run")
EVALUATED = ("pass", "fail")
BEHAVIORS = ("answer", "clarify", "abstain")
STAGES = ("embedding", "retrieval", "generation", "total")
PROVIDER_FAILURES = (
    "timeout", "connection", "transport", "authentication", "request",
    "redirect", "rate_limit", "upstream", "invalid_response",
)
FAILURE_CATEGORIES = PROVIDER_FAILURES + ("schema_validation",)
FIGURE_ORIGINS = ("context", "evidence", "question", "untraceable")
CHECK_CLASSES = ("objective", "judged")
COVERAGE_WITH_SECTIONS = ("direct", "partial")
FORBIDDEN_NAMES = frozenset({"question", "prompt", "response", "content", "answer", "text", "excerpt"})
SECRET_NAME = re.compile(r"(key|secret|token|password|authorization|credential)", re.IGNORECASE)
COMPARATORS = {">=": lambda value, target: value >= target, "<=": lambda value, target: value <= target, "==": lambda value, target: value == target}
Z = 1.959963984540054
MINIMUM = {"median": 5, "p95": 20, "max": 5, "quartile": 5}
COMPUTED_IDS = (
    "ACC-1", "ACC-2", "ACC-3", "REL-1", "REL-2", "REL-3", "REL-4", "GRD-1", "GRD-2", "GRD-3",
    "LAT-1", "LAT-2", "LAT-3", "LAT-4", "STR-1", "STR-2", "AVL-1",
)
METRIC_TEXT_FIELDS = ("id", "family", "name", "numerator", "denominator", "population", "source", "unit")


class CatalogueError(ValueError):
    pass


class ResultsError(ValueError):
    pass


def suite_digest(bank: dict) -> str:
    text = json.dumps(bank, separators=(",", ":"), ensure_ascii=False).replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf8")).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf8"))


def load_catalogue(path: Path = CATALOGUE_PATH) -> dict:
    return load_json(path)


def validate_catalogue(catalogue: dict) -> None:
    if not isinstance(catalogue, dict) or not isinstance(catalogue.get("catalogue_version"), str) or not catalogue["catalogue_version"]:
        raise CatalogueError("catalogue_version: required text")
    families = catalogue.get("families")
    metrics = catalogue.get("metrics")
    if not isinstance(families, list) or not families or not isinstance(metrics, list):
        raise CatalogueError("families and metrics: required lists")
    seen: set[str] = set()
    for index, metric in enumerate(metrics):
        for field in METRIC_TEXT_FIELDS:
            value = metric.get(field) if isinstance(metric, dict) else None
            if not isinstance(value, str) or not value.strip():
                raise CatalogueError(f"metrics[{index}].{field}: required non-empty text")
        if metric["family"] not in families:
            raise CatalogueError(f"metrics[{index}].family: not one of the catalogue families")
        if metric["id"] in seen:
            raise CatalogueError(f"metrics[{index}].id: duplicated identifier {metric['id']}")
        seen.add(metric["id"])
        target = metric.get("target")
        if target is not None and not (
            isinstance(target, dict) and target.get("comparator") in COMPARATORS
            and isinstance(target.get("value"), (int, float)) and not isinstance(target["value"], bool)
            and isinstance(target.get("origin"), str) and target.get("provisional") is True
        ):
            raise CatalogueError(f"metrics[{index}].target: needs comparator, value, origin and provisional true")
    for missing in sorted(set(COMPUTED_IDS) - seen):
        raise CatalogueError(f"catalogue lacks the computed metric {missing}")
    for extra in sorted(seen - set(COMPUTED_IDS)):
        raise CatalogueError(f"catalogue defines {extra}, which the calculator does not compute")


def wilson(successes: int, total: int) -> tuple[float, float] | None:
    if total <= 0:
        return None
    p = successes / total
    denominator = 1 + Z * Z / total
    centre = (p + Z * Z / (2 * total)) / denominator
    margin = Z * math.sqrt(p * (1 - p) / total + Z * Z / (4 * total * total)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def percentile(values: list[float], fraction: float, minimum: int = 1) -> float | None:
    if len(values) < minimum or not values:
        return None
    ordered = sorted(values)
    return ordered[max(1, math.ceil(fraction * len(ordered))) - 1]


def rate(successes: int, total: int) -> dict:
    interval = wilson(successes, total)
    if interval is None:
        return {"k": successes, "n": total, "rate": None, "ci95": None, "available": False}
    return {
        "k": successes, "n": total, "rate": round(successes / total, 6),
        "ci95": [round(interval[0], 6), round(interval[1], 6)], "available": True,
    }


def fail(path: str, message: str) -> None:
    raise ResultsError(f"{path}: {message}")


def scan_names(node, path: str) -> None:
    if isinstance(node, dict):
        for name, value in node.items():
            here = f"{path}.{name}" if path else str(name)
            if str(name).lower() in FORBIDDEN_NAMES or SECRET_NAME.search(str(name)):
                fail(here, "field not allowed in a results file")
            scan_names(value, here)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            scan_names(value, f"{path}[{index}]")


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def is_count(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def require(node: dict, field: str, path: str, kind) -> object:
    if not isinstance(node, dict) or field not in node:
        fail(f"{path}.{field}" if path else field, "required")
    value = node[field]
    if not kind(value):
        fail(f"{path}.{field}" if path else field, "wrong type or value")
    return value


def text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_run(run: dict, bank: dict) -> None:
    require(run, "commit", "run", text)
    require(run, "date", "run", text)
    require(run, "provider", "run", text)
    require(run, "alias", "run", text)
    bank_header = require(run, "bank", "run", lambda value: isinstance(value, dict))
    require(bank_header, "suite_version", "run.bank", text)
    digest = require(bank_header, "suite_sha256", "run.bank", text)
    if bank_header["suite_version"] != bank.get("suite_version") or digest != suite_digest(bank):
        fail("run.bank.suite_sha256", "does not match the question bank in the repository")
    corpus = require(run, "corpus", "run", lambda value: isinstance(value, dict))
    require(corpus, "sha256", "run.corpus", text)
    require(corpus, "documents", "run.corpus", is_count)
    require(corpus, "chunks", "run.corpus", is_count)
    retrieval = require(run, "retrieval", "run", lambda value: isinstance(value, dict))
    require(retrieval, "top_k", "run.retrieval", is_count)
    require(retrieval, "chunk_size", "run.retrieval", is_count)
    require(retrieval, "chunk_overlap", "run.retrieval", is_count)
    if "max_distance" not in retrieval or not (retrieval["max_distance"] is None or is_number(retrieval["max_distance"])):
        fail("run.retrieval.max_distance", "required number or null")
    require(run, "generation", "run", lambda value: isinstance(value, dict))
    availability = require(run, "availability", "run", lambda value: isinstance(value, dict))
    requests = require(availability, "requests", "run.availability", is_count)
    errors = require(availability, "server_errors", "run.availability", is_count)
    if errors > requests:
        fail("run.availability.server_errors", "cannot exceed the requests")


def validate_case(item: dict, index: int) -> None:
    path = f"cases[{index}]"
    outcome = require(item, "outcome", path, lambda value: value in OUTCOMES)
    checks = require(item, "checks", path, lambda value: isinstance(value, list))
    failed_check = False
    for position, check in enumerate(checks):
        where = f"{path}.checks[{position}]"
        require(check, "id", where, text)
        kind = require(check, "class", where, lambda value: value in CHECK_CLASSES)
        result = require(check, "result", where, lambda value: value in EVALUATED)
        deciders = require(check, "decided_by", where, lambda value: isinstance(value, list) and value and all(text(name) for name in value))
        if kind == "objective" and deciders != ["rule"]:
            fail(f"{where}.decided_by", "an objective check is decided by rule")
        if kind == "judged" and ("rule" in deciders or len(deciders) > 2):
            fail(f"{where}.decided_by", "a judged check names one or two people and never the rule")
        failed_check = failed_check or result == "fail"
    if outcome == "pass" and failed_check:
        fail(f"{path}.outcome", "pass requires every check to pass")
    retrieved = require(item, "retrieved", path, lambda value: isinstance(value, list))
    for position, fragment in enumerate(retrieved):
        where = f"{path}.retrieved[{position}]"
        require(fragment, "chunk_id", where, text)
        require(fragment, "source", where, text)
        require(fragment, "heading", where, lambda value: isinstance(value, str))
        require(fragment, "distance", where, lambda value: is_number(value) and 0 <= value <= 2)
    require(item, "citations", path, lambda value: isinstance(value, list) and all(text(entry) for entry in value))
    figures = require(item, "figures", path, lambda value: isinstance(value, list))
    for position, figure in enumerate(figures):
        require(figure, "origin", f"{path}.figures[{position}]", lambda value: value in FIGURE_ORIGINS)
    latency = require(item, "latency_ms", path, lambda value: isinstance(value, dict))
    for stage, value in latency.items():
        if stage not in STAGES or not is_number(value) or value < 0:
            fail(f"{path}.latency_ms.{stage}", "a known stage with a non-negative number is required")
    category = item.get("failure_category")
    stage = item.get("failure_stage")
    if category is not None and category not in FAILURE_CATEGORIES:
        fail(f"{path}.failure_category", "not one of the fixed failure categories")
    if stage is not None and stage not in STAGES[:3]:
        fail(f"{path}.failure_stage", "not one of the call stages")
    if (category is None) != (stage is None):
        fail(f"{path}.failure_stage" if category else f"{path}.failure_category", "required together with the other failure field")
    if "structured_ok" not in item or not (item["structured_ok"] is None or isinstance(item["structured_ok"], bool)):
        fail(f"{path}.structured_ok", "required boolean or null")
    refs = require(item, "evidence_refs", path, lambda value: isinstance(value, dict))
    total = require(refs, "total", f"{path}.evidence_refs", is_count)
    dangling = require(refs, "dangling", f"{path}.evidence_refs", is_count)
    if dangling > total:
        fail(f"{path}.evidence_refs.dangling", "cannot exceed the emitted references")


def validate_results(results: dict, bank: dict, labels: dict, catalogue: dict) -> None:
    scan_names(results, "")
    if not isinstance(results, dict) or results.get("results_version") != RESULTS_VERSION:
        fail("results_version", f"must be {RESULTS_VERSION}")
    if results.get("catalogue_version") != catalogue["catalogue_version"]:
        fail("catalogue_version", "does not match the current catalogue version")
    if "synthetic" in results and not isinstance(results["synthetic"], bool):
        fail("synthetic", "must be true or false")
    run = require(results, "run", "", lambda value: isinstance(value, dict))
    validate_run(run, bank)
    cases = require(results, "cases", "", lambda value: isinstance(value, list))
    expected = {case["id"] for case in bank["cases"]}
    seen: set[str] = set()
    for index, item in enumerate(cases):
        identifier = require(item, "case", f"cases[{index}]", text)
        if identifier not in expected:
            fail("cases", f"unknown case {identifier}")
        if identifier in seen:
            fail("cases", f"duplicated case {identifier}")
        seen.add(identifier)
        validate_case(item, index)
    for identifier in sorted(expected - seen):
        fail("cases", f"missing case {identifier}")
    labelled = {label["case"] for label in labels["labels"]}
    for identifier in sorted(expected - labelled):
        fail("labels", f"no retrieval label for case {identifier}")


def target_result(metric: dict, value) -> dict | None:
    target = metric["target"]
    if target is None:
        return None
    result = {"comparator": target["comparator"], "value": target["value"], "origin": target["origin"], "provisional": True}
    if "scope" in target:
        result["scope"] = target["scope"]
    result["met"] = None if value is None else bool(COMPARATORS[target["comparator"]](value, target["value"]))
    return result


def compute(results: dict, bank: dict, labels: dict, catalogue: dict) -> dict:
    validate_results(results, bank, labels, catalogue)
    definitions = {metric["id"]: metric for metric in catalogue["metrics"]}
    cases = results["cases"]
    behaviors = {case["id"]: case["behavior"] for case in bank["cases"]}
    declared_sources = {case["id"]: set(case["sources"]) for case in bank["cases"]}
    critical_ids = {case["id"] for case in bank["cases"] if case["expected"].get("numbers")}
    label_of = {label["case"]: label for label in labels["labels"]}
    run = results["run"]

    evaluated = [item for item in cases if item["outcome"] in EVALUATED]
    attempted = [item for item in cases if item["outcome"] != "not_run"]
    answers = [item for item in evaluated if behaviors[item["case"]] == "answer"]
    counts = {"cases": len(cases)}
    for outcome in OUTCOMES:
        counts[outcome] = sum(1 for item in cases if item["outcome"] == outcome)

    def passed(group: list[dict]) -> dict:
        return rate(sum(1 for item in group if item["outcome"] == "pass"), len(group))

    metrics: dict[str, dict] = {}
    metrics["ACC-1"] = passed(answers)
    objective = [check for item in answers for check in item["checks"] if check["class"] == "objective"]
    judged = [check for item in answers for check in item["checks"] if check["class"] == "judged"]
    acc2 = rate(sum(1 for check in objective if check["result"] == "pass"), len(objective))
    acc2["judged"] = rate(sum(1 for check in judged if check["result"] == "pass"), len(judged))
    metrics["ACC-2"] = acc2
    metrics["ACC-3"] = {"groups": {
        behavior: passed([item for item in evaluated if behaviors[item["case"]] == behavior]) for behavior in ("clarify", "abstain")
    }}

    def document_hit(item: dict) -> bool:
        return any(fragment["source"] in declared_sources[item["case"]] for fragment in item["retrieved"])

    def section_hit(item: dict) -> bool:
        wanted = {(entry["source"], entry["heading"]) for entry in label_of[item["case"]]["expect"]}
        return any((fragment["source"], fragment["heading"]) in wanted for fragment in item["retrieved"])

    with_sections = [item for item in answers if label_of[item["case"]]["coverage"] in COVERAGE_WITH_SECTIONS]
    metrics["REL-1"] = rate(sum(1 for item in answers if document_hit(item)), len(answers))
    metrics["REL-2"] = rate(sum(1 for item in with_sections if section_hit(item)), len(with_sections))
    metrics["REL-3"] = {"groups": {
        behavior: rate(
            sum(1 for item in evaluated if behaviors[item["case"]] == behavior and not item["retrieved"]),
            sum(1 for item in evaluated if behaviors[item["case"]] == behavior),
        )
        for behavior in BEHAVIORS
    }}
    similarities = [1 - min(fragment["distance"] for fragment in item["retrieved"]) for item in evaluated if item["retrieved"]]
    quartile = MINIMUM["quartile"]
    metrics["REL-4"] = {
        "n": len(similarities),
        "median": percentile(similarities, 0.5, quartile),
        "q1": percentile(similarities, 0.25, quartile),
        "q3": percentile(similarities, 0.75, quartile),
        "available": len(similarities) >= quartile,
    }

    citations = [(item, entry) for item in evaluated for entry in item["citations"]]
    valid = sum(1 for item, entry in citations if entry in {fragment["chunk_id"] for fragment in item["retrieved"]})
    metrics["GRD-1"] = rate(valid, len(citations))
    untraceable = {
        item["case"]: sum(1 for figure in item["figures"] if figure["origin"] == "untraceable") for item in evaluated
    }
    by_case = {case_id: number for case_id, number in sorted(untraceable.items()) if number}
    critical_evaluated = [item["case"] for item in evaluated if item["case"] in critical_ids]
    critical_failures = sorted(case_id for case_id in by_case if case_id in critical_ids)
    metrics["GRD-2"] = {
        "total": sum(by_case.values()), "by_case": by_case, "critical_failures": critical_failures,
        "available": bool(critical_evaluated),
    }
    emitted = sum(item["evidence_refs"]["total"] for item in evaluated)
    dangling = sum(item["evidence_refs"]["dangling"] for item in evaluated)
    metrics["GRD-3"] = rate(emitted - dangling, emitted)

    corpus = {"documents": run["corpus"]["documents"], "chunks": run["corpus"]["chunks"]}
    stage_values = {stage: [item["latency_ms"][stage] for item in attempted if stage in item["latency_ms"]] for stage in STAGES}
    failures = {stage: sum(1 for item in attempted if item.get("failure_stage") == stage) for stage in STAGES}

    def per_stage(statistic) -> dict:
        return {stage: {"n": len(stage_values[stage]), "value": statistic(stage_values[stage]), "covers": "successful calls only"} for stage in STAGES}

    metrics["LAT-1"] = {"stages": per_stage(lambda values: percentile(values, 0.5, MINIMUM["median"])), "corpus": corpus}
    metrics["LAT-2"] = {"stages": per_stage(lambda values: percentile(values, 0.95, MINIMUM["p95"])), "corpus": corpus}
    metrics["LAT-3"] = {"stages": per_stage(lambda values: percentile(values, 1.0, MINIMUM["max"])), "corpus": corpus}
    metrics["LAT-4"] = {"stages": {stage: rate(failures[stage], failures[stage] + len(stage_values[stage])) for stage in STAGES[:3]}}
    structured = [item["structured_ok"] for item in attempted if item["structured_ok"] is not None]
    metrics["STR-1"] = rate(sum(1 for value in structured if value), len(structured))
    by_category = {category: 0 for category in FAILURE_CATEGORIES}
    for item in attempted:
        if item["failure_category"]:
            by_category[item["failure_category"]] += 1
    metrics["STR-2"] = {"by_category": by_category, "total": sum(by_category.values())}
    availability = run["availability"]
    metrics["AVL-1"] = rate(availability["requests"] - availability["server_errors"], availability["requests"])

    for metric_id in ("ACC-2", "STR-1"):
        metrics[metric_id]["target"] = target_result(definitions[metric_id], metrics[metric_id]["rate"])
    metrics["GRD-2"]["target"] = target_result(
        definitions["GRD-2"], len(critical_failures) if metrics["GRD-2"]["available"] else None
    )
    for metric_id in ("LAT-1", "LAT-2", "LAT-3"):
        for stage, entry in metrics[metric_id]["stages"].items():
            entry["target"] = target_result(definitions[metric_id], entry["value"]) if stage == "total" else None
    for metric_id in ("ACC-1", "ACC-3", "REL-1", "REL-2", "REL-3", "REL-4", "GRD-1", "GRD-3", "LAT-4", "STR-2", "AVL-1"):
        metrics[metric_id].setdefault("target", None)

    single_decider = sorted({
        item["case"] for item in evaluated if item["case"] in critical_ids and any(
            check["class"] == "judged" and len(set(check["decided_by"])) < 2 for check in item["checks"]
        )
    })
    notes = []
    if run["provider"] == "mock":
        notes.append("El proveedor de embeddings es mock: la similitud y los aciertos de recuperacion no tienen significado semantico.")
    if results.get("synthetic"):
        notes.append("Datos sinteticos de ejemplo: no son una medicion del asistente.")
    return {
        "report_version": 1,
        "catalogue_version": catalogue["catalogue_version"],
        "run": {
            "commit": run["commit"], "date": run["date"], "provider": run["provider"], "alias": run["alias"],
            "suite_version": run["bank"]["suite_version"], "corpus": corpus, "retrieval": run["retrieval"],
            "synthetic": bool(results.get("synthetic")),
        },
        "counts": counts,
        "metrics": metrics,
        "gaps": sorted(label["case"] for label in labels["labels"] if label["coverage"] == "none"),
        "critical": {"cases": sorted(critical_ids), "single_decider_cases": single_decider},
        "notes": notes,
    }


def describe_rate(entry: dict) -> str:
    if not entry["available"]:
        return f"no disponible ({entry['k']} de {entry['n']})"
    low, high = entry["ci95"]
    return f"{entry['k']} de {entry['n']} ({entry['rate'] * 100:.1f} %; IC 95 % {low * 100:.1f} a {high * 100:.1f} %)"


def describe_target(target: dict | None) -> str:
    if target is None:
        return "sin objetivo"
    state = {True: "cumple", False: "no cumple", None: "sin datos"}[target["met"]]
    scope = f", {target['scope']}" if "scope" in target else ""
    return f"objetivo provisional {target['comparator']} {target['value']} (origen {target['origin']}{scope}): {state}"


def number(value) -> str:
    return "no disponible" if value is None else f"{value:.3f}".rstrip("0").rstrip(".")


def render_markdown(report: dict, catalogue: dict) -> str:
    definitions = {metric["id"]: metric for metric in catalogue["metrics"]}
    metrics = report["metrics"]
    run = report["run"]
    lines = ["# Informe de metricas tecnicas del asistente", ""]
    lines += [
        f"Catalogo {report['catalogue_version']} · generado {report.get('generated_at', 'sin fecha')}",
        f"Commit {run['commit']} · fecha de la ejecucion {run['date']} · proveedor {run['provider']} · alias {run['alias']}",
        f"Corpus: {run['corpus']['documents']} documentos y {run['corpus']['chunks']} fragmentos · top_k {run['retrieval']['top_k']}"
        f" · distancia maxima {run['retrieval']['max_distance']} · fragmentos de {run['retrieval']['chunk_size']} con solape {run['retrieval']['chunk_overlap']}",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"> {note}")
    if report["notes"]:
        lines.append("")
    counts = report["counts"]
    lines += [
        f"Casos: {counts['cases']} · pass {counts['pass']} · fail {counts['fail']} · blocked {counts['blocked']} · not_run {counts['not_run']}."
        " Los casos blocked y not_run no entran en ningun denominador.",
        "",
        "Las tasas se muestran como k de n con su intervalo de Wilson al 95 %. Los objetivos son provisionales y no son una puerta de aceptacion.",
        "",
        "| Id | Metrica | Valor | Objetivo |",
        "| --- | --- | --- | --- |",
    ]

    def row(metric_id: str, label: str, value: str, target: dict | None) -> None:
        lines.append(f"| {metric_id} | {label} | {value} | {describe_target(target)} |")

    for metric_id in ("ACC-1", "ACC-2", "REL-1", "REL-2", "GRD-1", "GRD-3", "STR-1", "AVL-1"):
        entry = metrics[metric_id]
        row(metric_id, definitions[metric_id]["name"], describe_rate(entry), entry["target"])
    row("ACC-2", "Comprobaciones juzgadas cumplidas", describe_rate(metrics["ACC-2"]["judged"]), None)
    for metric_id in ("ACC-3", "REL-3"):
        for behavior, entry in metrics[metric_id]["groups"].items():
            row(metric_id, f"{definitions[metric_id]['name']} ({behavior})", describe_rate(entry), None)
    rel4 = metrics["REL-4"]
    row("REL-4", definitions["REL-4"]["name"], f"n {rel4['n']}; mediana {number(rel4['median'])}; cuartiles {number(rel4['q1'])} y {number(rel4['q3'])}", None)
    grd2 = metrics["GRD-2"]
    row("GRD-2", definitions["GRD-2"]["name"], f"{grd2['total']} en total; casos criticos afectados: {', '.join(grd2['critical_failures']) or 'ninguno'}", grd2["target"])
    for metric_id in ("LAT-1", "LAT-2", "LAT-3"):
        for stage, entry in metrics[metric_id]["stages"].items():
            row(metric_id, f"{definitions[metric_id]['name']} ({stage}, n {entry['n']}, solo llamadas correctas)", f"{number(entry['value'])} ms", entry["target"])
    for stage, entry in metrics["LAT-4"]["stages"].items():
        row("LAT-4", f"{definitions['LAT-4']['name']} ({stage})", describe_rate(entry), None)
    str2 = metrics["STR-2"]
    row("STR-2", definitions["STR-2"]["name"], ", ".join(f"{name} {value}" for name, value in str2["by_category"].items() if value) or "sin fallos", None)
    lines += ["", f"La latencia se mide sobre un corpus de {run['corpus']['documents']} documentos y {run['corpus']['chunks']} fragmentos; no se compara con ejecuciones de otro tamano.", ""]
    if report["gaps"]:
        lines += ["Huecos del corpus (cobertura none, fuera de REL-2): " + ", ".join(report["gaps"]) + ".", ""]
    if report["critical"]["single_decider_cases"]:
        lines += ["Casos criticos con una sola persona decidiendo los puntos juzgados: " + ", ".join(report["critical"]["single_decider_cases"]) + ".", ""]
    lines += ["## Definiciones", "", "| Id | Familia | Numerador | Denominador | Poblacion | Fuente | Unidad |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for metric in catalogue["metrics"]:
        lines.append(
            f"| {metric['id']} | {metric['family']} | {metric['numerator']} | {metric['denominator']} | {metric['population']} | {metric['source']} | {metric['unit']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calculador de referencia de las metricas tecnicas del asistente (JUP-067).")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--generated-at", help="marca de tiempo del informe; fija el resultado para repetirlo")
    args = parser.parse_args(argv)
    try:
        catalogue = load_catalogue()
        validate_catalogue(catalogue)
        bank, labels = load_json(BANK_PATH), load_json(LABELS_PATH)
        try:
            results = load_json(args.results)
        except (OSError, ValueError):
            fail("results", "the file cannot be read as JSON")
        report = compute(results, bank, labels, catalogue)
    except (CatalogueError, ResultsError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    report["generated_at"] = args.generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    document = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    markdown = render_markdown(report, catalogue)
    if args.output:
        args.output.write_text(document, encoding="utf8", newline="\n")
    if args.report:
        args.report.write_text(markdown, encoding="utf8", newline="\n")
    if not args.output and not args.report:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
