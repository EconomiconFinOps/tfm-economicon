"""JUP-119: the frontend reads the reference date from the backend instead of its own clock."""
from datetime import date, datetime, timezone

import pytest

from app.services import reference_date
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers

PATH = "/billing/reference-date"
pytestmark = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)


def test_a_fixed_date_is_reported_as_simulated(api):
    reference_date.configure(date(2026, 10, 15))
    response = call(api, "GET", PATH, headers=headers())
    assert response.status_code == 200, response.text
    assert response.json() == {"reference_date": "2026-10-15", "simulated": True}


def test_the_real_day_is_reported_as_not_simulated(api, monkeypatch):
    monkeypatch.setattr(reference_date, "_utc_now", lambda: datetime(2026, 10, 13, 22, tzinfo=timezone.utc))
    response = call(api, "GET", PATH, headers=headers())
    assert response.json() == {"reference_date": "2026-10-13", "simulated": False}


def test_every_authenticated_user_gets_the_same_answer_and_no_other_setting(api):
    reference_date.configure(date(2026, 10, 15))
    first = call(api, "GET", PATH, headers=headers("alice", "tenant-a"))
    second = call(api, "GET", PATH, headers=headers("bob", "tenant-b"))
    without_tenant = call(api, "GET", PATH, headers=headers("alice", None))
    assert first.json() == second.json() == without_tenant.json()
    assert set(first.json()) == {"reference_date", "simulated"}


@pytest.mark.parametrize("authorization", [[], [("Authorization", "Bearer not-a-token")], [("Authorization", "Basic abc")]])
def test_it_needs_a_session_and_returns_no_date_without_one(api, authorization):
    reference_date.configure(date(2026, 10, 15))
    response = call(api, "GET", PATH, headers=authorization)
    assert response.status_code == 401
    assert "2026-10-15" not in response.text
