"""Offline integrity/arithmetic check of the published historical matched replay."""
import collections
import csv
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re

if not __debug__:
    raise RuntimeError("Run this integrity checker without Python optimization (-O).")


def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    lo = int(position)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (position - lo)


def verify(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]) == {"comparison.json", "phases.csv", "provenance.json"}
    for name, identity in manifest["files"].items():
        payload = (root / name).read_bytes()
        assert len(payload) == identity["bytes"], (name, "size")
        assert hashlib.sha256(payload).hexdigest() == identity["sha256"], (name, "hash")
    report = json.loads((root / "comparison.json").read_text(encoding="utf-8"))
    provenance = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
    assert report["state"] == "PAIRED_LOCAL_PROVISIONAL_COMPARISON"
    assert report["acceptance"] == provenance["acceptance"] == "NOT_ASSESSED"
    assert report["independent_adjudication"] is provenance["independent_adjudication"] is False
    assert report["api_ui_validated"] is provenance["api_ui_validated"] is False
    assert report["same_frozen_questions_and_actual_contexts"] is True
    assert provenance["new_inference_executed"] is False
    assert provenance["source_sha256"] == manifest["files"]["comparison.json"]["sha256"]
    expected = {(f"JUP-069-{i:03d}", r) for i in range(1, 29) for r in range(1, 4)}
    assert {(x["case_id"], x["repetition"]) for x in report["paired_samples"]} == expected
    assert len(report["paired_samples"]) == 84
    with (root / "phases.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 336
    assert {x["model"] for x in rows} == set(report["models"])
    results = {}
    for model, summary in report["models"].items():
        actual = collections.Counter(x[model] for x in report["paired_samples"])
        assert dict(actual) == summary["verdicts"], (model, "verdicts")
        by_case = collections.defaultdict(collections.Counter)
        for sample in report["paired_samples"]:
            by_case[sample["case_id"]][sample[model]] += 1
        assert {case: dict(v) for case, v in by_case.items()} == {
            case: value[model] for case, value in report["cases"].items()
        }, (model, "case totals")
        selected = [r for r in rows if r["model"] == model]
        assert len(selected) == 168
        assert {(r["case_id"], int(r["repetition"])) for r in selected} == expected
        seen = set()
        durations = collections.defaultdict(float)
        cost = Decimal(0)
        for row in selected:
            identity = (row["case_id"], int(row["repetition"]), row["phase"])
            assert identity not in seen and row["phase"] in ("draft", "final")
            seen.add(identity)
            assert re.fullmatch(r"[0-9a-f]{64}", row["receipt_sha256"])
            phase_cost, seconds = Decimal(row["cost_usd"]), float(row["generation_seconds"])
            assert phase_cost.is_finite() and phase_cost >= 0
            assert math.isfinite(seconds) and seconds >= 0
            cost += phase_cost
            durations[identity[:2]] += seconds
        assert cost == Decimal(summary["reported_phase_cost_usd"]), (model, "cost")
        assert summary["responses"] == len(durations) == 84
        assert summary["phases_with_unknown_cost"] == 0
        for name, p in (("generation_seconds_p50", .5), ("generation_seconds_p95", .95)):
            assert math.isclose(percentile(durations.values(), p), summary[name], abs_tol=1e-12), (model, name)
        assert math.isclose(max(durations.values()), summary["generation_seconds_max"], abs_tol=1e-12)
        results[model] = {"responses": 84, "phases": 168, "verdicts": dict(actual), "cost_usd": str(cost)}
    # Allowlisted publication contains no free-text source requests/responses or account data.
    prohibited = {"requests", "response", "messages", "ledger_snapshot", "authorization", "api_key", "password", "cookie"}
    def walk(value):
        if isinstance(value, dict):
            assert not (set(k.casefold() for k in value) & prohibited)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            assert not re.search(r"\b(?:sk-or-v1-|gh[pousr]_)[A-Za-z0-9_-]{20,}", value)
    walk(report)
    walk(provenance)
    return {"status": "PASS", "scope": "offline integrity and arithmetic; no new inference or semantic adjudication", "models": results}


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parent), ensure_ascii=False, indent=2))
