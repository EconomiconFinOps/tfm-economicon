"""JUP-039 consumer-contract tests using explicit synthetic JUP-033/034 rows."""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.savings import SavingsOpportunity, SavingsSelection, SavingsSnapshot
from app.services.savings_summary import InvalidSavingsEvidence, summarize_savings


def selection(**changes):
    return SavingsSelection.model_validate({
        "start_date": "2026-09-01", "end_date": "2026-10-01",
        "subscription_id": "sub-a", **changes,
    })


def opportunity(identifier="rec-a", **changes):
    """A provider double, not evidence of a live recommendation integration."""
    return {
        "recommendation_id": identifier, "tenant_id": "tenant-a",
        "subscription_id": "sub-a", "title": "Reduce idle capacity",
        "action": "Review utilization before reducing capacity", "state": "proposed",
        "currency": "EUR", "monthly_estimate": "100.00", "annual_estimate": "950.00",
        "independent_cost_basis": "cost-basis-" + identifier,
        "risk": "medium", "confidence": "high",
        "assumptions": ["Demand remains within the observed range"],
        "sources": [{"evidence_id": "evidence-" + identifier,
                     "title": "Synthetic utilization snapshot",
                     "reference": "fixture://jup-033-034/" + identifier}],
        "limitations": [], **changes,
    }


def snapshot(rows=None, **changes):
    return {
        "contract_version": "savings-input.v1", "tenant_id": "tenant-a",
        "start_date": "2026-09-01", "end_date": "2026-10-01",
        "subscription_id": "sub-a", "generated_at": "2026-10-01T09:30:00Z",
        "data_status": "available", "opportunities": rows if rows is not None else [opportunity()],
        "limitations": [], **changes,
    }


def summarize(rows=None, *, selected=None, **changes):
    return summarize_savings(snapshot(rows, **changes), "tenant-a", selected or selection())


def test_estimates_preserve_provider_annual_amount_and_never_claim_realized_savings():
    result = summarize()
    evidence = result["evidence"]
    group = evidence["groups"][0]
    assert (group["monthly_estimate"], group["annual_estimate"]) == ("100.00", "950.00")
    assert group["total_status"] == "estimated"
    assert evidence["benefit_kind"] == "potential_estimate"
    assert evidence["realized_savings"] is None
    assert "no es ahorro realizado" in result["content"]
    assert "Ahorro realizado: no verificado" in result["content"]
    assert "950.00 EUR/año" in result["content"]
    assert "1200.00" not in result["content"]


def test_two_hundred_maximum_amounts_sum_exactly_without_float_or_decimal_rounding():
    rows = [opportunity(f"rec-{index:03d}", monthly_estimate="99999999999999999999999999.99",
                        annual_estimate="99999999999999999999999999.99") for index in range(200)]
    group = summarize(rows)["evidence"]["groups"][0]
    assert group["monthly_estimate"] == "19999999999999999999999999998.00"
    assert group["annual_estimate"] == "19999999999999999999999999998.00"
    assert group["quantified_count"] == 200
    assert group["shown_count"] == 5


def test_currencies_have_separate_totals_and_independent_top_n():
    rows = [opportunity("usd-a", currency="USD", monthly_estimate="900.01", annual_estimate="901.01"),
            opportunity("eur-a", monthly_estimate="10.10", annual_estimate="91.10"),
            opportunity("usd-b", currency="USD", monthly_estimate="0.01", annual_estimate="0.02"),
            opportunity("eur-b", monthly_estimate="0.20", annual_estimate="1.30")]
    evidence = summarize(rows, selected=selection(top_n=1))["evidence"]
    assert [(group["currency"], group["monthly_estimate"], group["annual_estimate"],
             group["shown_count"]) for group in evidence["groups"]] == [
        ("EUR", "10.30", "92.40", 1), ("USD", "900.02", "901.03", 1),
    ]
    assert "monthly_estimate" not in evidence  # No combined amount across currencies.
    assert "annual_estimate" not in evidence


@pytest.mark.parametrize("basis", [None, "shared-capacity"])
def test_unknown_independence_or_overlap_suppresses_totals_but_preserves_estimates(basis):
    rows = [opportunity("rec-a", independent_cost_basis=basis),
            opportunity("rec-b", independent_cost_basis=basis)]
    result = summarize(rows)
    group = result["evidence"]["groups"][0]
    assert group["total_status"] == "non_additive"
    assert group["monthly_estimate"] is None
    assert group["annual_estimate"] is None
    assert [row["monthly_estimate"] for row in group["opportunities"]] == ["100.00", "100.00"]
    assert "No sumar las estimaciones individuales" in result["content"]


