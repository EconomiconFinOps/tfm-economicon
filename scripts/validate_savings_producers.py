"""Opt-in compatibility smoke. Pass trusted JUP-033 and JUP-034 repo roots."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--recommendations-root', type=Path, required=True)
parser.add_argument('--impact-root', type=Path, required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / "apps/backend"))
from app.schemas.billing import BillingSummary
from app.schemas.savings import SavingsSelection
from app.services.savings_sources import RecommendationSavingsProvider
from app.services.savings_summary import summarize_savings
from pydantic import ValidationError

fingerprints = {}

def load(name, relative):
    producer, suffix = relative.split('/', 1)
    path = (args.recommendations_root if producer.endswith('033') else args.impact_root) / suffix
    fingerprints[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

load("app.schemas.recommendations", "tfm-economicon-jup033/apps/backend/app/schemas/recommendations.py")
rservice = load("smoke_recommendations", "tfm-economicon-jup033/apps/backend/app/services/recommendations.py")
ischema = load("app.schemas.recommendation_impact", "tfm-economicon-jup034/apps/backend/app/schemas/recommendation_impact.py")
iservice = load("smoke_impact", "tfm-economicon-jup034/apps/backend/app/services/recommendation_impact.py")
selection = SavingsSelection(start_date="2026-09-01", end_date="2026-10-01", top_n=1)
summary = BillingSummary(
    period=dict(start_date="2026-09-01", end_date="2026-10-01", timezone="UTC"),
    group_by="project", tag_key=None, data_status="available",
    totals=[dict(currency="EUR", cost="200.00", record_count=8)],
    groups=[dict(currency="EUR", cost="100.00", record_count=4, subscription_id=None, value=value)
            for value in (None, "Project A")],
    missing_dimension_count=4, excluded_undated_count=0, monthly_spend="200.00",
    savings_identified=None, open_ingestions=0, currency="EUR",
)
recommendations = rservice.generate_recommendations(summary, tenant_id="tenant-a")
scenarios = [dict(recommendation_id=item.id, cost_scope_ids=[f"/subscriptions/test/resources/{index}"],
                  currency="EUR", baseline_monthly_cost="0.006", target_monthly_cost="0",
                  evidence_ids=item.evidence_ids, assumptions=["Hypothetical fixed usage and price."])
             for index, item in enumerate(recommendations.recommendations)]
request = ischema.ImpactRequest(baseline_month="2026-09-01", scenarios=scenarios)
impact = iservice.evaluate_recommendation_impact(request, "tenant-a")
snapshot = RecommendationSavingsProvider(lambda tenant, selected: recommendations,
                                         lambda tenant, selected: impact).load_snapshot("tenant-a", selection)
result = summarize_savings(snapshot, "tenant-a", selection)["evidence"]
assert result["opportunity_count"] == 2
assert result["groups"][0]["total_status"] == "non_additive"
assert result["groups"][0]["monthly_estimate"] is None
assert all(row["monthly_estimate"] == "0.01" and row["annual_estimate"] == "0.07" for row in snapshot["opportunities"])
assert snapshot["upstream_reports"]["JUP-034"]["totals"][0]["potential_monthly_savings"] == "0.01"
assert snapshot["upstream_reports"]["JUP-034"]["totals"][0]["potential_annual_savings"] == "0.14"
scenarios[1].update(baseline_monthly_cost=None, target_monthly_cost=None)
unknown = iservice.evaluate_recommendation_impact(ischema.ImpactRequest(baseline_month="2026-09-01", scenarios=scenarios), "tenant-a")
unknown_snapshot = RecommendationSavingsProvider(lambda tenant, selected: recommendations,
                                                 lambda tenant, selected: unknown).load_snapshot("tenant-a", selection)
assert unknown_snapshot["opportunities"][1]["monthly_estimate"] is None
try:
    ischema.ImpactScenario(**{**scenarios[0], "target_monthly_cost": None})
except ValidationError:
    pass
else:
    raise AssertionError("Producer accepted an unpaired scenario unexpectedly")
report = dict(status="passed", verification="local producer functions; synthetic billing/scenarios; no persistence or API integration",
              checks=["real generated recommendation and evidence IDs", "model-to-adapter serialization", "separate rounded individual estimates and original totals",
                      "unquantified impact remains null", "producer rejects unpaired costs"],
              producer_files_sha256=fingerprints,
              source_snapshot_sha256=result["snapshot_sha256"])
print(json.dumps(report, indent=2))
