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


def text_list(value):
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def validate(suite, baseline):
    require(suite.get("schema_version") == 1 and suite.get("jup") == "JUP-071", "invalid JUP-071 suite")
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
        for n in case["expected_numbers"]:
            require(isinstance(n.get("label"), str) and bool(n["label"].strip()) and
                    isinstance(n.get("unit"), str) and bool(n["unit"].strip()), f"{cid}: invalid number label/unit")
            for key in ("value", "tolerance"):
                require(type(n.get(key)) in (int, float) and math.isfinite(n[key]), f"{cid}: non-finite number")
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
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def provenance(suite, kind, config):
    return {"kind": kind, "collected_at": datetime.now(timezone.utc).isoformat(),
            "harness_commit": code_commit(), "suite_sha256": digest(suite),
            "harness_sha256": digest({str(p.relative_to(ROOT)): file_digest(p) for p in
                                      (Path(__file__), ROOT / "tools/assistant-eval.py", evaluation.RULES_PATH)}),
            "python_version": sys.version.split()[0],
            "service_sha256": file_digest(SERVICE), "configuration_sha256": digest(config),
            "configuration": config, "model_execution_verified": False}


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


def validate_raw(raw, suite, cases):
    require(isinstance(raw, dict) and raw.get("raw_version") == 1, "invalid raw version")
    execution = raw["execution"]
    require(execution["kind"] in KINDS, "unknown execution kind")
    require(execution["suite_sha256"] == digest(suite), "raw data belongs to a different suite")
    require(execution["configuration_sha256"] == digest(execution["configuration"]), "configuration hash mismatch")
    require(re.fullmatch(r"[0-9a-f]{40}", execution["harness_commit"]), "invalid harness commit")
    require(isinstance(execution["collected_at"], str) and
            re.fullmatch(r"\d{4}-\d{2}-\d{2}T[0-9:.]+\+00:00", execution["collected_at"]), "invalid UTC collection time")
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", execution["python_version"]), "invalid Python version")
    for key in ("service_sha256", "configuration_sha256", "harness_sha256"):
        require(re.fullmatch(r"[0-9a-f]{64}", execution[key]), "invalid provenance hash")
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
            distance = fragment.get("distance")
            require(type(distance) in (float, int) and math.isfinite(distance), f"{cid}: invalid distance")
        total = row.get("total_ms")
        require(total is None or (type(total) in (float, int) and math.isfinite(total) and total >= 0), f"{cid}: invalid latency")


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
                 "behavior": case["behavior"], "outcome": "not_run", "checks": {}, "reviewer_coverage": {}, "missing": [], "prompt_echo": False}
        if row is None:
            entry["reason"] = "missing_response"
        elif row.get("failure_category"):
            entry.update(outcome="blocked", reason=row["failure_category"])
        else:
            entry["prompt_echo"] = evaluation.prompt_text(case) in row["answer"]
            for n, spec in enumerate(case["expected"]["numbers"], 1):
                aliases = numeric_rules["aliases"].get(cid, {})
                own = aliases.get(str(n)) or [spec["label"]]
                rivals = [s["label"] for i, s in enumerate(case["expected"]["numbers"], 1) if i != n]
                result = evaluation.check_number(row["answer"], spec, own, row["prompt"], rivals)
                entry["checks"][f"numbers-{n}"] = "pass" if result else "fail"
            needed = 2 if case["risk"] == "critical" and not provisional else 1
            for key in human_checks(case):
                values = decisions.get(key, [])
                entry["checks"][key] = judge(values, needed)
                entry["reviewer_coverage"][key] = {"received": len(values), "required": needed}
            entry["missing"] = [key for key, coverage in entry["reviewer_coverage"].items() if coverage["received"] < needed]
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
    report["assessment_complete"] = not any(e["missing"] or e["outcome"] in ("blocked", "not_run") for e in entries)
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
        lines += ["> " + line for line in json.dumps({"citations": row.get("citations", []), "retrieved": row.get("retrieved", [])}, ensure_ascii=False, indent=2).splitlines()]
        lines += [""]
    return "\n".join(lines)