def test_unquantified_is_not_zero_and_known_zero_is_a_partial_subtotal():
    unknown = opportunity("unknown", monthly_estimate=None, annual_estimate=None,
                          independent_cost_basis=None, limitations=["No rate available"])
    unknown_result = summarize([unknown])
    unknown_group = unknown_result["evidence"]["groups"][0]
    assert unknown_group["total_status"] == "unavailable"
    assert unknown_group["monthly_estimate"] is None
    assert unknown_group["annual_estimate"] is None
    assert unknown_group["quantified_count"] == 0
    assert unknown_group["unquantified_count"] == 1
    assert "no se sustituye por cero" in unknown_result["content"]

    result = summarize([unknown, opportunity("zero", monthly_estimate="0.00", annual_estimate="0.00")])
    group = result["evidence"]["groups"][0]
    assert group["total_status"] == "partial"
    assert (group["monthly_estimate"], group["annual_estimate"]) == ("0.00", "0.00")
    assert (group["quantified_count"], group["unquantified_count"]) == (1, 1)
    assert [row["recommendation_id"] for row in group["opportunities"]] == ["zero", "unknown"]
    assert "Subtotal parcial conocido" in result["content"]


def test_known_zero_without_missing_data_is_an_estimate():
    group = summarize([opportunity(monthly_estimate="0.00", annual_estimate="0.00")])["evidence"]["groups"][0]
    assert group["total_status"] == "estimated"
    assert group["monthly_estimate"] == "0.00"


def test_only_proposed_and_accepted_are_included_and_excluded_rows_remain_auditable():
    rows = [opportunity(state, state=state) for state in
            ("proposed", "accepted", "dismissed", "implemented", "expired")]
    evidence = summarize(rows)["evidence"]
    assert evidence["opportunity_count"] == 2
    assert evidence["excluded_count"] == 3
    assert evidence["excluded_states"] == {"dismissed": 1, "implemented": 1, "expired": 1}
    assert evidence["groups"][0]["monthly_estimate"] == "200.00"
    assert {row["state"] for row in evidence["groups"][0]["opportunities"]} == {"proposed", "accepted"}
    assert len(evidence["source_snapshot"]["opportunities"]) == 5
    assert evidence["realized_savings"] is None


def test_top_n_limits_presentation_without_losing_evidence_assumptions_or_totals():
    rows = [opportunity("rec-a", monthly_estimate="10.00", annual_estimate="101.00"),
            opportunity("rec-b", monthly_estimate="30.00", annual_estimate="201.00"),
            opportunity("rec-c", monthly_estimate="20.00", annual_estimate="301.00",
                        assumptions=["Only weekday capacity is eligible"],
                        limitations=["Weekend demand has not been measured"])]
    original = deepcopy(rows)
    limited = summarize(rows, selected=selection(top_n=1))["evidence"]
    full = summarize(rows, selected=selection(top_n=20))["evidence"]
    group = limited["groups"][0]
    assert group["shown_count"] == 1
    assert group["opportunity_count"] == 3
    assert group["monthly_estimate"] == "60.00"
    assert group["annual_estimate"] == "603.00"
    assert [row["recommendation_id"] for row in group["opportunities"]] == ["rec-b"]
    assert limited["source_snapshot"] == full["source_snapshot"]
    assert limited["source_snapshot"]["opportunities"] == original
    assert limited["snapshot_sha256"] == full["snapshot_sha256"]
    assert len(limited["snapshot_sha256"]) == 64
    assert rows == original  # Caller-owned source evidence is never mutated.
    changed = deepcopy(rows)
    changed[2]["assumptions"] = ["Updated weekday assumption"]
    assert summarize(changed)["evidence"]["snapshot_sha256"] != limited["snapshot_sha256"]


def test_ranking_is_numeric_and_stable_for_equal_amounts_and_missing_estimates():
    rows = [opportunity("rec-b", monthly_estimate="9.00"),
            opportunity("rec-d", monthly_estimate=None, annual_estimate=None, limitations=["Missing rate"]),
            opportunity("rec-a", monthly_estimate="9.00"),
            opportunity("rec-c", monthly_estimate="100.00")]
    forward = summarize(rows)["evidence"]["groups"]
    reversed_input = summarize(list(reversed(rows)))["evidence"]["groups"]
    assert forward == reversed_input
    assert [row["recommendation_id"] for row in forward[0]["opportunities"]] == [
        "rec-c", "rec-a", "rec-b", "rec-d",
    ]


def test_partial_source_coverage_labels_known_subtotal_and_retains_reason():
    result = summarize(data_status="partial", limitations=["One subscription has no cost export"])
    assert result["evidence"]["data_status"] == "partial"
    assert result["evidence"]["groups"][0]["total_status"] == "partial"
    assert result["evidence"]["groups"][0]["monthly_estimate"] == "100.00"
    assert "Subtotal parcial conocido" in result["content"]
    assert "One subscription has no cost export" in result["content"]


@pytest.mark.parametrize("rows,status", [([], "empty"), ([opportunity(state="implemented")], "available")])
def test_no_active_opportunities_does_not_assert_zero_savings(rows, status):
    result = summarize(rows, data_status=status)
    assert result["evidence"]["groups"] == []
    assert result["evidence"]["opportunity_count"] == 0
    assert result["evidence"]["realized_savings"] is None
    assert "no acredita ahorro cero" in result["content"]
    assert "0.00" not in result["content"]


