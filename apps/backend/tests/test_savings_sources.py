"""Explicit contract doubles, not execution of unmerged JUP-033/034 services."""
from copy import deepcopy
from datetime import date
from unittest.mock import Mock

import pytest

from app.schemas.savings import SavingsSelection
from app.services.savings_sources import RecommendationSavingsProvider
from app.services.savings_summary import InvalidSavingsEvidence, summarize_savings


def identifier(prefix, digit):
    return f"{prefix}:sha256:{digit * 64}"


@pytest.fixture
def selection():
    return SavingsSelection(start_date=date(2026, 9, 1), end_date=date(2026, 10, 1), top_n=1)


def recommendation_report():
    period = dict(start_date="2026-09-01", end_date="2026-10-01", timezone="UTC")
    recommendations, evidence = [], []
    for digit, rule, value, category, qualification in (
        ("a", "missing_project", None, "tagging", "supported"),
        ("b", "largest_project_cost", "Project A", "investigation", "investigation_candidate"),
    ):
        scope = dict(dimension="project", value=value)
        observed = dict(amount="100.00", currency="EUR", record_count=4)
        evidence_id = identifier("cost-query", digit)
        recommendations.append(dict(
            id=identifier("recommendation", digit), rule_id=rule, rule_version=1,
            category=category, qualification=qualification,
            action="Revisar contexto del proyecto", rationale="Coste observado; no prueba desperdicio.",
            scope=scope, observed_cost=observed, estimated_savings=None, currency=None,
            confidence="low", risk="low", difficulty="unknown", evidence_ids=[evidence_id],
            requires_human_approval=True,
        ))
        evidence.append(dict(
            id=evidence_id, kind="cost_query", source="azure_cost_records",
            query=dict(period=deepcopy(period), group_by="project", tag_key=None),
            rule_id=rule, rule_version=1, scope=deepcopy(scope), observed_cost=deepcopy(observed),
        ))
    return dict(
        contract_version=1, period=period, source="azure_cost_records", cloud="azure",
        data_environment="simulated", data_status="available", status="available",
        recommendations=recommendations, evidence=evidence, total_candidates=2, truncated=False,
        assumptions=["Intervalo UTC con fin exclusivo."], limitations=["Solo costes simulados."],
        not_evaluated=[dict(action="savings_impact", missing_inputs=["Escenario comparable."])],
        missing_dimension_count=4, excluded_undated_count=0,
    )


def impact_report():
    impacts = []
    for digit in ("a", "b"):
        impacts.append(dict(
            scenario=dict(
                recommendation_id=identifier("recommendation", digit),
                cost_scope_ids=[f"/subscriptions/test/resources/{digit}"], currency="EUR",
                baseline_monthly_cost="0.006", target_monthly_cost="0",
                evidence_ids=[identifier("cost-query", digit)],
                assumptions=["Uso y precio constantes durante doce meses."],
            ),
            status="estimated", potential_monthly_savings="0.01", potential_annual_savings="0.07",
            observed_savings=None, included_in_total=True, excluded_by=[],
        ))
    return dict(
        schema_version="1.0", tenant_id="tenant-a", baseline_month="2026-09-01",
        basis="caller_supplied_scenario", aggregation_method="descending_savings_disjoint_scopes",
        recommendations=impacts,
        totals=[dict(currency="EUR", potential_monthly_savings="0.01", potential_annual_savings="0.14",
                     included_recommendation_ids=[item["scenario"]["recommendation_id"] for item in impacts],
                     unestimated_recommendation_ids=[], observed_savings=None)],
        assumptions=["Adopcion completa inmediata."],
        limitations=["Referencias e inputs suministrados no verificados."],
    )


def provider(recommendations=None, impact=None):
    return RecommendationSavingsProvider(
        Mock(return_value=recommendations if recommendations is not None else recommendation_report()),
        Mock(return_value=impact) if impact is not None else None,
    )


def test_recommendations_without_impact_preserve_evidence_and_do_not_invent_savings(selection):
    report = recommendation_report()
    source = provider(report)
    snapshot = source.load_snapshot("tenant-a", selection)
    source.recommendation_loader.assert_called_once_with("tenant-a", selection)
    assert snapshot["upstream_reports"] == {"JUP-033": report}
    assert len(snapshot["opportunities"]) == 2  # top_n is only presentation.
    for item, original in zip(snapshot["opportunities"], report["recommendations"]):
        assert item["monthly_estimate"] is item["annual_estimate"] is None
        assert item["subscription_id"] is item["independent_cost_basis"] is None
        assert item["tenant_id"] == "tenant-a" and item["state"] == "proposed"
        assert item["assumptions"] == report["assumptions"]
        assert item["sources"][0]["evidence_id"] == original["evidence_ids"][0]
        assert "azure_cost_records" in item["sources"][0]["reference"]
        assert any("no es ahorro" in text for text in item["limitations"])
    rendered = summarize_savings(snapshot, "tenant-a", selection)
    assert rendered["evidence"]["groups"][0]["total_status"] == "unavailable"
    assert rendered["evidence"]["realized_savings"] is None


