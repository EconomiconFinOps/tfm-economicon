"""JUP-114: authenticated anomaly episode API, status changes and tenant isolation."""
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from app.schemas.billing import AmbiguousCostSource
from app.services.anomaly_episodes import DetectionConflict
from anomaly_episode_support import D, episode_rows, episode_store, load_series
from billing_support import billing_schema
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers


DETECT = "/billing/anomalies/detect"
EPISODES = "/billing/anomalies/episodes"
SPIKE = ["400.00"] * 7 + ["550.00", "400.00"]
STORE_METHODS = ("run_anomaly_detection", "fetch_anomaly_episodes", "fetch_anomaly_episode",
                 "change_anomaly_episode_status")


def spy_store(api):
    for name in STORE_METHODS:
        api.spies[name] = MagicMock(name=name)
        setattr(api.db, name, api.spies[name])
    return api.spies


def detect(api, user="alice", tenant="tenant-a"):
    response = call(api, "POST", DETECT, headers=headers(user, tenant))
    assert response.status_code == 200, response.text
    return response.json()


def patch(api, identifier, body, user="alice", tenant="tenant-a"):
    return call(api, "PATCH", f"{EPISODES}/{identifier}", headers=headers(user, tenant), json=body)


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_detect_list_read_and_follow_an_episode(episode_store, api):
    load_series(episode_store, SPIKE)
    run = detect(api)
    assert run["status"] == "completed" and run["opened"] == 1
    assert run["last_complete_day"] == D.isoformat() and run["rules_version"] == "jup019-daily-v1"
    [item] = call(api, "GET", EPISODES, headers=headers()).json()["episodes"]
    assert item["kind"] == "cost_anomaly_candidate" and item["cause_status"] == "not_established"
    assert (item["currency"], item["service"], item["severity"], item["status"]) == ("EUR", "Compute", "P3", "new")
    assert (item["reference_daily_cost"], item["opening_observed_cost"], item["accumulated_impact"]) == ("400.00", "550.00", "150.00")
    assert item["start_date"] == item["last_seen_date"] == item["impact_through_date"] == D.isoformat()
    assert item["observation"] == "observed" and item["limitations"]
    assert item["rules"]["absolute_increase"] == "100.00" and item["previous_episode_id"] is None
    assert call(api, "GET", f"{EPISODES}/{item['id']}", headers=headers()).json() == item

    investigating = patch(api, item["id"], {"status": "investigating"})
    assert investigating.status_code == 200, investigating.text
    assert investigating.json()["status_changed_by"] == "alice"
    assert investigating.json()["first_reviewed_at"] is not None and investigating.json()["closed_at"] is None
    resolved = patch(api, item["id"], {"status": "resolved", "reason": "  Escalado revertido  "}, user="multi")
    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    assert (body["status"], body["status_changed_by"], body["closure_reason"]) == ("resolved", "multi", "Escalado revertido")
    assert body["first_reviewed_at"] == investigating.json()["first_reviewed_at"]
    assert (body["first_reviewed_by"], investigating.json()["first_reviewed_by"]) == ("alice", "alice")
    assert call(api, "GET", EPISODES, headers=headers()).json()["episodes"] == []
    assert [e["id"] for e in call(api, "GET", EPISODES + "?scope=all", headers=headers()).json()["episodes"]] == [item["id"]]
    assert patch(api, item["id"], {"status": "false_positive", "reason": "otra"}).status_code == 409
    assert detect(api)["status"] == "up_to_date"


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
@pytest.mark.parametrize("body", [
    {"status": "resolved"}, {"status": "resolved", "reason": "   "}, {"status": "false_positive", "reason": ""},
    {"status": "resolved", "reason": "a\u0007b"}, {"status": "resolved", "reason": "x" * 501},
    {"status": "resolved", "reason": "ok\x85x"}, {"status": "resolved", "reason": "\u202egnirts"},
    {"status": "resolved", "reason": "a\u2028b"}, {"status": "resolved", "reason": "\u200b"},
    {"status": "false_positive", "reason": "a\xadb"}, {"status": "resolved", "reason": "a\u2029b"},
    {"status": "investigating", "reason": "no se admite"}, {"status": "acknowledged"},
    {"status": "resolved", "reason": "ok", "actor": "mallory"}, {},
])
def test_invalid_status_requests_are_rejected_without_changes(episode_store, api, body):
    load_series(episode_store, SPIKE)
    detect(api)
    [before] = episode_rows(episode_store)
    response = patch(api, before["id"], body)
    assert response.status_code == 422, response.text
    assert episode_rows(episode_store) == [before]


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_new_cannot_be_requested_again(episode_store, api):
    load_series(episode_store, SPIKE)
    detect(api)
    [row] = episode_rows(episode_store)
    assert patch(api, row["id"], {"status": "investigating"}).status_code == 200
    response = patch(api, row["id"], {"status": "new"})
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "invalid_status_transition"}}


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_foreign_and_missing_episode_ids_are_indistinguishable(episode_store, api, caplog):
    load_series(episode_store, SPIKE, tenant="tenant-b", run="run-b-tenant")
    detect(api, user="bob", tenant="tenant-b")
    [foreign] = episode_rows(episode_store)
    missing = "anomaly-" + "0" * 64
    responses = [call(api, "GET", f"{EPISODES}/{identifier}", headers=headers()) for identifier in (foreign["id"], missing)]
    responses += [patch(api, identifier, {"status": "investigating"}) for identifier in (foreign["id"], missing)]
    assert {response.status_code for response in responses} == {404}
    assert len({response.text for response in responses}) == 1
    assert call(api, "GET", EPISODES + "?scope=all", headers=headers()).json()["episodes"] == []
    assert episode_rows(episode_store) == [foreign]
    assert foreign["id"] not in caplog.text and "9000" not in caplog.text


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_listing_is_ordered_and_never_mixes_currencies(episode_store, api):
    load_series(episode_store, ["400.00"] * 7 + ["9000.00", "400.00"], service="Compute")
    load_series(episode_store, ["400.00"] * 7 + ["560.00", "400.00"], service="Storage")
    load_series(episode_store, ["400.00"] * 7 + ["900.00", "400.00"], service="Network")
    load_series(episode_store, SPIKE, service="Compute", currency="USD")
    detect(api)
    result = call(api, "GET", EPISODES, headers=headers()).json()
    assert set(result) == {"contract_version", "scope", "episodes"}
    assert [(e["service"], e["currency"], e["severity"], e["accumulated_impact"]) for e in result["episodes"]] == [
        ("Compute", "EUR", "P1", "8600.00"), ("Network", "EUR", "P2", "500.00"),
        ("Storage", "EUR", "P3", "160.00"), ("Compute", "USD", "P3", "150.00"),
    ]


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_exact_twenty_percent_triggers_the_test_query_but_opens_no_episode(episode_store, api):
    load_series(episode_store, ["1000.00"] * 7 + ["1200.00", "1000.00"])
    query = call(api, "POST", "/billing/anomalies/evaluate", headers=headers(), json={
        "start_date": D.isoformat(), "end_date": (D + timedelta(days=1)).isoformat(), "currency": "EUR",
        "deviation_threshold_percent": "20.00", "min_absolute_increase": "100.00",
    })
    assert query.status_code == 200, query.text
    assert [alert["group_value"] for alert in query.json()["alerts"]] == ["Compute"]
    assert episode_rows(episode_store) == []
    run = detect(api)
    assert run["status"] == "completed" and run["opened"] == 0
    assert episode_rows(episode_store) == []


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("method,path", [
    ("POST", DETECT), ("GET", EPISODES), ("GET", EPISODES + "/anomaly-x"), ("PATCH", EPISODES + "/anomaly-x"),
])
@pytest.mark.parametrize("auth,tenant,expected", [(False, "tenant-a", 401), (True, "tenant-b", 403), (True, None, 400)])
def test_authentication_and_membership_precede_any_read(api, method, path, auth, tenant, expected):
    spies = spy_store(api)
    kwargs = {"json": {"status": "investigating"}} if method == "PATCH" else {}
    response = call(api, method, path, headers=headers(tenant=tenant) if auth else [], **kwargs)
    assert response.status_code == expected
    for name in STORE_METHODS:
        spies[name].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_listing_and_reading_never_run_a_detection(api):
    spies = spy_store(api)
    spies["fetch_anomaly_episodes"].return_value = []
    spies["fetch_anomaly_episode"].return_value = None
    assert call(api, "GET", EPISODES, headers=headers()).status_code == 200
    assert call(api, "GET", EPISODES + "/anomaly-x", headers=headers()).status_code == 404
    spies["run_anomaly_detection"].assert_not_called()
    spies["fetch_anomaly_episodes"].assert_called_once_with("tenant-a", scope="open")


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("error,code", [(AmbiguousCostSource(), "ambiguous_cost_source"), (DetectionConflict(), "detection_conflict")])
def test_detection_failures_return_conflict_codes(api, error, code):
    spies = spy_store(api)
    spies["run_anomaly_detection"].side_effect = error
    response = call(api, "POST", DETECT, headers=headers())
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": code}}
    assert spies["run_anomaly_detection"].call_args.args == ("tenant-a",)


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("query", ["?scope=closed", "?scope=", "?scope=ALL"])
def test_unknown_scope_is_rejected_before_reading(api, query):
    spies = spy_store(api)
    assert call(api, "GET", EPISODES + query, headers=headers()).status_code == 422
    spies["fetch_anomaly_episodes"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_detection_request_rejects_caller_rules(api):
    spies = spy_store(api)
    response = call(api, "POST", DETECT, headers=headers(), json={"absolute_increase": "1.00"})
    assert response.status_code == 422
    spies["run_anomaly_detection"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("auth,tenant,expected", [(False, "tenant-a", 401), (True, None, 400), (True, "tenant-b", 403)])
def test_detection_body_check_follows_identity_selector_and_membership(api, auth, tenant, expected):
    spies = spy_store(api)
    response = call(api, "POST", DETECT, headers=headers(tenant=tenant) if auth else [], json={"rules": 1})
    assert response.status_code == expected
    spies["run_anomaly_detection"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_status_change_concurrency_has_its_own_conflict_code(api):
    from app.services.anomaly_episodes import StatusChangeConflict

    spies = spy_store(api)
    spies["change_anomaly_episode_status"].side_effect = StatusChangeConflict()
    response = patch(api, "anomaly-x", {"status": "investigating"})
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "status_change_conflict"}}


@pytest.mark.parametrize("reason", ["Motivo válido", "Revertido: coste esperado (ticket 42)", "ñandú — ok"])
def test_visible_reasons_are_accepted(reason):
    from app.schemas.anomaly_episodes import EpisodeStatusChange

    assert EpisodeStatusChange(status="resolved", reason=reason).reason == reason
