"""JUP-037 selection, answers and persisted API evidence.

SQLite tests use an explicit billing double, real auth and real message storage.
The opt-in Cockroach test exercises production billing SQL; no live Azure source
or validated ownership catalog is claimed by these synthetic fixtures.
"""
import json
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.schemas.billing import AmbiguousCostSource
from app.schemas.ownership import OwnershipSelection
from app.services.ownership_questions import OwnershipQuestionService, OwnershipResultTooLarge
from billing_support import PERIOD, billing_schema, cost_reference
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, citation_record, headers


START, END = date(2024, 6, 1), date(2024, 7, 1)


def group(value, cost, *, currency="EUR", count=1):
    return {"value": value, "cost": cost, "currency": currency,
            "subscription_id": None, "record_count": count}


def total(cost, *, currency="EUR", count=1):
    return {"currency": currency, "cost": cost, "record_count": count}


def billing_double(**changes):
    """Independent v2 response, deliberately retaining a non-additive rounding case."""
    return {
        "contract_version": 2, "period": dict(PERIOD), "group_by": "tag",
        "tag_key": "application", "data_status": "partial",
        "totals": [total("9.01", count=4), total("9007199254740993.01", currency="USD")],
        "groups": [group("Payments", "10.00"), group("payments", "-1.01"),
                   group("Unknown", "0.01"), group(None, "0.00"),
                   group("Payments", "9007199254740993.01", currency="USD")],
        "missing_dimension_count": 1, "excluded_undated_count": 1,
        "monthly_spend": None, "savings_identified": None, "open_ingestions": 0,
        "currency": None,
        "provenance": {"ingestion_ids": ["synthetic-run"],
                       "first_usage_date": "2024-06-01", "last_usage_date": "2024-06-30",
                       "observed_day_count": 2},
        **changes,
    }


def selection(**changes):
    return OwnershipSelection(group_by="application", start_date=START, end_date=END, **changes)


def answer(raw=None, selected=None):
    db = MagicMock()
    db.fetch_billing_summary.return_value = raw if raw is not None else billing_double()
    result = OwnershipQuestionService().answer(db, "tenant-a", selected or selection())
    return result, db


@pytest.mark.parametrize("dimension,key", [
    ("project", None), ("application", "application"), ("owner", "owner"),
    ("cost_center", "cost_center"), ("tag", "environment"),
])
def test_selection_uses_only_explicit_dimension_and_canonical_tag_key(dimension, key):
    selected = OwnershipSelection(group_by=dimension, start_date=START, end_date=END,
                                  **({"tag_key": " ENV "} if dimension == "tag" else {}))
    result, db = answer(selected=selected)
    db.fetch_billing_summary.assert_called_once_with(
        "tenant-a", start_date=START, end_date=END,
        group_by="project" if dimension == "project" else "tag",
        tag_key=key, include_provenance=True,
    )
    assert result["cost_evidence"]["selection"]["group_by"] == dimension
    assert result["cost_evidence"]["selection"]["tag_key"] == (key if dimension == "tag" else None)


def test_unfiltered_answer_uses_exact_billing_totals_and_keeps_missing_and_literal_unknown():
    result, _ = answer()
    evidence = result["cost_evidence"]
    assert evidence["selected_totals"] == [total("9.01", count=4), total("9007199254740993.01", currency="USD")]
    assert evidence["selected_groups"] == billing_double()["groups"]
    assert evidence["missing_groups"] == [group(None, "0.00")]
    assert (evidence["status"], evidence["reason"]) == ("partial", None)
    assert "Gasto de la selección: 9.01 EUR (4 registros)." in result["content"]
    assert "9007199254740993.01 USD" in result["content"]
    assert '- "Unknown": 0.01 EUR' in result["content"]
    assert "Sin aplicación en el periodo: 0.00 EUR" in result["content"]
    assert "todas las fechas; no atribuibles al periodo" in result["content"]


