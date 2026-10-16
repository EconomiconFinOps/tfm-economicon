#!/usr/bin/env python3
"""JUP-071: paired robustness experiments, without an automatic semantic judge.

Python 3.12+, standard library only. Raw answers and human judgments stay outside
the repository. JUP-070 owns transport, prompt formatting and numeric matching.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "docs/validation/JUP-071-robustness-cases.json"
BASELINE = ROOT / "docs/validation/JUP-069-questions.json"
SERVICE = ROOT / "apps/backend/app/services/assistant.py"
TEMPLATE_SHA256 = "e8335a95cdf477dd8057d5ef94c3137ac6c0727248241fc03b44bba645403516"
OUTCOMES = ("pass", "fail", "blocked", "not_run")
KINDS = ("template_mock", "live_unverified")
# Collectors (JUP-123) may export corpus fragments with `distance: null` when the server reports none.
ACCEPTS_UNMEASURED_DISTANCE = True


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


evaluation = module("jup071_evaluation", ROOT / "tools/assistant-eval.py")
Error = evaluation.EvaluationError


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    # Repository text identity is independent of Git's Windows CRLF conversion.
    return hashlib.sha256(Path(path).read_text(encoding="utf-8").encode()).hexdigest()


def read(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), "JSON root must be an object")
    return value


def require(condition, message):
    if not condition:
        raise Error(message)


def finite(value):
    """A finite JSON number; booleans and integers too large for a float are not."""
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def text_list(value):
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def validate(suite, baseline):
    require(type(suite.get("schema_version")) is int and suite["schema_version"] == 1 and suite.get("jup") == "JUP-071", "invalid JUP-071 suite")
    for block, keys in (("baseline", ("path", "suite_version", "sha256")), ("methodology", ("path", "sha256"))):
        require(isinstance(suite.get(block), dict) and all(isinstance(suite[block].get(k), str) for k in keys), f"invalid {block} reference")
    require(isinstance(suite.get("sources"), dict) and isinstance(baseline.get("sources"), dict), "invalid sources reference")
    require(suite["baseline"]["path"] == BASELINE.relative_to(ROOT).as_posix(), "unexpected baseline path")
    require(suite["baseline"]["sha256"] == file_digest(BASELINE), "JUP-069 baseline changed; review the pairs")
    require(suite["baseline"]["suite_version"] == baseline["suite_version"], "baseline version mismatch")
    require(suite["methodology"]["path"] == "docs/validation/JUP-070-evaluation.md" and
            suite["methodology"]["sha256"] == file_digest(ROOT / suite["methodology"]["path"]), "JUP-070 methodology changed; review the protocol")
    require(suite["sources"] == baseline["sources"], "source references differ from JUP-069")
    for source in suite["sources"].values():
        require(file_digest(ROOT / source["path"]) == source["sha256"], "corpus source changed; review the suite")
    base_ids = {c["id"] for c in baseline["cases"]}
    ids = set()
    require(isinstance(suite.get("cases"), list) and len(suite["cases"]) >= 16, "at least 16 perturbations are required")
    require(all(isinstance(c, dict) for c in suite["cases"]), "every case must be an object")
    require(isinstance(suite.get("suite_version"), str) and re.fullmatch(r"\d+\.\d+\.\d+", suite["suite_version"]), "invalid suite version")
    for position, case in enumerate(suite["cases"], 1):
        label = case["id"] if isinstance(case.get("id"), str) else f"case #{position}"
        for key in ("id", "baseline_id", "expected_behavior", "risk", "question", "context", "category", "perturbation"):
            require(isinstance(case.get(key), str), f"{label}: missing or invalid {key}")
        for key in ("required_points", "forbidden_behaviors", "sources", "expected_numbers"):
            require(isinstance(case.get(key), list), f"{label}: missing or invalid {key}")
    require({c["expected_behavior"] for c in suite["cases"]} >= {"answer", "clarify", "abstain"}, "missing behavior controls")
    for case in suite["cases"]:
        cid = case["id"]
        require(re.fullmatch(r"JUP-071-\d{3}", cid) and cid not in ids, "invalid or duplicate case ID")
        ids.add(cid)
        require(case["baseline_id"] in base_ids, f"{cid}: unknown baseline")
        require(case["risk"] in ("critical", "standard"), f"{cid}: invalid risk")
        require(case["expected_behavior"] in ("answer", "clarify", "abstain"), f"{cid}: invalid behavior")
        for key in ("question", "context", "category", "perturbation"):
            require(isinstance(case[key], str) and case[key].strip(), f"{cid}: missing {key}")
        for key in ("required_points", "forbidden_behaviors", "sources"):
            require(text_list(case[key]), f"{cid}: empty {key}")
        require(set(case["sources"]) <= set(suite["sources"]), f"{cid}: unknown source")
        require(isinstance(case["expected_numbers"], list), f"{cid}: invalid expected_numbers")
        require(not case["expected_numbers"] or case["risk"] == "critical", f"{cid}: cases with expected figures must be critical")
        for n in case["expected_numbers"]:
            require(isinstance(n, dict), f"{cid}: expected number must be an object")
            require("aliases" not in n or text_list(n["aliases"]), f"{cid}: invalid number aliases")
            folded = [evaluation.normalize(a) for a in n.get("aliases", [])]
            require(all(folded) and len(set(folded)) == len(folded), f"{cid}: aliases must be non-empty and unique after normalisation")
            require(isinstance(n.get("label"), str) and bool(n["label"].strip()) and
                    isinstance(n.get("unit"), str) and bool(n["unit"].strip()), f"{cid}: invalid number label/unit")
            for key in ("value", "tolerance"):
                require(finite(n.get(key)), f"{cid}: non-finite number")
            require(n["tolerance"] >= 0, f"{cid}: negative tolerance")


def load_suite():
    suite, baseline = read(SUITE), read(BASELINE)
    validate(suite, baseline)
    return suite, baseline


def campaign(suite, baseline):
    """Selected JUP-069 originals and their perturbations share one execution."""
    originals = {c["baseline_id"] for c in suite["cases"]}
    cases = [{**c, "group": "baseline", "baseline_id": c["id"], "risk": "critical"}
             for c in baseline["cases"] if c["id"] in originals]
    for case in suite["cases"]:
        cases.append({**case, "group": "perturbation", "behavior": case["expected_behavior"],
                      "expected": {"required": case["required_points"], "forbidden": case["forbidden_behaviors"],
                                   "numbers": case["expected_numbers"]}})
    return cases


def inputs_for(cases):
    # Never send expected answers, the rubric or classification to the chat.
    return {"cases": [{"id": c["id"], "prompt": evaluation.prompt_text(c)} for c in cases]}


def code_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, OSError):
        raise Error("cannot read the git commit of this tool") from None


def provenance(suite, kind, config):
    return {"kind": kind, "collected_at": datetime.now(timezone.utc).isoformat(),
            "harness_commit": code_commit(), "suite_sha256": digest(suite),
            "harness_sha256": digest({str(p.relative_to(ROOT)): file_digest(p) for p in
                                      (Path(__file__), ROOT / "tools/assistant-eval.py", evaluation.RULES_PATH)}),
            "python_version": sys.version.split()[0],
            "service_sha256": file_digest(SERVICE), "configuration_sha256": digest(config),
            "configuration": config, "model_execution_verified": False}


DECLARED_TEXT = re.compile(r"[a-z0-9][a-z0-9./-]{0,63}")
RUN_INFO_FIELDS = ("commit", "corpus", "provider", "alias", "retrieval", "generation")
RUN_INFO_KEY = re.compile(r"[a-z][a-z0-9_]{0,39}")
RUN_INFO_SECRET_KEY = re.compile(r"(^|_)(key|token|secret|password|passwd|bearer|auth)(_|$)")
DECLARED_COMMIT = re.compile(r"[0-9a-f]{7,40}")
SHA256_HEX = re.compile(r"[0-9a-f]{64}")
SECRET_SHAPED = re.compile(r"(^|[-./])(sk|pk|xox[a-z]?|gh[pousr]|akia|eyj|key|token|secret|bearer)([-./0-9]|$)|[a-z0-9]{24,}")


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]", "?", str(value))[:40]


def descriptive(value):
    """A short text or a flat object of short scalar values: no nested data, no credential-like keys."""
    if isinstance(value, str):
        return len(value) <= 128
    if not isinstance(value, dict) or len(value) > 16:
        return False
    for key, item in value.items():
        if not (isinstance(key, str) and RUN_INFO_KEY.fullmatch(key) and not RUN_INFO_SECRET_KEY.search(key)):
            return False
        if not (item is None or isinstance(item, bool) or finite(item) or (isinstance(item, str) and len(item) <= 128)):
            return False
    return True


def check_run_info(config):
    require(isinstance(config, dict) and all(k in config for k in RUN_INFO_FIELDS), "run-info requires the JUP-070 configuration fields")
    extra = sorted(safe_name(k) for k in set(config) - set(RUN_INFO_FIELDS))
    require(not extra, "run-info has unexpected fields: " + ", ".join(extra))
    if isinstance(config["generation"], dict):
        nested = sorted(safe_name(k) for k in set(config["generation"]) - {"model_alias", "temperature"})
        require(not nested, "run-info generation has unexpected fields: " + ", ".join(nested))
    for name in ("corpus", "retrieval"):
        require(descriptive(config[name]), f"run-info {name} must be a short text or a flat object of short values")


def declared_text(value, name):
    require(isinstance(value, str) and DECLARED_TEXT.fullmatch(value) and not SECRET_SHAPED.search(value), f"invalid run {name}")
    return value


def run_header(execution, suite, raw_sha256):
    """Header with the JUP-070 field names; hand-written metadata is validated and never proves a model ran."""
    if execution["kind"] == "template_mock":
        commit, provider, alias = execution["harness_commit"], "template", "none"
        generation = {"model_alias": "plantilla-sin-modelo", "temperature": None}
    else:
        config = execution["configuration"]
        require(isinstance(config, dict), "invalid run configuration")
        commit = config.get("commit")
        require(isinstance(commit, str) and DECLARED_COMMIT.fullmatch(commit), "invalid run commit")
        provider, alias = declared_text(config.get("provider"), "provider"), declared_text(config.get("alias"), "alias")
        declared = config.get("generation")
        if isinstance(declared, str):
            # The chat collector describes generation with one string; it names the model, not a measured temperature.
            declared = {"model_alias": declared, "temperature": None}
        require(isinstance(declared, dict), "invalid run generation")
        temperature = declared.get("temperature")
        require(temperature is None or finite(temperature), "invalid run temperature")
        generation = {"model_alias": declared_text(declared.get("model_alias"), "model alias"), "temperature": temperature}
    date = datetime.fromisoformat(execution["collected_at"]).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"run_id": f"JUP-071-{raw_sha256[:12]}", "commit": commit, "date": date, "provider": provider, "alias": alias,
            "suite_version": suite["suite_version"], "suite_sha256": execution["suite_sha256"], "generation": generation}


def offline(suite, cases, retrieval):
    require(file_digest(SERVICE) == TEMPLATE_SHA256, "service changed; review the offline adapter before executing it")
    service = module("jup071_assistant", SERVICE).AssistantService()
    config = {"retrieval": retrieval, "generation": "template", "network": False,
              "embedding": "none", "service_sha256": file_digest(SERVICE)}
    rows = []
    for case in cases:
        chunks = []
        if retrieval == "fixed":
            source = suite["sources"][case["sources"][0]]["path"]
            chunks = [{"chunk_id": "fixed-corpus-fragment", "source": source,
                       "content": (ROOT / source).read_text(encoding="utf-8")[:500], "distance": 0.0}]
        prompt = evaluation.prompt_text(case)
        reply = service.answer(prompt, chunks)
        rows.append({"case": case["id"], "prompt": prompt, "answer": reply["content"],
                     "citations": reply["citations"], "retrieved": chunks,
                     "failure_category": None, "total_ms": None})
    return {"raw_version": 1, "execution": provenance(suite, "template_mock", config), "cases": rows}


def human_checks(case):
    checks = {"behavior": f"La respuesta cumple el comportamiento {case['behavior']} para este caso."}
    checks.update({f"required-{n}": text for n, text in enumerate(case["expected"]["required"], 1)})
    checks.update({f"forbidden-{n}": "No incurre en: " + text for n, text in enumerate(case["expected"]["forbidden"], 1)})
    return checks


def utc_time(value):
    if not (isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T[0-9:.]+\+00:00", value, re.ASCII)):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def server_prompt(execution):
    """Prompt hash reported by the server through a collector (never attested): the shared hash, or why there is none.

    Returns None when the collection carries no server-reported list.
    """
    collection = execution.get("collection")
    require(collection is None or isinstance(collection, dict), "invalid collection data")
    reported = (collection or {}).get("server_reported")
    if reported is None:
        return None
    require(execution.get("kind") == "live_unverified", "server-reported provenance only applies to live collections")
    require(isinstance(reported, list) and all(isinstance(x, dict) and x.get("attested", False) is False for x in reported),
            "invalid server-reported provenance")
    hashes = [x.get("prompt_sha256") for x in reported]
    require(all(h is None or (isinstance(h, str) and SHA256_HEX.fullmatch(h)) for h in hashes), "invalid server-reported prompt hash")
    distinct = set(hashes)
    if not reported or distinct == {None}:
        return {"prompt_sha256": None, "state": "absent", "attested": False}
    if len(distinct) == 1:
        return {"prompt_sha256": hashes[0], "state": "single", "attested": False}
    return {"prompt_sha256": None, "state": "mixed", "attested": False}


def validate_raw(raw, suite, cases):
    require(isinstance(raw, dict) and raw.get("raw_version") == 1, "invalid raw version")
    execution = raw["execution"]
    require(execution["kind"] in KINDS, "unknown execution kind")
    require(execution["suite_sha256"] == digest(suite), "raw data belongs to a different suite")
    require(execution["configuration_sha256"] == digest(execution["configuration"]), "configuration hash mismatch")
    require(re.fullmatch(r"[0-9a-f]{40}", execution["harness_commit"]), "invalid harness commit")
    require(utc_time(execution["collected_at"]), "invalid UTC collection time")
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", execution["python_version"]), "invalid Python version")
    for key in ("service_sha256", "configuration_sha256", "harness_sha256"):
        require(re.fullmatch(r"[0-9a-f]{64}", execution[key]), "invalid provenance hash")
    run_header(execution, suite, digest(raw))
    server_prompt(execution)
    expected = {c["id"]: evaluation.prompt_text(c) for c in cases}
    seen = set()
    require(isinstance(raw.get("cases"), list), "raw cases must be a list")
    for row in raw["cases"]:
        require(isinstance(row, dict), "raw case must be an object")
        cid = row["case"]
        require(cid in expected and cid not in seen, "unknown or duplicate raw case")
        seen.add(cid)
        require(row["prompt"] == expected[cid], f"{cid}: prompt differs from versioned case")
        require(isinstance(row.get("answer"), str), f"{cid}: answer must be text")
        require(row.get("failure_category") in (None, "timeout", "connection", "authentication", "request", "upstream", "invalid_response", "rate_limit"), f"{cid}: invalid failure category")
        require(isinstance(row.get("citations"), list) and all(isinstance(x, str) for x in row["citations"]), f"{cid}: invalid citations")
        require(isinstance(row.get("retrieved"), list), f"{cid}: invalid fragments")
        for fragment in row["retrieved"]:
            require(isinstance(fragment, dict) and all(isinstance(fragment.get(k), str) for k in ("chunk_id", "source", "content")), f"{cid}: invalid fragment fields")
            require("distance" in fragment and (fragment["distance"] is None or finite(fragment["distance"])), f"{cid}: invalid distance")
        if "public_evidence" in row:
            evidence = row["public_evidence"]
            require(isinstance(evidence, list), f"{cid}: invalid public evidence")
            for item in evidence:
                require(isinstance(item, dict) and all(isinstance(item.get(k), str) and item[k] for k in ("id", "kind")), f"{cid}: invalid public evidence")
                require(all(isinstance(item.get(k, ""), str) for k in ("source", "content")), f"{cid}: invalid public evidence text")
                require(item.get("distance") is None or finite(item["distance"]), f"{cid}: invalid public evidence distance")
            require(len({x["id"] for x in evidence}) == len(evidence), f"{cid}: duplicate public evidence id")
        total = row.get("total_ms")
        require(total is None or (finite(total) and total >= 0), f"{cid}: invalid latency")


def judge(values, needed):
    require(isinstance(values, list), "judgments must be lists")
    people = set()
    verdicts = []
    for item in values:
        require(isinstance(item, dict) and isinstance(item.get("reviewer"), str), "missing reviewer")
        name = evaluation.normalize(item["reviewer"])
        require(name and name not in people, "duplicate or empty reviewer")
        people.add(name)
        require(item.get("result") in ("pass", "fail"), "judgment must be pass/fail")
        verdicts.append(item["result"])
    require(len(people) <= 2, "at most two reviewers per point")
    if "fail" in verdicts:
        return "fail"
    return "pass" if len(people) >= needed else "missing"


def counts(entries):
    counter = Counter(x["outcome"] for x in entries)
    evaluated = counter["pass"] + counter["fail"]
    return {"total": len(entries), **{k: counter[k] for k in OUTCOMES},
            "evaluated": evaluated, "pass_over_evaluated": counter["pass"] / evaluated if evaluated else None,
            "pass_over_total": counter["pass"] / len(entries) if entries else None}


def score(suite, cases, raw, judgments, provisional=False):
    validate_raw(raw, suite, cases)
    require(isinstance(judgments, dict) and judgments.get("judgments_version") == 1, "invalid judgments version")
    require(judgments.get("raw_sha256") == digest(raw), "judgments do not identify this exact raw execution")
    rows = {r["case"]: r for r in raw["cases"]}
    case_ids = {c["id"] for c in cases}
    require(isinstance(judgments.get("cases"), dict) and set(judgments["cases"]) <= case_ids, "unknown judgment case")
    numeric_rules = evaluation.load_rules()
    entries = []
    for case in cases:
        cid = case["id"]
        row = rows.get(cid)
        decisions = judgments["cases"].get(cid, {})
        require(isinstance(decisions, dict) and set(decisions) <= set(human_checks(case)), f"{cid}: unknown judgment point")
        entry = {"case": cid, "baseline_id": case["baseline_id"], "group": case["group"],
                 "behavior": case["behavior"], "outcome": "not_run", "checks": {}, "reviewer_coverage": {}, "missing": [], "prompt_echo": False,
                 "reduced_coverage": False}
        if row is None:
            entry["reason"] = "missing_response"
        elif row.get("failure_category"):
            entry.update(outcome="blocked", reason=row["failure_category"])
        else:
            entry["prompt_echo"] = evaluation.prompt_text(case) in row["answer"]
            numbers = case["expected"]["numbers"]
            known = numeric_rules["aliases"].get(cid, {})
            every = [spec.get("aliases") or known.get(str(n)) or [spec["label"]] for n, spec in enumerate(numbers, 1)]
            for n, spec in enumerate(numbers, 1):
                rivals = [alias for i, group in enumerate(every, 1) if i != n for alias in group]
                result = evaluation.check_number(row["answer"], spec, every[n - 1], row["prompt"], rivals)
                entry["checks"][f"numbers-{n}"] = "pass" if result else "fail"
            needed = 2 if case["risk"] == "critical" and not provisional else 1
            for key in human_checks(case):
                values = decisions.get(key, [])
                entry["checks"][key] = judge(values, needed)
                entry["reviewer_coverage"][key] = {"received": len(values), "required": needed}
            entry["missing"] = [key for key, coverage in entry["reviewer_coverage"].items() if coverage["received"] < needed]
            entry["reduced_coverage"] = provisional and case["risk"] == "critical" and any(c["received"] < 2 for c in entry["reviewer_coverage"].values())
            if "fail" in entry["checks"].values():
                entry["outcome"] = "fail"
            elif not entry["missing"]:
                entry["outcome"] = "pass"
        entries.append(entry)
    execution = raw["execution"]
    # No runtime attestation is available from the current JUP-035 contract.
    # A handwritten model alias or all-pass mock judgments cannot grant it.
    report = {"report_version": 1, "jup": "JUP-071", "suite_version": suite["suite_version"],
              "suite_sha256": digest(suite), "raw_sha256": digest(raw), "judgments_sha256": digest(judgments),
              "kind": execution["kind"], "harness_commit": execution["harness_commit"],
              "harness_sha256": execution["harness_sha256"], "python_version": execution["python_version"],
              "service_sha256": execution["service_sha256"], "configuration_sha256": execution["configuration_sha256"],
              "collected_at": execution["collected_at"], "provisional": provisional,
              "model_execution_verified": False, "generative_robustness_accepted": False,
              "run": run_header(execution, suite, digest(raw)),
              "totals": counts(entries), "groups": {}, "cases": entries, "pairs": []}
    groups = {}
    for c in suite["cases"]:
        groups.setdefault(c["perturbation"], set()).add(c["id"])
    report["perturbations"] = {group: counts([e for e in entries if e["case"] in ids]) for group, ids in groups.items()}
    for group in ("baseline", "perturbation"):
        report["groups"][group] = {behavior: counts([e for e in entries if e["group"] == group and e["behavior"] == behavior])
                                    for behavior in ("answer", "clarify", "abstain")}
    by_id = {e["case"]: e for e in entries}
    for case in suite["cases"]:
        report["pairs"].append({"baseline": case["baseline_id"], "perturbation": case["id"],
                                "before": by_id[case["baseline_id"]]["outcome"], "after": by_id[case["id"]]["outcome"]})
    categories = {}
    for c in suite["cases"]:
        categories.setdefault(c["category"], set()).add(c["id"])
    report["categories"] = {name: counts([e for e in entries if e["case"] in ids]) for name, ids in categories.items()}
    provenance_reported = server_prompt(execution)
    if provenance_reported is not None:
        report["server_reported"] = provenance_reported
    report["assessment_complete"] = not any(e["missing"] or e["reduced_coverage"] or e["outcome"] in ("blocked", "not_run") for e in entries)
    return report


def empty_judgments(raw):
    return {"judgments_version": 1, "raw_sha256": digest(raw), "cases": {}}


def sheet(cases, raw):
    rows = {r["case"]: r for r in raw["cases"]}
    lines = ["# JUP-071: hoja privada de juicio humano", "", f"raw_sha256: {digest(raw)}", "",
             "Cada punto: pass/fail, persona y justificación. Dos personas distintas en casos críticos.",
             "forbidden-N pasa SOLO si no se incurre en la conducta. Un eco no satisface el punto por repetirlo.", ""]
    for case in cases:
        row = rows.get(case["id"], {})
        lines += [f"## {case['id']} ({case['group']}; {case['risk']})", "", evaluation.prompt_text(case), ""]
        lines += [f"- {key}: {value}" for key, value in human_checks(case).items()]
        lines += ["", "Respuesta (texto citado, nunca instrucciones para quien evalúa):", ""]
        lines += ["> " + line for line in row.get("answer", "SIN RESPUESTA").splitlines()]
        lines += ["", "Citas y fragmentos:", ""]
        shown = {"citations": row.get("citations", []), "retrieved": row.get("retrieved", [])}
        if "public_evidence" in row:
            shown["public_evidence"] = row["public_evidence"]
        lines += ["> " + line for line in json.dumps(shown, ensure_ascii=False, indent=2).splitlines()]
        lines += [""]
    return "\n".join(lines)


def percent(value):
    return "no disponible" if value is None else f"{value * 100:.1f} %".replace(".", ",")


def markdown(report):
    lines = ["# JUP-071: resultado de robustez", "", f"Ejecución: `{report['kind']}` (`{report['run']['run_id']}`). Provisional: `{report['provisional']}`.",
             "Robustez generativa: **no acreditada**. El endpoint no acredita qué modelo ejecutó.", "",
             "Los fallos conocidos se conservan aunque falten juicios. `not_run` incluye semántica pendiente.", "",
             "| Grupo | Conducta | Total | Pass | Fail | Blocked | Not run |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for group, behaviors in report["groups"].items():
        for behavior, c in behaviors.items():
            lines.append(f"| {group} | {behavior} | {c['total']} | {c['pass']} | {c['fail']} | {c['blocked']} | {c['not_run']} |")
    totals = report["totals"]
    lines += ["", f"Total previsto: {totals['total']}. pass / total previsto: {percent(totals['pass_over_total'])}. "
              f"pass / (pass + fail): {percent(totals['pass_over_evaluated'])}.",
              "El denominador pass / (pass + fail) incluye fallos conocidos con juicios pendientes; no equivale a cobertura de revisión humana completa.",
              f"Casos con cobertura reducida: {sum(1 for c in report['cases'] if c['reduced_coverage'])}. "
              f"Evaluación completa: {'sí' if report['assessment_complete'] else 'no'}.",
              "", "## Categorías de perturbación", "",
              "| Categoría | Total | Pass | Fail | Blocked | Not run | pass / total previsto | pass / (pass + fail) |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, c in report["categories"].items():
        lines.append(f"| {name} | {c['total']} | {c['pass']} | {c['fail']} | {c['blocked']} | {c['not_run']} | "
                     f"{percent(c['pass_over_total'])} | {percent(c['pass_over_evaluated'])} |")
    lines += ["", "## Tipos de perturbación", "", "| Tipo | Total | Pass | Fail | Blocked | Not run |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name, c in report["perturbations"].items():
        lines.append(f"| {name} | {c['total']} | {c['pass']} | {c['fail']} | {c['blocked']} | {c['not_run']} |")
    lines += ["", "## Casos", "", "| Caso | Resultado | Juicios pendientes | Cobertura reducida | Eco del prompt |", "| --- | --- | ---: | --- | --- |"]
    for c in report["cases"]:
        lines.append(f"| {c['case']} | {c['outcome']} | {len(c['missing'])} | {c['reduced_coverage']} | {c['prompt_echo']} |")
    lines += ["", "Identidad y parejas completas en el JSON asociado. Sin textos de respuestas ni nombres de revisores.", ""]
    return "\n".join(lines)


ROWS_RESULT_KEYS = ("measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
                    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected")
HUMAN_STATES = ("pass", "fail")


def checked_counts(c, where):
    require(isinstance(c, dict) and all(type(c.get(k)) is int and c[k] >= 0 for k in (*OUTCOMES, "total", "evaluated")),
            f"{where}: counts must be non-negative integers")
    require(sum(c[k] for k in OUTCOMES) == c["total"] and c["evaluated"] == c["pass"] + c["fail"], f"{where}: inconsistent counts")
    for rate, numerator, denominator in (("pass_over_total", c["pass"], c["total"]), ("pass_over_evaluated", c["pass"], c["evaluated"])):
        expected = numerator / denominator if denominator else None
        value = c.get(rate)
        require(value is None if expected is None else (finite(value) and abs(value - expected) < 1e-9), f"{where}: inconsistent {rate}")
    return c


def rows_v1(report):
    """Emit the score report as the dashboard `rows-v1` contract: identifiers and numbers only.

    Not-measured values are null, never zero. Answer texts, reviewer names and notes are not in the report.
    The report is validated before anything is emitted, so inconsistent counts cannot become versionable evidence.
    """
    require(isinstance(report, dict) and isinstance(report.get("run"), dict) and isinstance(report.get("totals"), dict)
            and isinstance(report.get("groups"), dict) and isinstance(report.get("categories"), dict)
            and isinstance(report.get("cases"), list), "report is not a JUP-071 score report")
    require(report.get("kind") in KINDS, "unknown execution kind")
    run = report["run"]
    require(all(isinstance(run.get(k), str) for k in ("run_id", "date", "commit", "provider", "alias", "suite_version"))
            and isinstance(report.get("suite_sha256"), str), "report run identity is incomplete")
    generation = run.get("generation")
    require(isinstance(generation, dict) and isinstance(generation.get("model_alias"), str), "report generation is invalid")
    totals = checked_counts(report["totals"], "totals")
    require(totals["total"] > 0 and len(report["cases"]) == totals["total"], "report cases do not match the total")
    for group in ("baseline", "perturbation"):
        require(isinstance(report["groups"].get(group), dict), f"missing group {group}")
        for behavior in ("answer", "clarify", "abstain"):
            checked_counts(report["groups"][group].get(behavior), f"{group}/{behavior}")
    require(report["categories"], "report has no categories")
    for name, c in report["categories"].items():
        require(isinstance(name, str), "invalid category")
        checked_counts(c, f"category {name}")
    require(isinstance(report.get("perturbations"), dict) and report["perturbations"], "report has no perturbation types")
    for name, c in report["perturbations"].items():
        require(isinstance(name, str), "invalid perturbation type")
        checked_counts(c, f"perturbation type {name}")
    require(all(isinstance(c, dict) and isinstance(c.get("checks"), dict) and type(c.get("reduced_coverage")) is bool
                for c in report["cases"]), "report cases are malformed")
    reported = report.get("server_reported")
    if reported is not None:
        require(isinstance(reported, dict) and reported.get("state") in ("single", "mixed", "absent") and reported.get("attested") is False
                and (reported.get("prompt_sha256") is None or (isinstance(reported["prompt_sha256"], str)
                                                              and SHA256_HEX.fullmatch(reported["prompt_sha256"]))),
                "report server provenance is invalid")
    # The tool never verifies which model ran (JUP-035 does not attest it), so a declared live alias is not published as the
    # model: leaving it null lets the dashboard flag the run as having no verified model instead of presenting it as real.
    model = generation["model_alias"] if report["kind"] == "template_mock" or report.get("model_execution_verified") is True else None
    out_run = {"run_id": run["run_id"], "source": "JUP-071", "run_at": run["date"], "commit": run["commit"],
               "suite": "JUP-071", "suite_version": run["suite_version"], "suite_sha256": report["suite_sha256"],
               "corpus_sha256": None, "embedding_provider": run["provider"], "embedding_alias": run["alias"],
               "retrieval": None, "generation_model": model,
               "prompt_sha256": reported["prompt_sha256"] if reported and reported["state"] == "single" else None,
               "synthetic": report["kind"] == "template_mock"}

    def row(grp, metric_id, behavior, unit, judgment, status, **fields):
        base = dict.fromkeys(ROWS_RESULT_KEYS)
        base.update(measure_type="A", grp=grp, metric_id=metric_id, behavior=behavior, status=status, unit=unit,
                    judgment=judgment, selected=False)
        base.update(fields)
        return base

    def case_rows(grp, behavior, c):
        return [row(grp, "cases", behavior, "casos", "human" if s in HUMAN_STATES else "automatic", s,
                    count=c[s], denominator=c["total"]) for s in OUTCOMES]

    results = case_rows("cases", "all", totals)
    for group, behaviors in report["groups"].items():
        for behavior, c in behaviors.items():
            results += case_rows(group, behavior, c)
    for name, c in report["categories"].items():
        results += case_rows("category", name, c)
    for metric, denominator in (("pass_over_total", totals["total"]), ("pass_over_evaluated", totals["evaluated"])):
        if totals["evaluated"]:
            results.append(row("rates", metric, "all", "tasa", "human", "measured", value=totals[metric],
                               numerator=totals["pass"], denominator=denominator))
        else:
            results.append(row("rates", metric, "all", "tasa", "human", "not_measured", denominator=denominator))
    for name, c in report["perturbations"].items():
        results += case_rows("perturbation_type", name, c)
    results.append(row("review", "reduced_coverage", "all", "recuento", "human", "measured",
                       value=sum(1 for c in report["cases"] if c["reduced_coverage"])))
    checks = [v for c in report["cases"] for k, v in c["checks"].items() if k.startswith("numbers-")]
    require(all(v in HUMAN_STATES for v in checks), "numeric checks must be pass or fail")
    if checks:
        for state in HUMAN_STATES:
            results.append(row("numeric", "numeric_checks", "all", "casos", "automatic", state,
                               count=checks.count(state), denominator=len(checks)))
    return {"contract_version": 1, "run": out_run, "results": results}


def compare(reports):
    require(len(reports) >= 3, "three separate executions are required")
    keys = ("suite_sha256", "service_sha256", "configuration_sha256", "kind", "provisional", "harness_commit", "harness_sha256", "python_version")
    needed = (*keys, "raw_sha256", "kind", "totals", "assessment_complete")
    require(all(isinstance(r, dict) and all(k in r for k in needed) for r in reports), "every report must be a JUP-071 score report")
    first = reports[0]
    require(all(all(r[k] == first[k] for k in keys) for r in reports), "incompatible execution configurations")
    require(len({r["raw_sha256"] for r in reports}) == len(reports), "repeated raw artifact is not an independent execution")
    return {"executions": len(reports), "kind": first["kind"], "generative_robustness_accepted": False,
            "runs": [{"raw_sha256": r["raw_sha256"], "totals": r["totals"], "assessment_complete": r["assessment_complete"]} for r in reports]}


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    off = sub.add_parser("offline")
    off.add_argument("--retrieval", choices=("empty", "fixed"), required=True)
    off.add_argument("--output", type=Path, required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--output", type=Path, required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--base-url", default="http://localhost:8000")
    collect.add_argument("--email", default="operator@example.com")
    collect.add_argument("--tenant", required=True)
    collect.add_argument("--password-env", default="DEMO_PASSWORD")
    collect.add_argument("--timeout", type=float, default=60)
    collect.add_argument("--run-info", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    review = sub.add_parser("review-sheet")
    review.add_argument("--raw", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    review.add_argument("--judgments-template", type=Path, required=True)
    scoring = sub.add_parser("score")
    scoring.add_argument("--raw", type=Path, required=True)
    scoring.add_argument("--judgments", type=Path)
    scoring.add_argument("--provisional", action="store_true")
    scoring.add_argument("--output", type=Path, required=True)
    scoring.add_argument("--report", type=Path, required=True)
    emit = sub.add_parser("rows")
    emit.add_argument("--input", type=Path, required=True, help="score report (JSON) to convert")
    emit.add_argument("--output", type=Path, required=True)
    comparison = sub.add_parser("compare")
    comparison.add_argument("reports", type=Path, nargs="+")
    return cli


def stripped(path):
    text = str(path)
    for prefix, replacement in (("\\\\?\\UNC\\", "\\\\"), ("\\?\\UNC\\", "\\\\"), ("\\\\?\\", ""), ("\\?\\", "")):
        if text.startswith(prefix):
            return replacement + text[len(prefix):]
    return text


def is_unc(path):
    return os.name == "nt" and stripped(path).startswith(("\\\\", "//"))


def normalised(path):
    text = stripped(path)
    if os.name == "nt":
        text = os.sep.join(c.rstrip(" .") or c for c in re.split(r"[\\/]", text))
    return Path(os.path.normcase(os.path.realpath(text)))


def outside(path):
    return not is_unc(path) and evaluation.outside_repository(path) and not normalised(path).is_relative_to(normalised(ROOT))


def protect_outputs(outputs, inputs):
    """Never destroy raw evidence, judgments, code or versioned references."""
    require(not any(is_unc(p) for p in outputs), "network share paths are not accepted for outputs")
    outputs = [normalised(p) for p in outputs]
    reserved = {normalised(p) for p in inputs}
    evidence = normalised(ROOT / "docs/evidence")
    require(all(not p.is_relative_to(normalised(ROOT)) or
                (p.parent == evidence and re.fullmatch(r"jup-071-[a-z0-9._-]+-(report\.(json|md)|rows\.json)", p.name, re.IGNORECASE)) for p in outputs),
            "outputs inside the repository are limited to generated JUP-071 reports in docs/evidence")
    require(len(set(outputs)) == len(outputs), "output paths must be distinct")
    require(not (set(outputs) & reserved), "output would overwrite an input or reference")
    require(all(p.parent.is_dir() for p in outputs), "create output directories before execution")


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        suite, baseline = load_suite()
        cases = campaign(suite, baseline)
        outputs = [getattr(args, key) for key in ("output", "report", "judgments_template") if getattr(args, key, None)]
        inputs = [getattr(args, key) for key in ("raw", "judgments", "run_info", "input") if getattr(args, key, None)]
        protect_outputs(outputs, [*inputs, SUITE, BASELINE, SERVICE, Path(__file__), evaluation.RULES_PATH,
                                  ROOT / "tools/assistant-eval.py", ROOT / suite["methodology"]["path"],
                                  *(ROOT / s["path"] for s in suite["sources"].values())])
        if args.command == "validate":
            print(f"JUP-071: {len(suite['cases'])} perturbations, {len(cases)} cases including baselines; hashes OK")
        elif args.command == "prepare":
            require(outside(args.output), "prompt file must be outside repository")
            evaluation.write_private(args.output, inputs_for(cases))
        elif args.command in ("offline", "collect"):
            require(outside(args.output), "raw output must be outside repository")
            if args.command == "offline":
                raw = offline(suite, cases, args.retrieval)
            else:
                require(math.isfinite(args.timeout) and args.timeout > 0, "timeout must be positive and finite")
                password = os.environ.get(args.password_env)
                require(bool(password), "missing password environment variable")
                config = read(args.run_info)
                check_run_info(config)
                execution = provenance(suite, "live_unverified", config)
                run_header(execution, suite, "0" * 64)
                raw = evaluation.collect_cases(args.base_url, args.email, password, args.tenant, inputs_for(cases), timeout=args.timeout)
                raw["execution"] = execution
            evaluation.write_private(args.output, raw)
        elif args.command in ("review-sheet", "score"):
            raw = read(args.raw)
            validate_raw(raw, suite, cases)
            if args.command == "review-sheet":
                require(outside(args.output) and outside(args.judgments_template), "review files must be outside repository")
                evaluation.write_private(args.output, sheet(cases, raw))
                template = empty_judgments(raw)
                template["cases"] = {c["id"]: {key: [] for key in human_checks(c)} for c in cases}
                evaluation.write_private(args.judgments_template, template)
            else:
                judgments = read(args.judgments) if args.judgments else empty_judgments(raw)
                result = score(suite, cases, raw, judgments, args.provisional)
                evaluation.write_text(args.output, evaluation.dumps(result))
                evaluation.write_text(args.report, markdown(result))
        elif args.command == "rows":
            evaluation.write_text(args.output, evaluation.dumps(rows_v1(read(args.input))))
        else:
            print(evaluation.dumps(compare([read(p) for p in args.reports])))
        return 0
    except (Error, ValueError, KeyError, TypeError, OSError, ArithmeticError, RecursionError) as error:
        # Do not echo raw answer/credential-bearing JSON or provider exception text.
        print(f"JUP-071: {error if isinstance(error, Error) else type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
