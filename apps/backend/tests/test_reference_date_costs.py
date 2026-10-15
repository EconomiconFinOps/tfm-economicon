"""JUP-119: costs after the reference date are never read, whichever read asks for them."""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.schemas.ownership import OwnershipSelection
from app.services import reference_date
from app.services.ownership_questions import OwnershipQuestionService
from billing_support import billing_schema, insert_cost, insert_run
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging

FIRST, LAST = date(2026, 9, 1), date(2026, 10, 10)
DAILY = "10.00"
pytestmark = pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)


@pytest.fixture
def series(billing_schema, api):
    """Ten euros a day for tenant-a from 2026-09-01 to 2026-10-10 and one undated record."""
    db = billing_schema
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        connection.execute(text("DELETE FROM azure_cost_ingestion_runs"))
        insert_run(connection, "run-a")
        for offset in range((LAST - FIRST).days + 1):
            day = FIRST + timedelta(days=offset)
            insert_cost(connection, f"day-{day}", day=day.isoformat(), cost=DAILY, service="Compute", project="Alpha",
                        tags={"project": "Alpha"})
        insert_cost(connection, "undated", day=None, cost="1.00")
    yield api
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        connection.execute(text("DELETE FROM azure_cost_ingestion_runs"))


def summary(api, start, end, **extra):
    query = f"start_date={start}&end_date={end}" + "".join(f"&{k}={v}" for k, v in extra.items())
    response = call(api, "GET", "/billing/summary?" + query, headers=headers())
    assert response.status_code == 200, response.text
    return response


def test_summary_stops_at_the_reference_day_and_keeps_the_requested_period(series):
    reference_date.configure(date(2026, 10, 5))
    body = summary(series, "2026-10-01", "2026-11-01").json()
    assert body["totals"] == [{"currency": "EUR", "cost": "50.00", "record_count": 5}]
    assert body["period"]["end_date"] == "2026-11-01"
    provenance = series.db.fetch_billing_summary("tenant-a", start_date=date(2026, 10, 1), end_date=date(2026, 11, 1),
                                                  include_provenance=True)["provenance"]
    assert provenance["last_usage_date"] == "2026-10-05" and provenance["observed_day_count"] == 5


def test_the_reference_day_is_included_and_the_next_one_is_not(series):
    reference_date.configure(date(2026, 9, 21))
    body = summary(series, "2026-09-21", "2026-09-23").json()
    assert body["totals"] == [{"currency": "EUR", "cost": DAILY, "record_count": 1}]


def test_a_period_wholly_after_the_reference_is_an_empty_period_without_a_trace_of_the_hidden_amounts(series):
    reference_date.configure(date(2026, 9, 21))
    response = summary(series, "2026-10-01", "2026-11-01")
    body = response.json()
    assert body["data_status"] == "partial" and body["totals"] == [] and body["groups"] == []
    assert body["excluded_undated_count"] == 1
    assert DAILY not in response.text and "2026-10-0" not in response.text.replace("2026-10-01", "")
    assert body["period"]["start_date"] == "2026-10-01"


def test_without_a_fixed_date_the_real_day_is_the_limit(series, monkeypatch):
    from datetime import datetime, timezone
    monkeypatch.setattr(reference_date, "_utc_now", lambda: datetime(2026, 9, 3, 12, tzinfo=timezone.utc))
    body = summary(series, "2026-09-01", "2026-10-01").json()
    assert body["totals"] == [{"currency": "EUR", "cost": "30.00", "record_count": 3}]