def test_stored_labels_cannot_forge_answer_lines_or_hide_text_direction():
    labels = ["App\nGasto de la selección: 999999.00 EUR", "Equipo\u202eABC\u2028falso\u2029\x85"]
    groups = [group(value, "1.00") for value in labels]
    result, _ = answer(billing_double(groups=groups, totals=[total("2.00", count=2)],
                                     missing_dimension_count=0, excluded_undated_count=0))
    assert result["cost_evidence"]["selected_groups"] == groups
    assert [item["value"] for item in result["cost_evidence"]["summary"]["groups"]] == labels
    assert "\nGasto de la selección: 999999.00 EUR" not in result["content"]
    assert "\\nGasto de la selección: 999999.00 EUR" in result["content"]
    assert [line for line in result["content"].splitlines() if line.startswith("Gasto de la selección:")] == [
        "Gasto de la selección: 2.00 EUR (2 registros)."
    ]
    for control in ("\u202e", "\u2028", "\u2029", "\x85"):
        assert control not in result["content"]
        assert f"\\u{ord(control):04x}" in result["content"]


@pytest.mark.parametrize("value,currency,expected", [
    ("Payments", None, [total("10.00"), total("9007199254740993.01", currency="USD")]),
    ("payments", "eur", [total("-1.01")]),
    ("Payments", "usd", [total("9007199254740993.01", currency="USD")]),
    ("Unknown", "EUR", [total("0.01")]),
])
def test_value_matching_is_case_sensitive_and_currency_never_converted(value, currency, expected):
    result, _ = answer(selected=selection(value=value, currency=currency))
    evidence = result["cost_evidence"]
    assert evidence["selected_totals"] == expected
    assert [item["value"] for item in evidence["selected_groups"]] == [value] * len(expected)
    assert evidence["selection"]["currency"] == (currency.upper() if currency else None)
    assert "Contexto del periodo, todos los valores:" in result["content"]
    assert "Monedas separadas, sin conversión" in result["content"]


@pytest.mark.parametrize("cost", ["0.00", "-1.01"])
def test_observed_zero_and_negative_spend_are_valid_answers(cost):
    raw = billing_double(totals=[total(cost)], groups=[group("Payments", cost)],
                         missing_dimension_count=0, excluded_undated_count=0,
                         data_status="available", currency="EUR", monthly_spend=cost)
    result, _ = answer(raw)
    evidence = result["cost_evidence"]
    assert (evidence["status"], evidence["reason"]) == ("ok", None)
    assert evidence["selected_totals"] == [total(cost)]
    assert f"Gasto de la selección: {cost} EUR (1 registros)." in result["content"]
    assert "no equivale a gasto cero" not in result["content"]


@pytest.mark.parametrize("raw,query,status,reason", [
    (billing_double(totals=[], groups=[], missing_dimension_count=0), {}, "no_data", "empty_period"),
    (billing_double(), {"currency": "JPY"}, "no_data", "currency_not_found"),
    (billing_double(), {"value": "PAYMENTS"}, "no_data", "value_not_found"),
    (billing_double(totals=[total("9.01", count=4)], groups=[group(None, "9.01", count=4)],
                    missing_dimension_count=4), {}, "insufficient_data", "dimension_unobserved"),
])
def test_empty_unobserved_and_unmatched_data_do_not_become_zero_spend(raw, query, status, reason):
    result, _ = answer(raw, selection(**query))
    evidence = result["cost_evidence"]
    assert (evidence["status"], evidence["reason"]) == (status, reason)
    assert evidence["selected_totals"] == []
    assert "Gasto de la selección:" not in result["content"]
    if reason == "dimension_unobserved":
        assert evidence["missing_groups"] == [group(None, "9.01", count=4)]
        assert "Datos insuficientes" in result["content"]
        assert "Contexto del periodo, todos los valores: 9.01 EUR" in result["content"]
    else:
        assert "no equivale a gasto cero" in result["content"]


