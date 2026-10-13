"""JUP-119: stored episodes obey the reference date as it is when they are asked for."""
from datetime import date, timedelta

import pytest

from app.services import reference_date
from anomaly_episode_support import D, episode_rows, episode_store, load_series
from billing_support import billing_schema
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers

DETECT = "/billing/anomalies/detect"
EPISODES = "/billing/anomalies/episodes"
SPIKE_THEN_CALM = ["400.00"] * 7 + ["550.00"] + ["400.00"] * 14
END = date(2026, 10, 20)
pytestmark = pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)


def detect(api):
    response = call(api, "POST", DETECT, headers=headers())
    assert response.status_code == 200, response.text
    return response.json()


def listing(api, scope="all"):
    response = call(api, "GET", f"{EPISODES}?scope={scope}", headers=headers())
    assert response.status_code == 200, response.text
    return response.json()


def test_moving_the_date_back_hides_the_episode_and_advancing_shows_it_again(episode_store, api):
    load_series(episode_store, SPIKE_THEN_CALM)
    reference_date.configure(END)
    assert detect(api)["opened"] == 1
    [seen] = listing(api)["episodes"]
    assert seen["start_date"] == D.isoformat()

    reference_date.configure(D)
    assert listing(api)["episodes"] == []
    hidden = call(api, "GET", f"{EPISODES}/{seen['id']}", headers=headers())
    unknown = call(api, "GET", f"{EPISODES}/anomaly-unknown", headers=headers())
    assert hidden.status_code == unknown.status_code == 404 and hidden.json() == unknown.json()
    changed = call(api, "PATCH", f"{EPISODES}/{seen['id']}", headers=headers(), json={"status": "investigating"})
    assert changed.status_code == 404 and changed.json() == unknown.json()
    assert episode_rows(episode_store)[0]["status"] == "new"

    reference_date.configure(END)
    assert listing(api)["episodes"] == [seen]


def test_an_episode_that_ended_is_hidden_until_the_day_it_stopped_being_observed_is_complete(episode_store, api):
    load_series(episode_store, SPIKE_THEN_CALM)
    reference_date.configure(END)
    detect(api)
    [seen] = listing(api)["episodes"]
    stopped = date.fromisoformat(seen["no_longer_observed_on"])
    assert seen["observation"] == "no_longer_observed" and stopped > date.fromisoformat(seen["impact_through_date"])
    reference_date.configure(date.fromisoformat(seen["impact_through_date"]))
    assert listing(api)["episodes"] == []
    reference_date.configure(stopped)
    assert listing(api)["episodes"] == []
    assert call(api, "GET", f"{EPISODES}/{seen['id']}", headers=headers()).status_code == 404
    reference_date.configure(stopped + timedelta(days=1))
    assert [item["id"] for item in listing(api)["episodes"]] == [seen["id"]]


def test_the_shown_last_evaluation_never_goes_beyond_the_visible_days(episode_store, api):
    load_series(episode_store, SPIKE_THEN_CALM)
    reference_date.configure(END)
    detect(api)
    assert listing(api)["last_evaluated_date"] > D.isoformat()
    reference_date.configure(D)
    assert listing(api)["last_evaluated_date"] == (D - timedelta(days=1)).isoformat()


def test_detecting_again_after_advancing_the_date_does_not_duplicate_the_episode(episode_store, api):
    load_series(episode_store, SPIKE_THEN_CALM)
    reference_date.configure(D + timedelta(days=1))
    first = detect(api)
    assert first["opened"] == 1 and first["last_complete_day"] == D.isoformat()
    [opened] = listing(api)["episodes"]
    reference_date.configure(END)
    second = detect(api)
    assert second["opened"] == 0
    episodes = listing(api)["episodes"]
    assert [item["id"] for item in episodes] == [opened["id"]]
    assert len(episode_rows(episode_store)) == 1