def markdown(report):
    lines = ["# JUP-071: resultado de robustez", "", f"Ejecución: `{report['kind']}`. Provisional: `{report['provisional']}`.",
             "Robustez generativa: **no acreditada**. El endpoint no acredita qué modelo ejecutó.", "",
             "Los fallos conocidos se conservan aunque falten juicios. `not_run` incluye semántica pendiente.", "",
             "| Grupo | Conducta | Total | Pass | Fail | Blocked | Not run |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for group, behaviors in report["groups"].items():
        for behavior, c in behaviors.items():
            lines.append(f"| {group} | {behavior} | {c['total']} | {c['pass']} | {c['fail']} | {c['blocked']} | {c['not_run']} |")
    lines += ["", "| Caso | Resultado | Juicios pendientes | Eco del prompt |", "| --- | --- | ---: | --- |"]
    for c in report["cases"]:
        lines.append(f"| {c['case']} | {c['outcome']} | {len(c['missing'])} | {c['prompt_echo']} |")
    lines += ["", "Identidad y parejas completas en el JSON asociado. Sin textos de respuestas ni nombres de revisores.", ""]
    return "\n".join(lines)


def compare(reports):
    require(len(reports) >= 3, "three separate executions are required")
    first = reports[0]
    keys = ("suite_sha256", "service_sha256", "configuration_sha256", "kind", "provisional", "harness_commit", "harness_sha256", "python_version")
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
    comparison = sub.add_parser("compare")
    comparison.add_argument("reports", type=Path, nargs="+")
    return cli


def protect_outputs(outputs, inputs):
    """Never destroy raw evidence, judgments, code or versioned references."""
    outputs = [p.resolve() for p in outputs]
    reserved = {p.resolve() for p in inputs}
    require(len(set(outputs)) == len(outputs), "output paths must be distinct")
    require(not (set(outputs) & reserved), "output would overwrite an input or reference")
    require(all(p.parent.is_dir() for p in outputs), "create output directories before execution")


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        suite, baseline = load_suite()
        cases = campaign(suite, baseline)
        outputs = [getattr(args, key) for key in ("output", "report", "judgments_template") if getattr(args, key, None)]
        inputs = [getattr(args, key) for key in ("raw", "judgments", "run_info") if getattr(args, key, None)]
        protect_outputs(outputs, [*inputs, SUITE, BASELINE, SERVICE, Path(__file__), evaluation.RULES_PATH,
                                  ROOT / "tools/assistant-eval.py", ROOT / suite["methodology"]["path"],
                                  *(ROOT / s["path"] for s in suite["sources"].values())])
        if args.command == "validate":
            print(f"JUP-071: {len(suite['cases'])} perturbations, {len(cases)} cases including baselines; hashes OK")
        elif args.command == "prepare":
            evaluation.write_private(args.output, inputs_for(cases))
        elif args.command in ("offline", "collect"):
            require(evaluation.outside_repository(args.output), "raw output must be outside repository")
            if args.command == "offline":
                raw = offline(suite, cases, args.retrieval)
            else:
                require(math.isfinite(args.timeout) and args.timeout > 0, "timeout must be positive and finite")
                password = os.environ.get(args.password_env)
                require(bool(password), "missing password environment variable")
                config = read(args.run_info)
                require(isinstance(config, dict) and all(k in config for k in ("commit", "corpus", "provider", "alias", "retrieval", "generation")), "run-info requires the JUP-070 configuration fields")
                execution = provenance(suite, "live_unverified", config)
                raw = evaluation.collect_cases(args.base_url, args.email, password, args.tenant, inputs_for(cases), timeout=args.timeout)
                raw["execution"] = execution
            evaluation.write_private(args.output, raw)
        elif args.command in ("review-sheet", "score"):
            raw = read(args.raw)
            validate_raw(raw, suite, cases)
            if args.command == "review-sheet":
                require(evaluation.outside_repository(args.output) and evaluation.outside_repository(args.judgments_template), "review files must be outside repository")
                evaluation.write_private(args.output, sheet(cases, raw))
                template = empty_judgments(raw)
                template["cases"] = {c["id"]: {key: [] for key in human_checks(c)} for c in cases}
                evaluation.write_private(args.judgments_template, template)
            else:
                judgments = read(args.judgments) if args.judgments else empty_judgments(raw)
                result = score(suite, cases, raw, judgments, args.provisional)
                evaluation.write_text(args.output, evaluation.dumps(result))
                evaluation.write_text(args.report, markdown(result))
        else:
            print(evaluation.dumps(compare([read(p) for p in args.reports])))
        return 0
    except (Error, ValueError, KeyError, TypeError, OSError) as error:
        # Do not echo raw answer/credential-bearing JSON or provider exception text.
        print(f"JUP-071: {error if isinstance(error, Error) else type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