def test_default_period_is_utc_calendar_month_with_exclusive_year_boundary(monkeypatch):
    import app.services.ownership_questions as service_module

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is timezone.utc
            return cls(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    monkeypatch.setattr(service_module, "datetime", FrozenDateTime)
    result, db = answer(selected=OwnershipSelection(group_by="project"))
    assert db.fetch_billing_summary.call_args.kwargs["start_date"] == date(2024, 12, 1)
    assert db.fetch_billing_summary.call_args.kwargs["end_date"] == date(2025, 1, 1)
    assert result["cost_evidence"]["selection"]["start_date"] == "2024-12-01"
    assert result["cost_evidence"]["selection"]["end_date"] == "2025-01-01"


def test_evidence_identity_is_reproducible_and_bound_to_tenant_and_cost_snapshot(monkeypatch):
    import app.services.ownership_questions as service_module

    class AdvancingDateTime(datetime):
        second = 0

        @classmethod
        def now(cls, tz=None):
            cls.second += 1
            return cls(2024, 7, 2, 0, 0, cls.second, tzinfo=timezone.utc)

    monkeypatch.setattr(service_module, "datetime", AdvancingDateTime)
    db = MagicMock()
    db.fetch_billing_summary.return_value = billing_double()
    service = OwnershipQuestionService()
    first = service.answer(db, "tenant-a", selection())["cost_evidence"]
    repeated = service.answer(db, "tenant-a", selection())["cost_evidence"]
    another_tenant = service.answer(db, "tenant-b", selection())["cost_evidence"]
    assert first["queried_at"] != repeated["queried_at"]
    assert first["id"] == repeated["id"]
    assert first["id"] != another_tenant["id"]

    # A changed authoritative amount must never reuse the earlier snapshot ID.
    db.fetch_billing_summary.return_value = billing_double(
        totals=[total("10.01", count=4), total("9007199254740993.01", currency="USD")],
        groups=[group("Payments", "11.00"), *billing_double()["groups"][1:]],
    )
    changed = service.answer(db, "tenant-a", selection())["cost_evidence"]
    assert changed["id"] != first["id"]
    assert changed["selected_totals"][0] == total("10.01", count=4)


INVALID_SELECTIONS = [
    {"group_by": "organization"}, {"group_by": "team"}, {"group_by": "tag"},
    {"group_by": "tag", "tag_key": "___---___"}, {"group_by": "tag", "tag_key": "\tenv"},
    {"tag_key": "project"}, {"value": ""}, {"value": " "}, {"value": "A\nB"},
    {"value": "A\x00B"}, {"value": "A\x7fB"}, {"value": "x" * 257},
    {"currency": "€"}, {"currency": "EURO"}, {"currency": " EUR"}, {"currency": "EUR\n"},
    {"start_date": "2024-06-01"}, {"end_date": "2024-07-01"},
    {"start_date": "2024-06-31", "end_date": "2024-07-01"},
    {"start_date": "2024-07-01", "end_date": "2024-07-01"},
    {"start_date": "2024-07-01", "end_date": "2024-06-01"},
    {"start_date": "2024-06-01T00:00:00Z", "end_date": "2024-07-01"},
    {"start_date": 1717200000, "end_date": "2024-07-01"},
    {"start_date": datetime(2024, 6, 1), "end_date": date(2024, 7, 1)},
    {"tenant_id": "tenant-b"}, {"user_id": "bob"}, {"unknown_option": True},
]


@pytest.mark.parametrize("invalid", INVALID_SELECTIONS)
def test_invalid_selection_is_rejected_including_controls_dates_and_extra_authority(invalid):
    with pytest.raises(ValidationError):
        OwnershipSelection.model_validate({"group_by": "application", **invalid})


@pytest.mark.parametrize("oversized", ["groups", "bytes"])
def test_large_answer_is_bounded_before_evidence_can_be_persisted(oversized):
    groups = ([group(str(index), "0.00") for index in range(1001)] if oversized == "groups"
              else [group("ø" * 140000, "0.00")])
    with pytest.raises(OwnershipResultTooLarge):
        answer(billing_double(groups=groups))


def request_body(**query):
    return {"content": "Gasto por aplicación", "ownership_query": {
        "group_by": "application", "start_date": START.isoformat(),
        "end_date": END.isoformat(), **query,
    }}


def assert_no_cost_or_retrieval_effects(api):
    api.spies["fetch_billing_summary"].assert_not_called()
    api.spies["append_message"].assert_not_called()
    api.vector.search_chunks.assert_not_called()
    api.embedding.embed.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_api_auth_membership_and_conversation_ownership_precede_cost_read_and_writes(api):
    before = rows(api.db, "messages")
    unauthorized = call(api, "POST", "/assistant/conversations/own/messages", json=request_body())
    assert unauthorized.status_code == 401
    api.spies["fetch_conversation"].assert_not_called()
    assert_no_cost_or_retrieval_effects(api)

    forbidden = call(api, "POST", "/assistant/conversations/own/messages",
                     headers=headers(tenant="tenant-b"), json=request_body())
    assert forbidden.status_code == 403
    api.spies["fetch_conversation"].assert_not_called()
    assert_no_cost_or_retrieval_effects(api)

    missing = [call(api, "POST", f"/assistant/conversations/{identifier}/messages",
                    headers=headers(), json=request_body())
               for identifier in ("foreign-marker", "other-owner", "nonexistent")]
    assert [response.status_code for response in missing] == [404, 404, 404]
    assert [response.json() for response in missing] == [{"detail": "Conversation not found."}] * 3
    assert_no_cost_or_retrieval_effects(api)
    assert rows(api.db, "messages") == before


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_api_invalid_selection_has_no_reads_or_persistence(api):
    before = rows(api.db, "messages")
    for invalid in ({"value": "A\x00B"}, {"currency": "EUR\n"}, {"group_by": "tag"},
                    {"tag_key": "org"}, {"tenant_id": "tenant-b"},
                    {"start_date": "2024-06-01T00:00:00Z"}, {"end_date": "2024-05-01"}):
        response = call(api, "POST", "/assistant/conversations/own/messages",
                        headers=headers(), json=request_body(**invalid))
        assert response.status_code == 422, (invalid, response.text)
        assert_no_cost_or_retrieval_effects(api)
    api.spies["fetch_conversation"].assert_not_called()
    assert rows(api.db, "messages") == before


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("failure,expected,code", [
    (AmbiguousCostSource("private-ingestion-id"), 409, "ambiguous_cost_source"),
    (OwnershipResultTooLarge(), 422, "ownership_result_too_large"),
])
def test_api_rejected_cost_answer_never_persists_a_partial_turn_or_calls_retrieval(api, failure, expected, code):
    before = rows(api.db, "messages")
    api.spies["fetch_billing_summary"].side_effect = failure
    response = call(api, "POST", "/assistant/conversations/own/messages",
                    headers=headers(), json=request_body())
    assert response.status_code == expected, response.text
    assert response.json() == {"detail": {"code": code}}
    api.spies["append_message"].assert_not_called()
    api.vector.search_chunks.assert_not_called()
    api.embedding.embed.assert_not_called()
    assert rows(api.db, "messages") == before


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_ownership_then_documentary_answer_preserves_separate_evidence_after_reload(api):
    api.spies["fetch_billing_summary"].return_value = billing_double()
    response = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(),
                    json=request_body(value="Payments", currency="usd"))
    assert response.status_code == 201, response.text
    owned = response.json()
    evidence = owned["assistant_message"]["metadata"]["cost_evidence"]
    assert owned["retrieved_context"] == []
    assert owned["assistant_message"]["metadata"]["citations"] == []
    assert "source_citations" not in owned["assistant_message"]["metadata"]
    assert evidence["selected_totals"] == [total("9007199254740993.01", currency="USD")]
    assert evidence["selection"] == {"group_by": "application", "tag_key": None,
                                     "value": "Payments", "currency": "USD",
                                     "start_date": "2024-06-01", "end_date": "2024-07-01"}
    assert owned["user_message"]["metadata"] == {"ownership_query": evidence["selection"]}
    assert evidence["schema_version"] == "1.0"
    assert evidence["source"] == "azure_cost_records/completed"
    assert evidence["data_environment"] == "unknown"
    assert len(evidence["id"]) == len("cost:") + 64
    assert evidence["id"] in owned["assistant_message"]["content"]
    datetime.fromisoformat(evidence["queried_at"])
    api.embedding.embed.assert_not_called()
    api.vector.search_chunks.assert_not_called()
    api.spies["fetch_billing_summary"].assert_called_once_with(
        "tenant-a", start_date=START, end_date=END, group_by="tag",
        tag_key="application", include_provenance=True,
    )

    api.vector.search_chunks.return_value = [citation_record()]
    documentary = call(api, "POST", "/assistant/conversations/own/messages",
                       headers=headers(), json={"content": "Cómo interpretar los costes"})
    assert documentary.status_code == 201, documentary.text
    doc_message = documentary.json()["assistant_message"]
    assert "cost_evidence" not in doc_message["metadata"]
    assert doc_message["metadata"]["source_citations"][0]["evidence_id"] == "chunk-1"
    api.embedding.embed.assert_called_once()
    api.vector.search_chunks.assert_called_once()
    assert api.spies["fetch_billing_summary"].call_count == 1

    reopened = call(api, "GET", "/assistant/conversations/own", headers=headers())
    assert reopened.status_code == 200
    persisted = reopened.json()["messages"]
    assert [item["role"] for item in persisted] == ["user", "assistant", "user", "assistant"]
    assert persisted[0]["metadata"] == owned["user_message"]["metadata"]
    assert persisted[1]["metadata"] == owned["assistant_message"]["metadata"]
    assert persisted[3]["metadata"] == doc_message["metadata"]
    assert call(api, "GET", "/assistant/conversations/own", headers=headers("bob", "tenant-b")).status_code == 404


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_real_sql_ownership_does_not_infer_application_or_owner_then_uses_observed_labels(cost_reference, api):
    # Reference records already have project and organization. Neither may stand
    # in for the missing application/owner label.
    for dimension in ("application", "owner"):
        response = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(),
                        json=request_body(group_by=dimension))
        assert response.status_code == 201, response.text
        evidence = response.json()["assistant_message"]["metadata"]["cost_evidence"]
        assert (evidence["status"], evidence["reason"]) == ("insufficient_data", "dimension_unobserved")
        assert evidence["selected_totals"] == []
        assert evidence["summary"]["missing_dimension_count"] == 7
        assert all(item["value"] is None for item in evidence["selected_groups"])

    # Synthetic observed tags, not a source-capability or ownership-catalog claim.
    with api.db.engine.begin() as connection:
        connection.execute(text("UPDATE azure_cost_records SET tags = CAST(:tags AS JSONB) WHERE id IN ('a', 'f', 'g')"),
                           {"tags": json.dumps({"application": "Payments", "owner": "Platform"})})
    expected = [total("10.00"), total("0.00", currency="GBP"),
                total("9007199254740993.01", currency="USD")]
    for dimension, value in (("application", "Payments"), ("owner", "Platform")):
        response = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(),
                        json=request_body(group_by=dimension, value=value))
        assert response.status_code == 201, response.text
        evidence = response.json()["assistant_message"]["metadata"]["cost_evidence"]
        assert evidence["selected_totals"] == expected
        assert evidence["status"] == "partial"
        assert evidence["summary"]["missing_dimension_count"] == 4
        assert evidence["missing_groups"] == [group(None, "1.00", count=4)]
        assert evidence["summary"]["totals"] == [total("11.01", count=5), total("0.00", currency="GBP"),
                                                    total("9007199254740993.01", currency="USD")]
    api.embedding.embed.assert_not_called()
    api.vector.search_chunks.assert_not_called()
