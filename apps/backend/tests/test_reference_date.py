"""JUP-119: one reference date decides which day is "today" for costs, detection and the assistant."""
import re
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.core.config import Settings, get_settings
from app.core.runtime_secrets import StartupError
from app.services import reference_date

APP = Path(__file__).resolve().parents[1] / "app"
INVALID = ["2026-09-21T00:00:00Z", " 2026-09-21", "2026-09-21 ", "2026-02-30", "26-09-21", "2026-9-21", "21/09/2026", "tomorrow"]


class Clock:
    def __init__(self, moment):
        self.moment = moment

    def __call__(self):
        return self.moment


@pytest.fixture
def clock(monkeypatch):
    fake = Clock(datetime(2026, 10, 13, 23, 59, 59, tzinfo=timezone.utc))
    monkeypatch.setattr(reference_date, "_utc_now", fake)
    return fake


def test_default_follows_the_utc_clock_without_restarting(clock):
    assert reference_date.today() == date(2026, 10, 13)
    assert reference_date.simulated() is False
    clock.moment = datetime(2026, 10, 14, 0, 0, 0, tzinfo=timezone.utc)
    assert reference_date.today() == date(2026, 10, 14)


def test_a_fixed_date_ignores_the_clock_and_is_flagged_simulated(clock):
    reference_date.configure(date(2026, 9, 21))
    assert reference_date.today() == date(2026, 9, 21)
    assert reference_date.simulated() is True
    clock.moment = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert reference_date.today() == date(2026, 9, 21)


@pytest.mark.parametrize("end, expected", [
    (date(2026, 11, 1), date(2026, 9, 22)),
    (date(2026, 9, 22), date(2026, 9, 22)),
    (date(2026, 9, 10), date(2026, 9, 10)),
])
def test_visible_end_is_the_day_after_the_reference_date_at_most(end, expected):
    reference_date.configure(date(2026, 9, 21))
    assert reference_date.visible_end(end) == expected


def test_the_setting_is_empty_by_default_and_a_valid_date_is_accepted(monkeypatch):
    assert Settings(_env_file=None).cost_reference_date is None
    monkeypatch.setenv("COST_REFERENCE_DATE", "")
    assert Settings(_env_file=None).cost_reference_date is None
    monkeypatch.setenv("COST_REFERENCE_DATE", "2026-09-21")
    assert Settings(_env_file=None).cost_reference_date == date(2026, 9, 21)


@pytest.mark.parametrize("value", INVALID)
def test_an_invalid_setting_stops_startup_naming_the_setting_and_never_its_value(monkeypatch, value):
    monkeypatch.setenv("COST_REFERENCE_DATE", value)
    with pytest.raises(StartupError) as raised:
        get_settings()
    message = str(raised.value)
    assert "cost_reference_date" in message
    assert value.strip() not in message or value.strip() == ""
    assert "db-fixture-pass" not in message


def test_no_code_that_picks_the_visible_day_reads_the_clock():
    watched = [
        "api/routes/billing.py", "services/ownership_questions.py", "schemas/anomalies.py",
        "services/anomaly_episodes.py", "db/database.py", "services/anomalies.py", "services/budget.py",
    ]
    pattern = re.compile(r"\.now\([^)]*\)\.date\(\)|(?<!\w)date\.today\(|utcnow\(")
    offenders = {name: [n for n, line in enumerate((APP / name).read_text("utf-8").splitlines(), 1) if pattern.search(line)]
                 for name in watched}
    assert {name: lines for name, lines in offenders.items() if lines} == {}


def test_only_the_reference_service_reads_the_clock_for_the_day():
    pattern = re.compile(r"\.now\([^)]*\)\.date\(\)|(?<!\w)date\.today\(|utcnow\(")
    found = sorted(path.relative_to(APP).as_posix() for path in APP.rglob("*.py") if pattern.search(path.read_text("utf-8")))
    assert found == []
