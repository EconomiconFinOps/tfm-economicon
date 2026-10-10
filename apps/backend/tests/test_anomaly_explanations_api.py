"""JUP-038 HTTP/adapter contract: real SQLite/auth, explicit detector doubles.

These tests do not claim to execute JUP-030 or production cost aggregation.
"""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, call as mock_call

import pytest
from pydantic import BaseModel

from app.api.routes.anomaly_explanations import get_anomaly_provider
from app.schemas.billing import AmbiguousCostSource, BillingPeriod, BillingSummary
from app.services import anomaly_explanations as explanations
from app.services.anomaly_explanations import (
    BillingAnomalyProvider, DetectorUnavailable, InvalidSelection,
)
from tenant_isolation_support import populated_database, rows, tenant_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging


ANOMALY_ID = "cost-" + "1" * 64
EVIDENCE_ID = "evidence-" + "2" * 64
PATH = "/assistant/conversations/own/anomaly-explanations"


def selection():
    return {
        "start_date": "2024-06-01", "end_date": "2024-06-08",
        "group_by": "service", "currency": "EUR", "absolute_threshold": "100.00",
        "deviation_threshold_percent": None, "min_absolute_increase": "0.01",
    }


def request_body():
    return {"anomaly_id": ANOMALY_ID, "evidence_id": EVIDENCE_ID, "definition": selection()}


def detector_snapshot():
    """Independent synthetic observed-cost example; not detector output."""
    return {
        "contract_version": 1, "source": "billing_summary_v2", "definition": selection(),
        "current_period": {"start_date": "2024-06-01", "end_date": "2024-06-08", "timezone": "UTC"},
        "baseline_period": None,
        "current_quality": {"data_status": "available", "record_count": 2,
                            "missing_dimension_count": 0, "excluded_undated_count": 0},
        "baseline_quality": None, "evaluation_status": "evaluated",
        "completeness": "not_verified", "limitations": ["Synthetic provider boundary fixture"],
        "alerts": [{
            "id": ANOMALY_ID, "evidence_id": EVIDENCE_ID,
            "group_value": "Compute", "subscription_id": "subscription-a", "currency": "EUR",
            "current_cost": "125.25", "current_record_count": 2,
            "baseline_cost": None, "baseline_record_count": None,
            "delta_amount": None, "deviation_percent": None,
            "threshold_status": "triggered", "deviation_status": "disabled",
            "trigger_reasons": ["absolute_threshold"], "cause_status": "not_established",
        }],
        "assessments": [],
    }


@pytest.fixture
def anomaly_api(api, monkeypatch):
    provider = MagicMock(spec_set=["evaluate"])
    provider.evaluate.return_value = detector_snapshot()
    monkeypatch.setitem(api.app.dependency_overrides, get_anomaly_provider, lambda: provider)
    assistant = MagicMock(spec_set=["answer"])
    monkeypatch.setattr(api.app.state, "assistant_service", assistant)
    api.provider = provider
    api.assistant = assistant
    return api


