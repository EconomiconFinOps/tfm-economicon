from datetime import date
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from sqlalchemy import text
from app.schemas.assistant import AzureCostSelection
from app.schemas.billing import AmbiguousCostSource
from app.services.azure_cost_questions import AzureCostQuestionService
from billing_support import billing_schema, cost_reference, insert_cost, insert_run, summary
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging

SELECTION = {"group_by": "service", "value": "Compute", "start_date": "2024-06-01", "end_date": "2024-07-01"}
PROVENANCE = {"ingestion_ids": ["run-a"], "first_usage_date": "2024-06-01", "last_usage_date": "2024-06-30", "observed_day_count": 2}
PATH = "/assistant/conversations/own/messages"

def dataset(**changes):
    return summary(provenance=PROVENANCE, **changes)

@pytest.mark.parametrize("changes", [{"tenant_id": "tenant-b"}, {"group_by": "owner"}, {"start_date": "2024-06-31"}, {"end_date": None}, {"end_date": "2024-06-01"}, {"value": " "}, {"value": "x\x00y"}, {"value": "a" * 257}, {"value": "\nCompute"}, {"start_date": 1717200000}])
def test_strict_selection(changes):
    with pytest.raises(ValidationError):
        AzureCostSelection.model_validate(SELECTION | changes)

def test_exact_money_separate_currencies_stable_scoped_evidence():
    db = Mock()
    db.fetch_billing_summary.return_value = dataset()
    selection = AzureCostSelection.model_validate(SELECTION)
    first = AzureCostQuestionService().answer(db, "tenant-a", selection)
    second = AzureCostQuestionService().answer(db, "tenant-a", selection)
    for amount in ("11.01 EUR", "0.00 GBP", "9007199254740993.01 USD"):
        assert amount in first["content"]
    assert first["cost_evidence"]["id"] == second["cost_evidence"]["id"]
    assert first["cost_evidence"]["summary"]["totals"] == summary()["totals"]
    assert first["cost_evidence"]["provenance"] == PROVENANCE
    assert first["cost_evidence"]["status"] == "partial"
    assert "no garantiza cobertura completa" in first["content"]
    db.fetch_billing_summary.assert_called_with("tenant-a", start_date=date(2024, 6, 1), end_date=date(2024, 7, 1), group_by="service", selected_subscription=None, selected_value="Compute", include_provenance=True)
    assert AzureCostQuestionService().answer(db, "tenant-b", selection)["cost_evidence"]["id"] != first["cost_evidence"]["id"]

@pytest.mark.parametrize("totals,status,phrase", [([], "no_data", "no equivale a gasto cero"), ([{"currency": "EUR", "cost": "0.00", "record_count": 1}], "ok", "0.00 EUR"), ([{"currency": "EUR", "cost": "-1.01", "record_count": 1}], "ok", "-1.01 EUR")])
def test_empty_zero_and_credit(totals, status, phrase):
    db = Mock()
    db.fetch_billing_summary.return_value = dataset(totals=totals, data_status="available", missing_dimension_count=0, excluded_undated_count=0)
    result = AzureCostQuestionService().answer(db, "tenant-a", AzureCostSelection.model_validate(SELECTION))
    assert result["cost_evidence"]["status"] == status
    assert phrase in result["content"]

def test_december_default_month(monkeypatch):
    from app.services import azure_cost_questions
    from datetime import datetime, timezone
    class Clock:
        @staticmethod
        def now(tz):
            return datetime(2026, 12, 31, tzinfo=timezone.utc)
    monkeypatch.setattr(azure_cost_questions, "datetime", Clock)
    db = Mock()
    db.fetch_billing_summary.return_value = dataset()
    result = AzureCostQuestionService().answer(db, "tenant-a", AzureCostSelection(group_by="account"))
    assert result["cost_evidence"]["selection"]["start_date"] == "2026-12-01"
    assert result["cost_evidence"]["selection"]["end_date"] == "2027-01-01"