@pytest.mark.parametrize("field,value", [
    ("tenant_id", "tenant-other"), ("subscription_id", "sub-other"),
    ("start_date", "2026-09-02"), ("end_date", "2026-10-02"),
])
def test_snapshot_scope_mismatch_fails_closed(field, value):
    with pytest.raises(InvalidSavingsEvidence, match=r"^Invalid savings evidence\.$"):
        summarize(**{field: value})


@pytest.mark.parametrize("changes", [
    {"tenant_id": "tenant-other"}, {"subscription_id": "sub-other"},
])
@pytest.mark.parametrize("state", ["proposed", "implemented"])
def test_out_of_scope_opportunities_fail_closed_even_when_excluded(changes, state):
    with pytest.raises(InvalidSavingsEvidence):
        summarize([opportunity(state=state, **changes)])


def test_all_subscriptions_selection_accepts_different_subscriptions_in_same_tenant():
    result = summarize([opportunity("a"), opportunity("b", subscription_id="sub-b")],
                       subscription_id=None, selected=selection(subscription_id=None))
    assert result["evidence"]["opportunity_count"] == 2
    assert result["evidence"]["groups"][0]["monthly_estimate"] == "200.00"


def test_duplicate_recommendation_ids_fail_closed_including_different_states():
    with pytest.raises(InvalidSavingsEvidence):
        summarize([opportunity(), opportunity(state="dismissed")])


def test_same_source_id_can_be_reused_only_with_identical_provenance():
    first, second = opportunity("first"), opportunity("second")
    second["sources"] = deepcopy(first["sources"])
    assert summarize([first, second])["evidence"]["opportunity_count"] == 2
    second["sources"][0]["reference"] = "fixture://conflicting-source"
    with pytest.raises(InvalidSavingsEvidence):
        summarize([first, second])
    second["state"] = "expired"
    with pytest.raises(InvalidSavingsEvidence):
        summarize([first, second])


@pytest.mark.parametrize("changes", [
    {"top_n": 0}, {"top_n": 21}, {"top_n": True}, {"top_n": "5"}, {"top_n": 5.0},
    {"start_date": "2026-10-01"}, {"start_date": "2026-10-02"},
    {"start_date": "2026-02-30"}, {"subscription_id": "  "}, {"untrusted": "value"},
    {"start_date": 0}, {"start_date": "0"}, {"end_date": "1790812800"},
    {"start_date": "2026-09-01T00:00:00"}, {"end_date": "2026-10-01T00:00:00Z"},
])
def test_invalid_selection_is_rejected(changes):
    with pytest.raises(ValidationError):
        selection(**changes)


@pytest.mark.parametrize("money", [
    "-0.01", "-0.00", "1", "1.0", "1.001", "01.00", "1e2", "NaN", "Infinity",
    "100000000000000000000000000.00", 1, 1.01, True,
])
@pytest.mark.parametrize("field", ["monthly_estimate", "annual_estimate"])
def test_estimates_require_bounded_nonnegative_exact_decimal_strings(field, money):
    with pytest.raises(ValidationError):
        SavingsOpportunity.model_validate(opportunity(**{field: money}))


@pytest.mark.parametrize("changes", [
    {"monthly_estimate": None}, {"annual_estimate": None},
    {"monthly_estimate": None, "annual_estimate": None},
    {"sources": []}, {"assumptions": []}, {"currency": "eur"},
    {"currency": "EURO"}, {"risk": "unknown"}, {"state": "deleted"},
])
def test_invalid_provider_opportunity_fails_closed(changes):
    with pytest.raises(InvalidSavingsEvidence):
        summarize([opportunity(**changes)])


@pytest.mark.parametrize("changes", [
    {"data_status": "partial"}, {"data_status": "empty"}, {"opportunities": []},
    {"generated_at": "2026-10-01T09:30:00"}, {"contract_version": "savings-input.v2"},
    {"end_date": "2026-08-01"}, {"realized_savings": "100.00"},
])
def test_invalid_snapshot_cannot_be_used_as_savings_evidence(changes):
    with pytest.raises(InvalidSavingsEvidence):
        summarize(**changes)


def test_snapshot_limits_the_contract_to_two_hundred_opportunities():
    with pytest.raises(ValidationError):
        SavingsSnapshot.model_validate(snapshot([opportunity(str(index)) for index in range(201)]))


@pytest.mark.parametrize("kind", ["unsupported_object", "invalid_utf8_bytes", "lone_surrogate"])
def test_non_json_upstream_evidence_fails_closed_instead_of_escaping_serializer(kind):
    value = {"unsupported_object": object(), "invalid_utf8_bytes": b"\xff", "lone_surrogate": "\ud800"}[kind]
    with pytest.raises(InvalidSavingsEvidence, match=r"^Invalid savings evidence\.$"):
        summarize(upstream_reports={"JUP-034": {"invalid": value}})