def assert_no_generation(api):
    api.embedding.embed.assert_not_called()
    api.vector.search_chunks.assert_not_called()
    api.assistant.answer.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("authorization,tenant,expected", [
    (False, "tenant-a", 401), (True, None, 400), (True, "tenant-b", 403),
])
def test_auth_and_membership_precede_provider_and_writes(anomaly_api, authorization, tenant, expected):
    api = anomaly_api
    before = rows(api.db, "messages")
    response = call(api, "POST", PATH,
                    headers=headers(tenant=tenant) if authorization else [], json=request_body())
    assert response.status_code == expected, response.text
    api.provider.evaluate.assert_not_called()
    api.spies["fetch_conversation"].assert_not_called()
    api.spies["append_message"].assert_not_called()
    assert rows(api.db, "messages") == before
    assert_no_generation(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_foreign_other_owner_and_missing_conversations_are_indistinguishable(anomaly_api):
    api = anomaly_api
    before = rows(api.db, "messages")
    responses = [call(api, "POST", f"/assistant/conversations/{identifier}/anomaly-explanations",
                      headers=headers(), json=request_body())
                 for identifier in ("foreign-marker", "other-owner", "nonexistent")]
    assert [response.status_code for response in responses] == [404, 404, 404]
    assert all(response.json() == {"detail": "Conversation not found."} for response in responses)
    api.provider.evaluate.assert_not_called()
    api.spies["append_message"].assert_not_called()
    assert rows(api.db, "messages") == before
    assert_no_generation(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_explanation_persists_exact_numeric_evidence_and_reopens_without_generation(anomaly_api):
    api = anomaly_api
    response = call(api, "POST", PATH, headers=headers(), json=request_body())
    assert response.status_code == 201, response.text
    result = response.json()
    api.provider.evaluate.assert_called_once_with("tenant-a", selection())
    assert result["retrieved_context"] == []
    assert result["user_message"]["metadata"] == {"anomaly_id": ANOMALY_ID, "evidence_id": EVIDENCE_ID}
    assistant = result["assistant_message"]
    assert assistant["metadata"]["capability"] == "anomaly_explanation"
    explanation = assistant["metadata"]["anomaly_explanation"]
    assert explanation["cause_status"] == "not_established"
    evidence = explanation["evidence"]
    assert evidence["anomaly"] == detector_snapshot()["alerts"][0]
    assert evidence["definition"] == selection()
    assert evidence["current_period"] == detector_snapshot()["current_period"]
    assert evidence["source"] == "billing_summary_v2"
    assert evidence["completeness"] == "not_verified"
    assert "125.25 EUR" in assistant["content"] and "100.00 EUR" in assistant["content"]
    assert "no demuestra una causa" in assistant["content"]
    assert [item.kwargs["role"] for item in api.spies["append_message"].call_args_list] == ["user", "assistant"]
    assert all(item.kwargs["requester_id"] == "alice" for item in api.spies["append_message"].call_args_list)
    reopened = call(api, "GET", "/assistant/conversations/own", headers=headers())
    assert reopened.status_code == 200
    assert reopened.json()["messages"][-1] == assistant
    for user, tenant in (("other-a", "tenant-a"), ("bob", "tenant-b")):
        assert call(api, "GET", "/assistant/conversations/own", headers=headers(user, tenant)).status_code == 404
    assert_no_generation(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("failure,expected,detail", [
    ("unavailable", 503, "Anomaly detection is unavailable."),
    ("upstream_error", 503, "Anomaly detection is unavailable."),
    ("invalid", 502, "Invalid anomaly evidence."),
    ("inconsistent", 502, "Invalid anomaly evidence."),
    ("stale", 409, "Anomaly evidence changed. Refresh the evaluation."),
    ("missing", 404, "Anomaly not found in this evaluation."),
    ("invalid_selection", 422, "Invalid anomaly selection."),
    ("ambiguous", 409, {"code": "ambiguous_cost_source"}),
])
def test_failed_provider_or_evidence_never_persists_messages(anomaly_api, failure, expected, detail, capsys, caplog):
    api = anomaly_api
    marker = "synthetic-private-upstream-diagnostic"
    before = rows(api.db, "messages")
    errors = {"unavailable": DetectorUnavailable(marker), "upstream_error": RuntimeError(marker),
              "invalid_selection": InvalidSelection(marker), "ambiguous": AmbiguousCostSource(marker)}
    if failure in errors:
        api.provider.evaluate.side_effect = errors[failure]
    else:
        evidence = detector_snapshot()
        if failure == "invalid":
            evidence["contract_version"] = 999
        elif failure == "inconsistent":
            evidence["alerts"][0]["current_cost"] = "1.00"
        elif failure == "stale":
            evidence["alerts"][0]["evidence_id"] = "evidence-" + "3" * 64
        elif failure == "missing":
            evidence["alerts"] = []
        api.provider.evaluate.return_value = evidence
    response = call(api, "POST", PATH, headers=headers(), json=request_body())
    assert response.status_code == expected, response.text
    assert response.json() == {"detail": detail}
    api.spies["append_message"].assert_not_called()
    assert rows(api.db, "messages") == before
    captured = capsys.readouterr()
    assert marker not in response.text + captured.out + captured.err + caplog.text
    assert_no_generation(api)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("location,key,value", [
    ("request", "tenant_id", "tenant-b"), ("request", "user_id", "bob"),
    ("request", "current_cost", "999999.99"), ("request", "evidence", {"cause": "invented"}),
    ("definition", "tenant_id", "tenant-b"), ("definition", "observed_cost", "999999.99"),
])
def test_client_authority_and_evidence_fields_are_rejected_before_provider(anomaly_api, location, key, value):
    api = anomaly_api
    body = request_body()
    (body if location == "request" else body["definition"])[key] = value
    response = call(api, "POST", PATH, headers=headers(), json=body)
    assert response.status_code == 422, response.text
    api.provider.evaluate.assert_not_called()
    api.spies["append_message"].assert_not_called()
    assert_no_generation(api)


class SyntheticDefinition(BaseModel):
    """Explicit upstream schema double; only tests adapter argument forwarding."""
    start_date: date
    end_date: date
    group_by: str
    deviation_threshold_percent: str | None = None

    @property
    def baseline_period(self):
        if self.deviation_threshold_percent is None:
            return None
        return BillingPeriod(start_date=self.start_date - (self.end_date - self.start_date),
                             end_date=self.start_date)


def synthetic_billing(start, end):
    return {
        "contract_version": 2, "period": {"start_date": start, "end_date": end, "timezone": "UTC"},
        "group_by": "service", "tag_key": None, "data_status": "available",
        "totals": [{"currency": "EUR", "cost": "125.25", "record_count": 2}],
        "groups": [{"currency": "EUR", "cost": "125.25", "record_count": 2,
                    "subscription_id": "subscription-a", "value": "Compute"}],
        "missing_dimension_count": 0, "excluded_undated_count": 0,
        "monthly_spend": None, "savings_identified": None, "open_ingestions": 0, "currency": "EUR",
    }


def install_upstream_doubles(monkeypatch):
    evaluated = MagicMock(spec_set=["model_dump"])
    evaluated.model_dump.return_value = {"explicit_synthetic_upstream": True}
    evaluate = MagicMock(return_value=evaluated)
    modules = {"app.schemas.anomalies": SimpleNamespace(AnomalyDefinition=SyntheticDefinition),
               "app.services.anomalies": SimpleNamespace(evaluate_anomalies=evaluate)}
    loader = MagicMock(side_effect=lambda name: modules[name])
    monkeypatch.setattr(explanations, "import_module", loader)
    return loader, evaluate, evaluated


@pytest.mark.parametrize("with_baseline", [False, True])
def test_adapter_forwards_authorized_scope_and_typed_billing_to_explicit_upstream_double(monkeypatch, with_baseline):
    loader, evaluate, evaluated = install_upstream_doubles(monkeypatch)
    database = MagicMock(spec_set=["fetch_billing_summary"])
    start, end = date(2024, 6, 1), date(2024, 6, 8)
    database.fetch_billing_summary.side_effect = lambda tenant, start_date, end_date, **kwargs: synthetic_billing(start_date, end_date)
    chosen = {**selection(), "deviation_threshold_percent": "20.00" if with_baseline else None}
    result = BillingAnomalyProvider(database).evaluate("tenant-a", chosen)
    assert result == {"explicit_synthetic_upstream": True}
    assert loader.call_args_list == [mock_call("app.schemas.anomalies"), mock_call("app.services.anomalies")]
    expected = [mock_call("tenant-a", start_date=start, end_date=end, group_by="service", tag_key=None)]
    if with_baseline:
        expected.append(mock_call("tenant-a", start_date=start - timedelta(days=7), end_date=start,
                                  group_by="service", tag_key=None))
    assert database.fetch_billing_summary.call_args_list == expected
    evaluate.assert_called_once()
    definition, current, baseline = evaluate.call_args.args
    assert isinstance(definition, SyntheticDefinition)
    assert isinstance(current, BillingSummary) and current.period.start_date == start
    assert evaluate.call_args.kwargs == {"tenant_id": "tenant-a"}
    if with_baseline:
        assert isinstance(baseline, BillingSummary) and baseline.period.end_date == start
    else:
        assert baseline is None
    evaluated.model_dump.assert_called_once_with(mode="json")


@pytest.mark.parametrize("failure", [ImportError, AttributeError])
def test_adapter_missing_detector_fails_closed_without_cost_reads(monkeypatch, failure):
    monkeypatch.setattr(explanations, "import_module", MagicMock(side_effect=failure("synthetic missing dependency")))
    database = MagicMock(spec_set=["fetch_billing_summary"])
    with pytest.raises(DetectorUnavailable):
        BillingAnomalyProvider(database).evaluate("tenant-a", selection())
    database.fetch_billing_summary.assert_not_called()


def test_adapter_invalid_selection_is_rejected_before_cost_reads(monkeypatch):
    _, evaluate, _ = install_upstream_doubles(monkeypatch)
    database = MagicMock(spec_set=["fetch_billing_summary"])
    invalid = {**selection(), "start_date": "not-a-date"}
    with pytest.raises(InvalidSelection):
        BillingAnomalyProvider(database).evaluate("tenant-a", invalid)
    database.fetch_billing_summary.assert_not_called()
    evaluate.assert_not_called()
