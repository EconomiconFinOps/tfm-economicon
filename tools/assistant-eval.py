"""Evaluation of the assistant chat answers against the question bank (JUP-070).

It collects the answers of a running chat, decides by rule what can be checked
objectively (figures and prohibited behaviours), leaves the rest to people, and
writes the results file that the reference calculator (JUP-067) already accepts.
The raw run, the review sheet and the judgements carry text and live outside Git;
the results file carries none. Standard library only, deterministic.
Usage and method: docs/validation/JUP-070-evaluation.md
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import socket
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import namedtuple
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK_PATH = ROOT / "docs" / "validation" / "JUP-069-questions.json"
RULES_PATH = ROOT / "docs" / "validation" / "JUP-070-evaluation-rules.json"
METRICS_PATH = ROOT / "tools" / "assistant-metrics.py"

Figure = namedtuple("Figure", "value unit start end")
CURRENCIES = ("eur", "usd")
NEGATORS = re.compile(r"(?<!\w)(no|ni|tampoco|nunca|jamas|evit\w+|nadie)(?!\w)")
NUMBER = re.compile(r"(?<![\w.,\-])(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?![\w]|[.,]\d)")
PERCENT = re.compile(r"^\s*(?:%|por ciento|puntos? porcentuales?|pp\b)")
CURRENCY = re.compile(r"^\s*(eur\b|euros?\b|usd\b|dolares?\b|[€$])")
PERIOD = re.compile(r"^\s*(?:/|\bal\b|\bpor\b|\bcada\b)\s*(dia|mes|pedido)\b|^\s*(diarios?|mensuales?)")
PREFIX_CURRENCY = re.compile(r"([€$])\s*$")
SENTENCE_BREAK = re.compile(r"(?<=[.!?;])\s+|\s*\n+\s*")
FAILURE_BY_STATUS = {401: "authentication", 403: "authentication", 429: "rate_limit"}
INFRA_STAGE = "embedding"
RAW_VERSION = 1
MAX_REVIEWERS = 2


class EvaluationError(Exception):
    pass


def load_metrics():
    spec = importlib.util.spec_from_file_location("economicon_assistant_metrics_for_eval_tool", METRICS_PATH)
    if spec is None or spec.loader is None:
        raise EvaluationError("no se puede cargar tools/assistant-metrics.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CALIBRATION_PATH = ROOT / "tools" / "retrieval-calibration.py"
CORPUS_DIR = ROOT / "docs" / "assistant-corpus"


def load_calibration():
    spec = importlib.util.spec_from_file_location("economicon_retrieval_calibration_for_eval", CALIBRATION_PATH)
    if spec is None or spec.loader is None:
        raise EvaluationError("no se puede cargar tools/retrieval-calibration.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def corpus_file(path: str) -> Path:
    target = (ROOT / path).resolve()
    if CORPUS_DIR.resolve() not in target.parents or target.suffix != ".md":
        raise EvaluationError(f"{path}: solo se admiten documentos Markdown del corpus del asistente")
    return target


def label_fragments(fragments: list[dict], document_map: dict, chunk_size: int, chunk_overlap: int) -> list[dict]:
    """Source key of the bank and section of each retrieved chunk, from the document it was cut from."""
    calibration = load_calibration()
    bank = read_json(BANK_PATH)
    keys = {item["path"]: name for name, item in bank["sources"].items()}
    cache: dict[str, tuple] = {}
    labelled = []
    for fragment in fragments:
        item = dict(fragment)
        document, _, index = item["chunk_id"].partition(":chunk:")
        path = document_map.get(document)
        if path is not None and index.isdigit():
            file = corpus_file(path)
            if path not in cache:
                text = file.read_text(encoding="utf-8")
                cache[path] = (calibration.chunk_spans(text, chunk_size, chunk_overlap), calibration.section_spans(text))
            spans, sections = cache[path]
            if int(index) < len(spans):
                _, start, end = spans[int(index)]
                item["source"] = keys.get(path, file.stem)
                item["heading"] = calibration.primary_section(sections, start, end) or ""
        labelled.append(item)
    return labelled


def normalize(text: str) -> str:
    folded = unicodedata.normalize("NFD", text)
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", folded.casefold()).strip()


def split_sentences(text: str) -> list[str]:
    parts = (normalize(part).rstrip(".!?; ") for part in SENTENCE_BREAK.split(text))
    return [part for part in parts if part]


def parse_number_token(token: str) -> Decimal | None:
    separators = [char for char in token if char in ".,"]
    if not separators:
        digits = token
    elif "." in token and "," in token:
        decimal = token[max(token.rfind("."), token.rfind(","))]
        other = "," if decimal == "." else "."
        digits = token.replace(other, "").replace(decimal, ".")
    elif len(separators) > 1:
        digits = token.replace(separators[0], "")
    else:
        head, tail = token.split(separators[0])
        thousands = len(tail) == 3 and 1 <= len(head) <= 3 and head != "0"
        digits = head + tail if thousands else head + "." + tail
    try:
        return Decimal(digits)
    except InvalidOperation:
        return None


def unit_key(unit: str) -> str:
    return normalize(unit)


def parse_figures(sentence: str) -> list[Figure]:
    figures = []
    for match in NUMBER.finditer(sentence):
        value = parse_number_token(match.group(1))
        if value is None:
            continue
        rest = sentence[match.end():]
        unit = None
        end = match.end()
        percent = PERCENT.match(rest)
        currency = CURRENCY.match(rest)
        if percent:
            unit, end = "%", match.end() + percent.end()
        elif currency:
            word = currency.group(1)
            unit = "usd" if word.startswith(("usd", "dolar", "$")) else "eur"
            end = match.end() + currency.end()
            period = PERIOD.match(sentence[end:])
            if period:
                unit += "/" + (period.group(1) or ("dia" if period.group(2).startswith("diar") else "mes"))
                end += period.end()
        else:
            prefix = PREFIX_CURRENCY.search(sentence[:match.start()])
            if prefix:
                unit = "usd" if prefix.group(1) == "$" else "eur"
        if unit is not None:
            figures.append(Figure(value, unit, match.start(), end))
    return figures


def numbers_in(text: str) -> set[Decimal]:
    values = set()
    for match in NUMBER.finditer(normalize(text)):
        value = parse_number_token(match.group(1))
        if value is not None:
            values.add(value)
    return values


def has_alias(sentence: str, alias: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(normalize(alias)) + r"(?!\w)", sentence) is not None


def is_echo(sentence: str, normalized_prompt: str) -> bool:
    """A sentence copied from the prompt (with or without a leading label) is not an answer."""
    candidates = {sentence, re.sub(r"^[^:]{1,20}:\s*", "", sentence)}
    for item in candidates:
        if len(item) < 12:
            continue
        # A question repeated as a statement ("el gasto es cero") is an assertion, not an echo.
        for match in re.finditer(re.escape(item), normalized_prompt):
            if item.startswith("¿") or match.start() == 0 or normalized_prompt[match.start() - 1] != "¿":
                return True
    return False


def answer_sentences(response: str, prompt: str) -> list[str]:
    normalized = normalize(prompt)
    return [sentence for sentence in split_sentences(response) if not is_echo(sentence, normalized)] if prompt else split_sentences(response)


def check_number(response: str, spec: dict, aliases: list[str], prompt: str = "") -> bool:
    wanted, tolerance = Decimal(str(spec["value"])), Decimal(str(spec["tolerance"]))
    unit = unit_key(spec["unit"])
    for sentence in answer_sentences(response, prompt):
        if not any(has_alias(sentence, alias) for alias in aliases):
            continue
        for figure in parse_figures(sentence):
            if figure.unit == unit and abs(figure.value - wanted) <= tolerance:
                return True
    return False


def negated(sentence: str, start: int, end: int) -> bool:
    return NEGATORS.search(sentence[max(0, start - 40):end]) is not None


def alternative_hits(alt: dict, sentence: str, prompt_numbers: set[Decimal]):
    kind = alt["kind"]
    if kind == "pattern":
        for match in re.finditer(alt["pattern"], sentence):
            yield match.start(), match.end()
    elif kind == "figure":
        wanted, tolerance = Decimal(str(alt["value"])), Decimal(str(alt["tolerance"]))
        if "context" in alt and not re.search(alt["context"], sentence):
            return
        for figure in parse_figures(sentence):
            if figure.unit == unit_key(alt["unit"]) and abs(figure.value - wanted) <= tolerance:
                yield figure.start, figure.end
    elif kind == "amount_not_in_prompt":
        for figure in parse_figures(sentence):
            if figure.unit.split("/")[0] in CURRENCIES and figure.value not in prompt_numbers:
                yield figure.start, figure.end
    else:
        raise EvaluationError(f"tipo de regla desconocido: {kind}")


def rule_hits(rule: dict, response: str, prompt: str) -> bool:
    exempt = re.compile(rule["exempt"]) if rule.get("exempt") else None
    check_negation = rule.get("negation", True)
    prompt_numbers = numbers_in(prompt)
    for sentence in answer_sentences(response, prompt):
        for alt in rule["any"]:
            for start, end in alternative_hits(alt, sentence, prompt_numbers):
                if exempt and exempt.search(sentence):
                    continue
                if check_negation and negated(sentence, start, end):
                    continue
                return True
    return False


def prompt_text(case: dict) -> str:
    return case["context"] + "\n" + case["question"]


def load_rules(path: Path = RULES_PATH) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise EvaluationError(f"no se puede leer el fichero de reglas: {error}") from None


def validate_rules(rules: dict, bank: dict) -> None:
    for name in ("rules_version", "aliases", "forbidden", "acceptance"):
        if name not in rules:
            raise EvaluationError(f"el fichero de reglas no tiene «{name}»")
    cases = {case["id"]: case for case in bank["cases"]}
    for case_id, case in cases.items():
        for position in range(1, len(case["expected"]["forbidden"]) + 1):
            rule = rules["forbidden"].get(case_id, {}).get(str(position))
            if not rule or not rule.get("any"):
                raise EvaluationError(f"falta la regla de la conducta prohibida {position} del caso {case_id}")
            for alt in rule["any"]:
                if alt.get("kind") == "pattern":
                    try:
                        re.compile(alt["pattern"])
                    except re.error as error:
                        raise EvaluationError(f"patrón inválido en {case_id} item {position}: {error}") from None
        for position in range(1, len(case["expected"].get("numbers", [])) + 1):
            if not rules["aliases"].get(case_id, {}).get(str(position)):
                raise EvaluationError(f"faltan alias de la cifra {position} del caso {case_id}")
    for case_id, items in rules["forbidden"].items():
        if case_id not in cases:
            raise EvaluationError(f"regla de un caso que no está en la batería: {case_id}")
        if set(items) - {str(n) for n in range(1, len(cases[case_id]["expected"]["forbidden"]) + 1)}:
            raise EvaluationError(f"regla de una conducta que no existe en {case_id}")


def classify_figures(answer: str, case: dict, retrieved: list[dict]) -> list[dict]:
    question, context = numbers_in(case["question"]), numbers_in(case["context"])
    evidence: set[Decimal] = set()
    for item in retrieved:
        evidence |= numbers_in(item.get("content", ""))
    derived = [(Decimal(str(n["value"])), Decimal(str(n["tolerance"]))) for n in case["expected"].get("numbers", [])]
    found = []
    for sentence in split_sentences(answer):
        for figure in parse_figures(sentence):
            if figure.value in question:
                origin = "question"
            elif figure.value in context:
                origin = "context"
            elif figure.value in evidence:
                origin = "evidence"
            elif any(abs(figure.value - value) <= tolerance for value, tolerance in derived):
                origin = "context"
            else:
                origin = "untraceable"
            found.append({"origin": origin})
    return found


def blank_entry(case_id: str, outcome: str) -> dict:
    return {
        "case": case_id, "outcome": outcome, "checks": [], "retrieved": [], "citations": [], "figures": [],
        "latency_ms": {}, "failure_category": None, "failure_stage": None, "structured_ok": None,
        "evidence_refs": {"total": 0, "dangling": 0},
    }


def reviewers_of(verdicts: list[dict]) -> list[str]:
    return sorted({item["reviewer"].strip() for item in verdicts if item.get("reviewer", "").strip()})


def score_case(case: dict, raw: dict | None, judgments: dict, rules: dict, *, provisional: bool = False):
    case_id = case["id"]
    analysis = {"reason": None, "disagreements": [], "single_decider": False, "objective_failures": []}
    if raw is None:
        analysis["reason"] = "el caso no está en la ejecución cruda"
        return blank_entry(case_id, "not_run"), analysis
    if raw.get("failure_category"):
        entry = blank_entry(case_id, "blocked")
        entry["failure_category"], entry["failure_stage"] = raw["failure_category"], INFRA_STAGE
        analysis["reason"] = f"fallo de infraestructura: {raw['failure_category']}"
        return entry, analysis
    expected = case["expected"]
    critical = bool(expected.get("numbers"))
    prompt = prompt_text(case)
    checks = []
    for position, spec in enumerate(expected.get("numbers", []), start=1):
        aliases = rules["aliases"][case_id].get(str(position)) or [spec["label"]]
        passed = check_number(raw["answer"], spec, aliases, prompt)
        checks.append({"id": f"numbers-{position}", "class": "objective", "result": "pass" if passed else "fail", "decided_by": ["rule"]})
    for position in range(1, len(expected["forbidden"]) + 1):
        violated = rule_hits(rules["forbidden"][case_id][str(position)], raw["answer"], prompt)
        checks.append({"id": f"forbidden-{position}", "class": "objective", "result": "fail" if violated else "pass", "decided_by": ["rule"]})
    needed = 2 if critical and not provisional else 1
    judged = []
    for position in range(1, len(expected["required"]) + 1):
        check_id = f"required-{position}"
        verdicts = judgments.get(check_id, [])
        people = reviewers_of(verdicts)
        if len(people) > MAX_REVIEWERS:
            raise EvaluationError(f"{case_id} {check_id}: más de {MAX_REVIEWERS} revisores")
        if len(people) < needed:
            analysis["reason"] = f"faltan juicios de {check_id}: {len(people)} revisor(es) distinto(s) y hacen falta {needed}"
            return blank_entry(case_id, "not_run"), analysis
        results = {item["result"] for item in verdicts}
        if not results <= {"pass", "fail"}:
            raise EvaluationError(f"{case_id} {check_id}: el resultado de un juicio debe ser pass o fail")
        if len(results) > 1:
            analysis["disagreements"].append(check_id)
        if critical and len(people) < 2:
            analysis["single_decider"] = True
        judged.append({"id": check_id, "class": "judged", "result": "pass" if results == {"pass"} else "fail", "decided_by": people})
    checks.extend(judged)
    retrieved = [{"chunk_id": item["chunk_id"], "source": item["source"], "heading": item.get("heading") or "", "distance": item["distance"]}
                 for item in raw["retrieved"]]
    figures = classify_figures(raw["answer"], case, raw["retrieved"])
    untraceable = critical and any(item["origin"] == "untraceable" for item in figures)
    failed = [check["id"] for check in checks if check["result"] == "fail"]
    analysis["objective_failures"] = [i for i in failed if i.startswith(("numbers-", "forbidden-"))]
    total = raw["total_ms"]
    entry = blank_entry(case_id, "fail" if failed or untraceable else "pass")
    citations = [str(item) for item in raw["citations"]]
    ids = {item["chunk_id"] for item in raw["retrieved"]}
    entry.update({
        "checks": checks, "retrieved": retrieved, "citations": citations, "figures": figures, "structured_ok": True,
        "latency_ms": {"embedding": 0, "retrieval": 0, "generation": total, "total": total},
        "evidence_refs": {"total": len(citations), "dangling": sum(1 for item in citations if item not in ids)},
    })
    return entry, analysis


def build_results(bank: dict, rules: dict, raw: dict, judgments: dict, run_info: dict, *, provisional: bool, document_map: dict | None = None):
    metrics = load_metrics()
    validate_rules(rules, bank)
    raw_cases = {item["case"]: item for item in raw["cases"]}
    if document_map:
        retrieval = run_info["retrieval"]
        raw_cases = {case_id: {**item, "retrieved": label_fragments(item["retrieved"], document_map, retrieval["chunk_size"], retrieval["chunk_overlap"])}
                     for case_id, item in raw_cases.items()}
    entries, analysis = [], {"provisional": provisional, "single_decider_cases": [], "not_run": [], "blocked": [], "disagreements": {}, "reasons": {}}
    for case in bank["cases"]:
        entry, detail = score_case(case, raw_cases.get(case["id"]), judgments.get(case["id"], {}), rules, provisional=provisional)
        entries.append(entry)
        if entry["outcome"] == "not_run":
            analysis["not_run"].append(case["id"])
        if entry["outcome"] == "blocked":
            analysis["blocked"].append(case["id"])
        if detail["single_decider"]:
            analysis["single_decider_cases"].append(case["id"])
        if detail["disagreements"]:
            analysis["disagreements"][case["id"]] = detail["disagreements"]
        if detail["reason"]:
            analysis["reasons"][case["id"]] = detail["reason"]
    run = {
        "commit": run_info["commit"], "date": run_info["date"],
        "bank": {"suite_version": bank["suite_version"], "suite_sha256": metrics.suite_digest(bank)},
        "corpus": run_info["corpus"], "provider": run_info["provider"], "alias": run_info["alias"],
        "retrieval": run_info["retrieval"], "generation": run_info["generation"],
        "availability": {"requests": sum(item.get("requests", 0) for item in raw["cases"]),
                         "server_errors": sum(item.get("server_errors", 0) for item in raw["cases"])},
    }
    results = {"results_version": 1, "catalogue_version": metrics.load_catalogue()["catalogue_version"], "synthetic": False, "run": run, "cases": entries}
    return results, analysis


def verdict(report: dict, rules: dict) -> dict:
    def compare(comparator: str, value, target) -> bool:
        return {">=": value >= target, "<=": value <= target, "==": value == target}[comparator]

    unstructured = set(rules["acceptance"]["not_applicable_when_unstructured"])
    items, reasons = [], []

    def add(metric, label, status, detail):
        items.append({"metric": metric, "label": label, "status": status, "detail": detail})
        if status in ("unmet", "not_available"):
            reasons.append(f"{metric}: {detail}")

    for metric, block in report["metrics"].items():
        targets = []
        if block.get("target"):
            targets.append((metric, block["target"], block.get("available", True)))
        for stage, value in (block.get("stages") or {}).items():
            if value.get("target"):
                targets.append((f"{metric} ({stage})", value["target"], value.get("n", 0) > 0))
        for label, target, available in targets:
            description = f"{target['comparator']} {target['value']}"
            if target["met"] is None:
                if metric in unstructured:
                    add(metric, label, "not_applicable", f"{description}; el chat no devuelve salida estructurada")
                else:
                    add(metric, label, "not_available", f"{description} no se puede calcular")
            else:
                add(metric, label, "met" if target["met"] else "unmet", f"{description}" + ("" if target["met"] else " no se cumple"))
    for extra in rules["acceptance"]["extra"]:
        block = report["metrics"].get(extra["metric"], {})
        description = f"{extra['comparator']} {extra['value']} ({extra.get('origin', 'JUP-070')})"
        if not block.get("available") or block.get("rate") is None:
            add(extra["metric"], extra["metric"], "not_available", f"{description} no se puede calcular")
        else:
            met = compare(extra["comparator"], block["rate"], extra["value"])
            add(extra["metric"], extra["metric"], "met" if met else "unmet", f"{description}: medido {block['rate']}")
    return {"accepted": all(item["status"] in ("met", "not_applicable") for item in items) and bool(items), "thresholds": items, "reasons": reasons}


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def outside_repository(path: Path) -> bool:
    target = Path(path).resolve()
    return target != ROOT and ROOT not in target.parents


def write_private(path: Path, value) -> None:
    if not outside_repository(path):
        raise EvaluationError(f"{path}: este fichero lleva texto de respuestas y no puede escribirse dentro del repositorio")
    Path(path).write_text(value if isinstance(value, str) else dumps(value), encoding="utf-8")


def request(opener, url: str, body: dict | None, headers: dict, timeout: float):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST")
    with opener.open(req, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def failure_of(error: Exception) -> tuple[int | None, str]:
    if isinstance(error, urllib.error.HTTPError):
        status = error.code
        if status in FAILURE_BY_STATUS:
            return status, FAILURE_BY_STATUS[status]
        return status, "upstream" if status >= 500 else "request"
    reason = getattr(error, "reason", error)
    if isinstance(error, (TimeoutError, socket.timeout)) or isinstance(reason, (TimeoutError, socket.timeout)):
        return None, "timeout"
    return None, "connection"


def collect_cases(base_url: str, email: str, password: str, tenant: str, inputs: dict, *, timeout: float = 60, opener=None) -> dict:
    opener = opener or urllib.request.build_opener()
    base = base_url.rstrip("/")
    if not base.startswith(("http://", "https://")):
        raise EvaluationError("--base-url debe empezar por http:// o https://")
    try:
        _, login = request(opener, base + "/auth/login", {"email": email, "password": password}, {}, timeout)
        token = login["access_token"]
    except (urllib.error.URLError, OSError, KeyError, ValueError) as error:
        raise EvaluationError(f"no se pudo iniciar sesión en {base}: {type(error).__name__}") from None
    headers = {"Authorization": "Bearer " + token, "X-Tenant-Id": tenant}
    cases = []
    for item in inputs["cases"]:
        entry = {"case": item["id"], "prompt": item["prompt"], "status": None, "failure_category": None, "total_ms": None,
                 "answer": "", "citations": [], "retrieved": [], "requests": 0, "server_errors": 0}
        started = time.perf_counter()
        try:
            entry["requests"] += 1
            _, conversation = request(opener, base + "/assistant/conversations", {"title": f"evaluacion {item['id']}"}, headers, timeout)
            entry["requests"] += 1
            started = time.perf_counter()
            status, reply = request(opener, f"{base}/assistant/conversations/{conversation['id']}/messages", {"content": item["prompt"]}, headers, timeout)
            entry["total_ms"] = round((time.perf_counter() - started) * 1000, 3)
            entry["status"] = status
            message = reply["assistant_message"]
            if not isinstance(message.get("content"), str) or not isinstance(reply.get("retrieved_context"), list):
                raise ValueError("invalid reply")
            sections = {c.get("evidence_id"): c.get("section") for c in message.get("metadata", {}).get("source_citations", [])}
            entry["answer"] = message["content"]
            entry["citations"] = [str(c) for c in message.get("metadata", {}).get("citations", [])]
            entry["retrieved"] = [{"chunk_id": r["chunk_id"], "source": r["source"], "heading": sections.get(r["chunk_id"]) or "",
                                   "distance": r["distance"], "content": r.get("content", "")} for r in reply.get("retrieved_context", [])]
        except (urllib.error.URLError, OSError, ValueError, KeyError) as error:
            status, category = failure_of(error)
            if isinstance(error, urllib.error.HTTPError):
                error.close()
            entry["status"], entry["failure_category"], entry["total_ms"] = status, category, None
            if status is not None and status >= 500:
                entry["server_errors"] += 1
        cases.append(entry)
    return {"raw_version": RAW_VERSION, "base_url": base, "tenant": tenant, "cases": cases}


def review_sheet(bank: dict, raw: dict) -> str:
    raw_cases = {item["case"]: item for item in raw["cases"]}
    lines = ["# Hoja de revisión (JUP-070)", "",
             "Fuera de Git. Para cada punto `required-N`, pass o fail con tu nombre; los casos críticos (los que tienen cifras) los juzgan dos personas por separado. "
             "Las cifras y las prohibiciones las decide la regla; si ves una violación que la regla no detectó, falla el punto `required` correspondiente y anota por qué.", ""]
    for case in bank["cases"]:
        item = raw_cases.get(case["id"], {})
        lines += [f"## {case['id']} · {case['category']} · {case['behavior']}", "", f"**Pregunta:** {case['question']}", "",
                  f"**Contexto:** {case['context']}", "", "**Puntos requeridos**", ""]
        lines += [f"- `required-{n}`: {text}" for n, text in enumerate(case["expected"]["required"], start=1)]
        lines += ["", "**Conductas prohibidas** (las decide la regla)", ""]
        lines += [f"- `forbidden-{n}`: {text}" for n, text in enumerate(case["expected"]["forbidden"], start=1)]
        lines += ["", "**Respuesta original**", "", "```text", item.get("answer", "(sin respuesta)"), "```", ""]
        lines += [f"**Citas:** {', '.join(item.get('citations', [])) or 'ninguna'}", ""]
        for fragment in item.get("retrieved", []):
            lines += [f"- Fragmento `{fragment['chunk_id']}` ({fragment['source']}, distancia {fragment['distance']})"]
        lines += [""]
    return "\n".join(lines)


def compare_reports(paths: list[Path]) -> str:
    reports = [(path.stem, json.loads(Path(path).read_text(encoding="utf-8"))) for path in paths]
    names = [name for name, _ in reports]
    lines = ["Métrica | " + " | ".join(names) + " | variación (máx − mín)"]
    for metric in sorted({m for _, report in reports for m in report["metrics"]}):
        values = []
        for _, report in reports:
            block = report["metrics"].get(metric, {})
            values.append(block.get("rate") if block.get("available") else None)
        numeric = [value for value in values if value is not None]
        if not numeric:
            continue
        spread = round(max(numeric) - min(numeric), 6)
        lines.append(f"{metric} | " + " | ".join("no disponible" if value is None else str(value) for value in values) + f" | {spread}")
    lines.append("Las ejecuciones se publican todas; no se sustituye una mala por otra mejor.")
    return "\n".join(lines) + "\n"


def render_report(base_report: str, result: dict, analysis: dict) -> str:
    lines = [base_report.rstrip("\n"), "", "## Evaluación de las respuestas (JUP-070)", "",
             f"**Veredicto: {'Aceptado' if result['accepted'] else 'No aceptado'}**", ""]
    if analysis["provisional"]:
        lines += ["Medición **provisional**: los casos críticos con un solo revisor se listan abajo.", ""]
    lines += ["| Umbral | Estado | Detalle |", "| --- | --- | --- |"]
    lines += [f"| {item['label']} | {item['status']} | {item['detail']} |" for item in result["thresholds"]]
    lines += ["", f"- Casos no ejecutados (`not_run`): {', '.join(analysis['not_run']) or 'ninguno'}",
              f"- Casos bloqueados por infraestructura: {', '.join(analysis['blocked']) or 'ninguno'}",
              f"- Casos críticos con un solo decisor: {', '.join(analysis['single_decider_cases']) or 'ninguno'}",
              f"- Discrepancias entre revisores: {', '.join(f'{c} ({', '.join(p)})' for c, p in analysis['disagreements'].items()) or 'ninguna'}"]
    return "\n".join(lines) + "\n"


def read_json(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise EvaluationError(f"no se puede leer {path}: {error}") from None


def run_collect(args) -> int:
    password = os.environ.get(args.password_env)
    if not password:
        raise EvaluationError(f"falta la variable de entorno {args.password_env}")
    if not outside_repository(args.output):
        raise EvaluationError(f"{args.output}: el fichero crudo lleva texto y debe quedar fuera del repositorio")
    raw = collect_cases(args.base_url, args.email, password, args.tenant, read_json(args.inputs), timeout=args.timeout)
    write_private(args.output, raw)
    blocked = sum(1 for item in raw["cases"] if item["failure_category"])
    print(f"Recogidos {len(raw['cases'])} casos ({blocked} bloqueados por infraestructura).")
    return 0


def run_review_sheet(args) -> int:
    bank = read_json(BANK_PATH)
    write_private(args.output, review_sheet(bank, read_json(args.raw)))
    print(f"Hoja de revisión escrita ({len(bank['cases'])} casos).")
    return 0


def run_score(args) -> int:
    metrics = load_metrics()
    bank, rules = read_json(BANK_PATH), load_rules(args.rules)
    validate_rules(rules, bank)
    judgments = read_json(args.judgments).get("cases", {})
    document_map = read_json(args.document_map) if args.document_map else None
    results, analysis = build_results(bank, rules, read_json(args.raw), judgments, read_json(args.run_info), provisional=args.provisional, document_map=document_map)
    labels = read_json(ROOT / "docs" / "validation" / "JUP-022-retrieval-labels.json")
    catalogue = metrics.load_catalogue()
    report = metrics.compute(results, bank, labels, catalogue)
    result = verdict(report, rules)
    if args.generated_at:
        report["generated_at"] = args.generated_at
    Path(args.output).write_text(dumps(results), encoding="utf-8")
    Path(args.report).write_text(render_report(metrics.render_markdown(report, catalogue), result, analysis), encoding="utf-8")
    if args.report_json:
        Path(args.report_json).write_text(dumps(report), encoding="utf-8")
    print(f"Veredicto: {'Aceptado' if result['accepted'] else 'No aceptado'}")
    for reason in result["reasons"]:
        print(f"- {reason}")
    return 0


def run_compare(args) -> int:
    sys.stdout.write(compare_reports(args.reports))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Evaluación de las respuestas del chat frente a la batería (JUP-070).")
    commands = root.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect")
    collect.add_argument("--base-url", default="http://localhost:8000")
    collect.add_argument("--email", default="operator@example.com")
    collect.add_argument("--password-env", default="DEMO_PASSWORD")
    collect.add_argument("--tenant", required=True)
    collect.add_argument("--inputs", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--timeout", type=float, default=60)
    collect.set_defaults(run=run_collect)
    sheet = commands.add_parser("review-sheet")
    sheet.add_argument("--raw", type=Path, required=True)
    sheet.add_argument("--output", type=Path, required=True)
    sheet.set_defaults(run=run_review_sheet)
    score = commands.add_parser("score")
    score.add_argument("--raw", type=Path, required=True)
    score.add_argument("--judgments", type=Path, required=True)
    score.add_argument("--run-info", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--report", type=Path, required=True)
    score.add_argument("--report-json", type=Path, help="informe del calculador en JSON, para compare")
    score.add_argument("--rules", type=Path, default=RULES_PATH)
    score.add_argument("--provisional", action="store_true")
    score.add_argument("--document-map", type=Path, help="JSON {id del documento: ruta del corpus} para etiquetar fuente y seccion de los fragmentos")
    score.add_argument("--generated-at")
    score.set_defaults(run=run_score)
    compare = commands.add_parser("compare")
    compare.add_argument("reports", type=Path, nargs="+")
    compare.set_defaults(run=run_compare)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.run(args)
    except EvaluationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # the message could carry a response or a header
        print(f"Error: {type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