def test_impacts_preserve_rounding_and_original_totals_without_recalculation(selection):
    impacts = impact_report()
    source = provider(impact=impacts)
    snapshot = source.load_snapshot("tenant-a", selection)
    source.impact_loader.assert_called_once_with("tenant-a", selection)
    assert snapshot["upstream_reports"]["JUP-034"] == impacts
    for item in snapshot["opportunities"]:
        assert (item["monthly_estimate"], item["annual_estimate"]) == ("0.01", "0.07")
        assert item["independent_cost_basis"] is None
        assert "Adopcion completa inmediata." in item["assumptions"]
        assert "Uso y precio constantes durante doce meses." in item["assumptions"]
        assert any("hipotetico" in text for text in item["limitations"])
    summary = summarize_savings(snapshot, "tenant-a", selection)["evidence"]
    assert summary["groups"][0]["total_status"] == "non_additive"
    assert summary["groups"][0]["monthly_estimate"] is None
    assert summary["source_snapshot"]["upstream_reports"]["JUP-034"]["totals"][0]["potential_monthly_savings"] == "0.01"
    # Reports are snapshots, not references to mutable producer dictionaries.
    impacts["totals"][0]["potential_monthly_savings"] = "999.99"
    assert snapshot["upstream_reports"]["JUP-034"]["totals"][0]["potential_monthly_savings"] == "0.01"


def test_missing_some_impacts_is_unknown_not_zero(selection):
    impacts = impact_report()
    impacts["recommendations"].pop()
    impacts["totals"][0]["included_recommendation_ids"].pop()
    snapshot = provider(impact=impacts).load_snapshot("tenant-a", selection)
    assert snapshot["opportunities"][1]["monthly_estimate"] is None
    assert any("no disponible" in text for text in snapshot["opportunities"][1]["limitations"])


def test_unknown_impact_and_explicit_zero_are_distinct(selection):
    impacts = impact_report()
    first, second = impacts["recommendations"]
    first.update(status="insufficient_data", potential_monthly_savings=None, potential_annual_savings=None, included_in_total=False)
    first["scenario"].update(baseline_monthly_cost=None, target_monthly_cost=None)
    second.update(status="no_savings", potential_monthly_savings="0.00", potential_annual_savings="0.00")
    second["scenario"].update(baseline_monthly_cost="1", target_monthly_cost="1")
    impacts["totals"][0].update(
        potential_monthly_savings="0.00", potential_annual_savings="0.00",
        included_recommendation_ids=[second["scenario"]["recommendation_id"]],
        unestimated_recommendation_ids=[first["scenario"]["recommendation_id"]],
    )
    snapshot = provider(impact=impacts).load_snapshot("tenant-a", selection)
    assert snapshot["opportunities"][0]["monthly_estimate"] is None
    assert snapshot["opportunities"][1]["monthly_estimate"] == "0.00"


def test_overlap_exclusion_is_preserved_without_hiding_individual_estimate(selection):
    impacts = impact_report()
    first, second = impacts["recommendations"]
    second["scenario"]["cost_scope_ids"] = first["scenario"]["cost_scope_ids"]
    second.update(included_in_total=False, excluded_by=[first["scenario"]["recommendation_id"]])
    impacts["totals"][0]["included_recommendation_ids"].pop()
    snapshot = provider(impact=impacts).load_snapshot("tenant-a", selection)
    assert snapshot["opportunities"][1]["monthly_estimate"] == "0.01"
    assert any("solapadas" in text for text in snapshot["opportunities"][1]["limitations"])


def test_subscription_filter_is_rejected_before_calling_loaders(selection):
    source = provider(impact=impact_report())
    with pytest.raises(InvalidSavingsEvidence):
        source.load_snapshot("tenant-a", selection.model_copy(update={"subscription_id": "sub-a"}))
    source.recommendation_loader.assert_not_called()
    source.impact_loader.assert_not_called()


