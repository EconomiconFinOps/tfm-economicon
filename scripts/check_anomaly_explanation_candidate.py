"""Explicit local compatibility probe, outside CI: JUP-030 candidate plus JUP-038.

Uses the requested detector checkout's modules and synthetic billing responses.
No database, cloud connection, deployed integration or human validation is claimed.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import sys


def selection():
    return {
        "start_date": "2024-06-01", "end_date": "2024-06-08",
        "group_by": "service", "currency": "EUR", "absolute_threshold": "100.00",
        "deviation_threshold_percent": None, "min_absolute_increase": "0.01",
    }


class BillingDouble:
    """Independent observed-cost fixture; does not run billing SQL."""

    def __init__(self, current="125.25", previous="100.00", partial=False):
        self.current = current
        self.previous = previous
        self.partial = partial
        self.calls = []

    def fetch_billing_summary(self, tenant, *, start_date, end_date, group_by, tag_key):
        self.calls.append((tenant, str(start_date), str(end_date), group_by, tag_key))
        is_current = str(start_date) == "2024-06-01"
        cost = self.current if is_current else self.previous
        observed = {"currency": "EUR", "cost": cost, "record_count": 2 if is_current else 1}
        return {
            "contract_version": 2,
            "period": {"start_date": start_date, "end_date": end_date, "timezone": "UTC"},
            "group_by": group_by, "tag_key": tag_key,
            "data_status": "empty" if cost is None else "partial" if is_current and self.partial else "available",
            "totals": [] if cost is None else [observed.copy()],
            "groups": [] if cost is None else [{**observed, "subscription_id": "subscription-a", "value": "Compute"}],
            "missing_dimension_count": 1 if is_current and self.partial else 0,
            "excluded_undated_count": 0, "monthly_spend": None, "savings_identified": None,
            "open_ingestions": 0, "currency": "EUR",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detector-root", required=True, type=Path,
                        help="Repository root of the explicit JUP-030 candidate checkout")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository / "apps" / "backend"))
    from app.schemas.anomaly_explanations import ExplainAnomalyRequest
    from app.services.anomaly_explanations import BillingAnomalyProvider, EvidenceChanged, explain_anomaly

    upstream = args.detector_root.resolve() / "apps" / "backend" / "app"
    hashes = {}
    for name, relative in (("app.schemas.anomalies", "schemas/anomalies.py"),
                           ("app.services.anomalies", "services/anomalies.py")):
        path = upstream / relative
        # Compile the same bytes we hash: concurrent candidate edits cannot change
        # which source version is attributed to this invocation.
        source = path.read_bytes()
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(source, str(path), "exec"), module.__dict__)
        hashes["apps/backend/app/" + relative] = hashlib.sha256(source).hexdigest()

    results = []
    cases = [
        ("absolute", BillingDouble(), {}),
        ("both_rules", BillingDouble(), {"deviation_threshold_percent": "20.00"}),
        ("missing_baseline", BillingDouble(previous=None), {"deviation_threshold_percent": "20.00"}),
        ("zero_baseline", BillingDouble(previous="0.00"), {"deviation_threshold_percent": "20.00"}),
        ("partial_current", BillingDouble(partial=True), {}),
        ("large_decimal", BillingDouble(current="9007199254740993.01"),
         {"absolute_threshold": "9007199254740993.00"}),
    ]
    for name, database, changes in cases:
        chosen = {**selection(), **changes}
        raw = BillingAnomalyProvider(database).evaluate("tenant-a", chosen)
        alert = raw["alerts"][0]
        request = ExplainAnomalyRequest(anomaly_id=alert["id"], evidence_id=alert["evidence_id"], definition=chosen)
        result = explain_anomaly(raw, request)
        assert result.evidence["anomaly"] == alert
        assert result.evidence["definition"] == raw["definition"]
        assert result.cause_status == "not_established"
        assert all(call[0] == "tenant-a" for call in database.calls)
        results.append({"case": name, "status": "passed", "evaluation_status": raw["evaluation_status"],
                        "rules": alert["trigger_reasons"], "database": "synthetic double"})

    database = BillingDouble()
    old = BillingAnomalyProvider(database).evaluate("tenant-a", selection())
    database.current = "126.25"
    new = BillingAnomalyProvider(database).evaluate("tenant-a", selection())
    assert old["alerts"][0]["id"] == new["alerts"][0]["id"]
    assert old["alerts"][0]["evidence_id"] != new["alerts"][0]["evidence_id"]
    request = ExplainAnomalyRequest(anomaly_id=old["alerts"][0]["id"],
                                     evidence_id=old["alerts"][0]["evidence_id"], definition=selection())
    try:
        explain_anomaly(new, request)
    except EvidenceChanged:
        results.append({"case": "stale_snapshot", "status": "passed"})
    else:
        raise AssertionError("Expected stale evidence rejection")

    print(json.dumps({
        "scope": "Explicit local JUP-030 candidate modules; adapter plus explainer; synthetic billing only, no production SQL or deployment",
        "python": platform.python_version(),
        "versions": {name: importlib.metadata.version(name) for name in ["pytest", "pydantic", "fastapi", "sqlalchemy"]},
        "sha256": hashes, "results": results,
    }, indent=2))


if __name__ == "__main__":
    main()