def test_the_default_period_is_the_month_of_the_reference_date_cut_at_it(series):
    reference_date.configure(date(2026, 10, 7))
    response = call(series, "GET", "/billing/summary", headers=headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["period"]["start_date"] == "2026-10-01" and body["period"]["end_date"] == "2026-11-01"
    assert body["totals"] == [{"currency": "EUR", "cost": "70.00", "record_count": 7}]


def test_tag_coverage_counts_only_visible_records(series):
    reference_date.configure(date(2026, 10, 5))
    response = call(series, "GET", "/billing/tag-coverage?start_date=2026-10-01&end_date=2026-11-01", headers=headers())
    assert response.status_code == 200, response.text
    assert [item["record_count"] for item in response.json()["currencies"]] == [5]


def test_the_budget_observes_only_visible_spend(series):
    reference_date.configure(date(2026, 10, 5))
    response = call(series, "POST", "/billing/budget/evaluate", headers=headers(), json={
        "amount": "100.00", "currency": "EUR", "start_date": "2026-10-01", "end_date": "2026-11-01"})
    assert response.status_code == 200, response.text
    assert response.json()["observed_spend"] == "50.00" and response.json()["record_count"] == 5


def test_the_anomaly_test_query_reads_only_visible_days_and_refuses_a_future_end(series):
    reference_date.configure(date(2026, 10, 5))
    body = {"start_date": "2026-10-01", "end_date": "2026-10-05", "currency": "EUR", "group_by": "service",
            "absolute_threshold": "30.00", "deviation_threshold_percent": None, "min_absolute_increase": "0.01"}
    accepted = call(series, "POST", "/billing/anomalies/evaluate", headers=headers(), json=body)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["alerts"][0]["current_cost"] == "40.00"
    refused = call(series, "POST", "/billing/anomalies/evaluate", headers=headers(), json={**body, "end_date": "2026-10-06"})
    assert refused.status_code == 422, refused.text


def test_the_daily_read_and_the_observed_range_stop_at_the_reference_day(series):
    reference_date.configure(date(2026, 10, 5))
    with series.db.engine.connect() as connection:
        first, last = series.db.observed_cost_day_range(connection, "tenant-a")
        observed, daily = series.db.read_daily_service_costs(connection, "tenant-a", start_date=FIRST, end_date=date(2026, 11, 1))
    assert (first, last) == (FIRST, date(2026, 10, 5))
    assert max(observed) == date(2026, 10, 5) and max(daily[("EUR", "Compute")]) == date(2026, 10, 5)


def test_the_ownership_answer_uses_the_reference_month_and_never_quotes_later_amounts(series):
    reference_date.configure(date(2026, 10, 5))
    answer = OwnershipQuestionService().answer(series.db, "tenant-a", OwnershipSelection(group_by="project"))
    evidence = answer["cost_evidence"]["selection"]
    assert (evidence["start_date"], evidence["end_date"]) == ("2026-10-01", "2026-11-01")
    assert "50.00" in answer["content"] and "60.00" not in answer["content"] and "100.00" not in answer["content"]
    assert "Fecha de referencia: 2026-10-05" in answer["content"] and answer["cost_evidence"]["reference_date"] == "2026-10-05"
    assert "Solo se cuentan los días hasta el 2026-10-05, inclusive." in answer["content"]


def test_a_question_about_a_month_after_the_reference_reports_no_data(series):
    reference_date.configure(date(2026, 9, 21))
    answer = OwnershipQuestionService().answer(series.db, "tenant-a", OwnershipSelection(
        group_by="project", start_date=date(2026, 10, 1), end_date=date(2026, 11, 1)))
    assert answer["cost_evidence"]["status"] == "no_data" and answer["cost_evidence"]["reason"] == "empty_period"
    assert DAILY not in answer["content"] and "posteriores" not in answer["content"]
    assert "Fecha de referencia: 2026-09-21" in answer["content"] and "Solo se cuentan" not in answer["content"]


def test_overlapping_sources_after_the_reference_do_not_refuse_the_request(series):
    with series.db.engine.begin() as connection:
        insert_run(connection, "run-b")
        insert_cost(connection, "overlap", run="run-b", day="2026-10-08", cost="5.00", service="Other")
    reference_date.configure(date(2026, 10, 5))
    assert summary(series, "2026-10-01", "2026-11-01").json()["totals"][0]["cost"] == "50.00"
    reference_date.configure(date(2026, 10, 9))
    refused = call(series, "GET", "/billing/summary?start_date=2026-10-01&end_date=2026-11-01", headers=headers())
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "ambiguous_cost_source"


@pytest.mark.parametrize("group,value", [("subscription", "sub-a"), ("account", "acct-a"), ("service", "Compute")])
def test_azure_cost_selection_keeps_filters_and_the_reference_limit(series, group, value):
    with series.db.engine.begin() as connection:
        connection.execute(text("UPDATE azure_cost_records SET billing_account_id = 'acct-a'"))
    reference_date.configure(date(2026, 10, 5))
    response = call(series, "POST", "/assistant/conversations/own/messages", headers=headers(), json={
        "content": "Coste de la selección", "cost_query": {
            "group_by": group, "value": value, "subscription_id": "sub-a",
        },
    })
    assert response.status_code == 201, response.text
    message = response.json()["assistant_message"]
    evidence = message["metadata"]["cost_evidence"]
    assert evidence["selection"]["start_date"] == "2026-10-01"
    assert evidence["selection"]["end_date"] == "2026-11-01"
    assert evidence["summary"]["totals"] == [{"currency": "EUR", "cost": "50.00", "record_count": 5}]
    assert evidence["provenance"]["last_usage_date"] == "2026-10-05"
    assert evidence["reference_date"] == "2026-10-05"
    assert "Solo se cuentan los días hasta el 2026-10-05, inclusive." in message["content"]
    history = call(series, "GET", "/assistant/conversations/own", headers=headers())
    assert history.status_code == 200
    assert history.json()["messages"][-1]["metadata"]["cost_evidence"] == evidence