def test_truncated_producer_is_partial_and_full_report_survives(selection):
    report = recommendation_report()
    report.update(total_candidates=4, truncated=True)
    snapshot = provider(report).load_snapshot("tenant-a", selection)
    assert snapshot["data_status"] == "partial"
    assert any("2 de 4" in text for text in snapshot["limitations"])
    assert snapshot["upstream_reports"]["JUP-033"]["total_candidates"] == 4


def test_empty_producer_stays_empty_not_zero_savings(selection):
    report = recommendation_report()
    report.update(recommendations=[], evidence=[], total_candidates=0, data_status="empty", status="insufficient_data")
    snapshot = provider(report).load_snapshot("tenant-a", selection)
    assert snapshot["data_status"] == "empty" and snapshot["opportunities"] == []
    assert summarize_savings(snapshot, "tenant-a", selection)["evidence"]["realized_savings"] is None


def set_path(report, path, value):
    current = report
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value


@pytest.mark.parametrize("path,value", [
    (("contract_version",), 2),
    (("period", "end_date"), "2026-11-01"),
    (("period", "timezone"), "Europe/Paris"),
    (("unexpected",), "not part of contract"),
    (("total_candidates",), 1),
    (("truncated",), True),
    (("data_status",), "empty"),
    (("evidence", 0, "id"), identifier("cost-query", "c")),
    (("evidence", 0, "observed_cost", "currency"), "USD"),
    (("evidence", 0, "query", "period", "start_date"), "2026-08-01"),
    (("recommendations", 1, "id"), identifier("recommendation", "a")),
    (("recommendations", 0, "estimated_savings"), "100.00"),
    (("recommendations", 0, "qualification"), "investigation_candidate"),
    (("recommendations", 0, "requires_human_approval"), False),
    (("missing_dimension_count",), float("nan")),
])
def test_invalid_recommendation_report_fails_closed(selection, path, value):
    report = deepcopy(recommendation_report())
    set_path(report, path, value)
    with pytest.raises(InvalidSavingsEvidence, match="^Invalid savings evidence.$"):
        provider(report).load_snapshot("tenant-a", selection)


@pytest.mark.parametrize("path,value", [
    (("schema_version",), "2.0"),
    (("tenant_id",), "tenant-b"),
    (("baseline_month",), "2026-08-01"),
    (("basis",), "verified_billing"),
    (("recommendations", 0, "observed_savings"), "0.01"),
    (("recommendations", 0, "potential_monthly_savings"), None),
    (("recommendations", 0, "potential_monthly_savings"), "NaN"),
    (("recommendations", 0, "status"), "no_savings"),
    (("recommendations", 0, "scenario", "recommendation_id"), identifier("recommendation", "c")),
    (("recommendations", 0, "scenario", "currency"), "USD"),
    (("recommendations", 0, "scenario", "evidence_ids"), [identifier("cost-query", "b")]),
    (("recommendations", 0, "scenario", "baseline_monthly_cost"), None),
    (("recommendations", 0, "excluded_by"), [identifier("recommendation", "c")]),
    (("recommendations", 1, "scenario", "cost_scope_ids"), ["/subscriptions/test/resources/a/"]),
    (("totals", 0, "included_recommendation_ids"), [identifier("recommendation", "c")]),
    (("totals", 0, "currency"), "USD"),
    (("totals", 0, "potential_monthly_savings"), None),
    (("totals", 0, "unestimated_recommendation_ids"), [identifier("recommendation", "a")]),
])
def test_invalid_impact_report_fails_closed(selection, path, value):
    report = impact_report()
    set_path(report, path, value)
    with pytest.raises(InvalidSavingsEvidence, match="^Invalid savings evidence.$"):
        provider(impact=report).load_snapshot("tenant-a", selection)


@pytest.mark.parametrize("start,end", [("2026-09-02", "2026-10-01"), ("2026-09-01", "2026-11-01")])
def test_impact_rejects_selection_other_than_its_complete_baseline_month(start, end):
    selection = SavingsSelection(start_date=start, end_date=end)
    report = recommendation_report()
    report["period"].update(start_date=start, end_date=end)
    for evidence in report["evidence"]:
        evidence["query"]["period"] = deepcopy(report["period"])
    with pytest.raises(InvalidSavingsEvidence):
        provider(report, impact_report()).load_snapshot("tenant-a", selection)


def test_unavailable_loader_propagates_without_becoming_an_empty_report(selection):
    source = RecommendationSavingsProvider(Mock(side_effect=RuntimeError("provider unavailable")))
    with pytest.raises(RuntimeError, match="provider unavailable"):
        source.load_snapshot("tenant-a", selection)