@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_persisted_chat_evidence_without_rag(api):
    api.spies["fetch_billing_summary"].return_value = dataset()
    response = call(api, "POST", PATH, headers=headers(), json={"content": "Cuanto hemos gastado", "cost_query": SELECTION})
    assert response.status_code == 201, response.text
    body = response.json()
    evidence = body["assistant_message"]["metadata"]["cost_evidence"]
    assert evidence["selection"]["value"] == "Compute"
    assert evidence["summary"]["totals"] == summary()["totals"]
    assert body["retrieved_context"] == []
    api.embedding.embed.assert_not_called()
    api.vector.search_chunks.assert_not_called()
    persisted = call(api, "GET", "/assistant/conversations/own", headers=headers()).json()
    assert persisted["messages"][1]["metadata"]["cost_evidence"] == evidence

@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("changes", [{"start_date": "2024-07-01"}, {"tenant_id": "tenant-b"}])
def test_invalid_request_no_effects(api, changes):
    response = call(api, "POST", PATH, headers=headers(), json={"content": "cost", "cost_query": SELECTION | changes})
    assert response.status_code == 422
    api.spies["fetch_billing_summary"].assert_not_called()
    api.spies["append_message"].assert_not_called()

@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("conversation,tenant,expected", [("foreign-marker", "tenant-a", 404), ("other-owner", "tenant-a", 404), ("own", "tenant-b", 403)])
def test_unauthorized_no_cost_read(api, conversation, tenant, expected):
    response = call(api, "POST", PATH.replace("own", conversation), headers=headers(tenant=tenant), json={"content": "cost", "cost_query": SELECTION})
    assert response.status_code == expected
    api.spies["fetch_billing_summary"].assert_not_called()
    api.spies["append_message"].assert_not_called()

@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_conflict_without_messages(api):
    api.spies["fetch_billing_summary"].side_effect = AmbiguousCostSource()
    response = call(api, "POST", PATH, headers=headers(), json={"content": "cost", "cost_query": SELECTION})
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "ambiguous_cost_source"}}
    api.spies["append_message"].assert_not_called()

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
@pytest.mark.parametrize("group,value,subscription,totals,ids,days", [
    ("service", "Compute", "sub-a", [("EUR", "10.00", 1), ("GBP", "0.00", 1), ("USD", "9007199254740993.01", 1)], ["run-a"], 2),
    ("subscription", "sub-b", None, [("EUR", "-1.00", 3)], ["run-b"], 1),
    ("account", "acct-a", None, [("EUR", "12.01", 2), ("GBP", "0.00", 1), ("USD", "9007199254740993.01", 1)], ["run-a"], 3),
    ("service", "Compute", "foreign-sub", [], [], 0),
    ("account", "foreign-account", None, [], [], 0),
    ("service", "x' OR 1=1--", None, [], [], 0),
])
def test_real_cost_sql(cost_reference, api, group, value, subscription, totals, ids, days):
    with api.db.engine.begin() as connection:
        connection.execute(text("UPDATE azure_cost_records SET billing_account_id = CASE WHEN tenant_id = 'tenant-b' THEN 'foreign-account' WHEN subscription_id = 'sub-a' THEN 'acct-a' ELSE 'acct-b' END"))
    selection = SELECTION | {"group_by": group, "value": value, "subscription_id": subscription}
    direct = AzureCostQuestionService().answer(api.db, "tenant-a", AzureCostSelection.model_validate(selection))
    response = call(api, "POST", PATH, headers=headers(), json={"content": "cost", "cost_query": selection})
    assert response.status_code == 201, response.text
    evidence = response.json()["assistant_message"]["metadata"]["cost_evidence"]
    assert evidence["summary"]["totals"] == [{"currency": cur, "cost": amount, "record_count": n} for cur, amount, n in totals]
    assert evidence["summary"] == direct["cost_evidence"]["summary"]
    assert evidence["provenance"]["ingestion_ids"] == ids
    assert evidence["provenance"]["observed_day_count"] == days
    assert (evidence["status"] == "no_data") == (not totals)

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_filter_does_not_hide_overlap(cost_reference, api):
    with api.db.engine.begin() as connection:
        insert_run(connection, "overlap")
        insert_cost(connection, "other-service", run="overlap", day="2024-06-01", service="NotCompute")
    response = call(api, "POST", PATH, headers=headers(), json={"content": "cost", "cost_query": SELECTION})
    assert response.status_code == 409, response.text
    api.spies["append_message"].assert_not_called()
