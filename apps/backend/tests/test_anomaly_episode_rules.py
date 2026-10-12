"""JUP-114: daily business rule, episodes, impact and severity without a database."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.anomaly_episodes import (
    RULES, RULES_VERSION, Episode, detection_window, plan_detection, severity,
)


TODAY = date(2026, 10, 12)
D = date(2026, 9, 8)
EUR = ("EUR", "Compute")


def days(start, count):
    return [start + timedelta(days=offset) for offset in range(count)]


def series(start, values):
    return {start + timedelta(days=offset): Decimal(value) for offset, value in enumerate(values) if value is not None}


def run(daily, *, last_evaluated=None, episodes=(), observed=None, latest=None, today=TODAY, tenant="tenant-a"):
    observed = set(observed) if observed is not None else {day for values in daily.values() for day in values}
    latest = latest if latest is not None else max(observed)
    window = detection_window(today=today, last_evaluated=last_evaluated, latest_observed=latest,
                              earliest_observed=min(observed) if observed else None)
    return window, plan_detection(window, tenant_id=tenant, observed_days=observed, daily=daily,
                                  episodes=[episode.copy() for episode in episodes])


def one_day(previous, observed_value, group=EUR, *, after=1):
    """Seven reference days, the evaluated day and `after` extra days so it is complete."""
    start = D - timedelta(days=7)
    values = [previous] * 7 + [observed_value] + [previous] * after
    return {group: series(start, values)}


def only(plan):
    assert len(plan.opened) == 1, plan
    return plan.opened[0]


# Rule and boundaries -------------------------------------------------------

def test_both_conditions_exceeded_opens_an_episode():
    _, plan = run(one_day("400.00", "550.00"))
    item = only(plan)
    assert (item.start_date, item.last_seen_date, item.status, item.observation) == (D, D, "new", "observed")
    assert item.reference_daily_cost == "400.00"
    assert item.opening_observed_cost == "550.00"
    assert item.accumulated_impact == "150.00"
    assert item.severity == "P3"


@pytest.mark.parametrize("previous,current", [
    ("400.00", "500.00"),   # absolute increase exactly 100.00 (JUP-069-017)
    ("1000.00", "1200.00"),  # relative increase exactly 20 % (JUP-069-018)
    ("100.00", "190.00"),   # relative only
    ("5000.00", "5150.00"),  # absolute only
])
def test_strict_and_combined_conditions(previous, current):
    _, plan = run(one_day(previous, current))
    assert plan.opened == []


def test_just_above_both_boundaries_triggers():
    _, plan = run(one_day("400.00", "500.01"))
    assert only(plan).accumulated_impact == "100.01"
    _, plan = run(one_day("1000.00", "1200.01"))
    assert len(plan.opened) == 1


def test_question_bank_case_016_triggers():
    _, plan = run(one_day("400.00", "550.00"))
    item = only(plan)
    assert Decimal(item.opening_observed_cost) - Decimal(item.reference_daily_cost) == Decimal("150.00")


@pytest.mark.parametrize("previous", ["0.00", "-5.00", None])
def test_zero_negative_or_absent_reference_never_opens(previous):
    start = D - timedelta(days=7)
    daily = {EUR: series(start, [previous] * 7 + ["150.00", "0.00"]),
             ("EUR", "Other"): series(start, ["1.00"] * 9)}
    _, plan = run(daily)
    assert plan.opened == []


def test_mean_comparison_is_exact_without_rounding_the_reference():
    # Mean 100.0014285..., so 200.01 exceeds it by slightly less than 100.01 but more than 100.
    start = D - timedelta(days=7)
    daily = {EUR: series(start, ["100.00"] * 6 + ["100.01", "200.01", "100.00"])}
    _, plan = run(daily)
    item = only(plan)
    assert item.reference_daily_cost == "100.00"
    assert item.accumulated_impact == "100.01"
    # 200.00 is above the rounded mean by 100.00 but below the exact mean + 100.
    daily = {EUR: series(start, ["100.00"] * 6 + ["100.01", "200.00", "100.00"])}
    assert run(daily)[1].opened == []


def test_large_amounts_keep_cents():
    big = "9007199254740993.01"
    start = D - timedelta(days=7)
    daily = {EUR: series(start, [big] * 7 + ["18014398509481986.05", big])}
    item = only(run(daily)[1])
    assert item.reference_daily_cost == big
    assert item.accumulated_impact == "9007199254740993.04"


@pytest.mark.parametrize("currency", ["GBP", "JPY", "eur"])
def test_unsupported_currency_is_reported_not_evaluated(currency):
    _, plan = run(one_day("400.00", "9000.00", group=(currency, "Compute")))
    assert plan.opened == []
    assert plan.unsupported_currencies == [currency]


def test_usd_uses_nominal_thresholds_and_currencies_are_never_mixed():
    start = D - timedelta(days=7)
    daily = {("USD", "Compute"): series(start, ["400.00"] * 7 + ["550.00", "400.00"]),
             ("EUR", "Compute"): series(start, ["400.00"] * 7 + ["450.00", "400.00"])}
    _, plan = run(daily)
    item = only(plan)
    assert (item.currency, item.accumulated_impact) == ("USD", "150.00")


def test_null_service_and_case_are_separate_groups():
    start = D - timedelta(days=7)
    daily = {("EUR", None): series(start, ["400.00"] * 7 + ["550.00", "400.00"]),
             ("EUR", "compute"): series(start, ["400.00"] * 7 + ["550.00", "400.00"]),
             ("EUR", "Compute"): series(start, ["400.00"] * 9)}
    _, plan = run(daily)
    assert sorted((item.service or "") for item in plan.opened) == ["", "compute"]
    assert len({item.id for item in plan.opened}) == 2


def test_missing_group_on_an_observed_day_counts_as_zero():
    start = D - timedelta(days=7)
    daily = {EUR: series(start, ["700.00"] + [None] * 6 + ["250.00", None]),
             ("EUR", "Other"): series(start, ["1.00"] * 9)}
    # Mean 100.00 because the six days without Compute records count as 0.00.
    item = only(run(daily)[1])
    assert (item.reference_daily_cost, item.accumulated_impact) == ("100.00", "150.00")


# Windows, coverage and idempotence -----------------------------------------

def test_latest_day_is_not_complete_and_today_is_never_evaluated():
    window = detection_window(today=TODAY, last_evaluated=None, latest_observed=date(2026, 9, 14),
                              earliest_observed=date(2026, 9, 1))
    assert window.last_complete_day == date(2026, 9, 13)
    assert window.days == days(date(2026, 9, 1), 13)
    window = detection_window(today=TODAY, last_evaluated=None, latest_observed=date(2026, 10, 20),
                              earliest_observed=date(2026, 10, 1))
    assert window.last_complete_day == date(2026, 10, 11)


def test_first_run_covers_the_whole_history_without_a_day_limit():
    window = detection_window(today=TODAY, last_evaluated=None, latest_observed=date(2026, 9, 21),
                              earliest_observed=date(2026, 6, 1))
    assert window.days[0] == date(2026, 6, 1) and window.days[-1] == date(2026, 9, 20)
    assert len(window.days) == 112
    assert window.read_start == date(2026, 5, 25)


@pytest.mark.parametrize("earliest", [date(2026, 9, 14), date(2026, 9, 20)])
def test_history_without_a_complete_day_is_insufficient(earliest):
    window = detection_window(today=TODAY, last_evaluated=None, latest_observed=date(2026, 9, 14),
                              earliest_observed=earliest)
    assert window.status == "insufficient_data" and window.days == []


def test_without_data_detection_is_insufficient():
    window = detection_window(today=TODAY, last_evaluated=None, latest_observed=None)
    assert window.status == "insufficient_data" and window.days == []


@pytest.mark.parametrize("last_evaluated", [date(2026, 9, 13), date(2026, 9, 20)])
def test_nothing_new_is_up_to_date(last_evaluated):
    window = detection_window(today=TODAY, last_evaluated=last_evaluated, latest_observed=date(2026, 9, 14))
    assert window.status == "up_to_date" and window.days == []


def test_every_missed_day_is_evaluated():
    window = detection_window(today=TODAY, last_evaluated=date(2026, 9, 1), latest_observed=date(2026, 9, 21),
                              earliest_observed=date(2026, 8, 1))
    assert window.days == days(date(2026, 9, 2), 19)
    assert window.read_start == date(2026, 8, 26)
    assert not hasattr(window, "unevaluated")


def test_short_pending_range():
    window = detection_window(today=TODAY, last_evaluated=date(2026, 9, 11), latest_observed=date(2026, 9, 14),
                              earliest_observed=date(2026, 9, 1))
    assert window.days == [date(2026, 9, 12), date(2026, 9, 13)]


def test_gap_skips_the_missing_day_and_every_day_that_needs_it():
    start = date(2026, 8, 29)
    values = ["400.00"] * 15
    values[7] = None  # 2026-09-05 has no tenant records
    values[10] = "9000.00"  # spike on 2026-09-08 would trigger if it were evaluated
    daily = {EUR: series(start, values)}
    window, plan = run(daily, latest=date(2026, 9, 12))
    assert window.days == days(start, 14)
    assert dict(plan.skipped_days) == {**{day: "reference_incomplete" for day in days(start, 7)},
                                       date(2026, 9, 5): "not_observed",
                                       **{day: "reference_incomplete" for day in days(date(2026, 9, 6), 6)}}
    assert plan.opened == [] and plan.updated == []
    assert plan.status == "insufficient_data"


def test_not_enough_history_stores_nothing():
    start = D
    daily = {EUR: series(start, ["400.00", "9000.00", "400.00"])}
    _, plan = run(daily)
    assert plan.status == "insufficient_data"
    assert plan.opened == plan.updated == []
    assert plan.new_last_evaluated is None


def test_successful_run_moves_the_watermark_to_the_last_complete_day():
    window, plan = run(one_day("400.00", "400.00", after=3))
    assert plan.status == "completed"
    assert plan.new_last_evaluated == window.last_complete_day


def test_rerun_over_the_same_days_with_stored_episodes_is_idempotent():
    daily = one_day("400.00", "550.00")
    window, first = run(daily)
    second = plan_detection(window, tenant_id="tenant-a", observed_days=set(daily[EUR]), daily=daily,
                            episodes=[item.copy() for item in first.opened])
    # A replay over already processed days must neither open nor count anything twice.
    assert second.opened == [] and second.updated == []


# Episodes ------------------------------------------------------------------

def sustained(reference="1000.00", level="2400.00", count=14, *, extra=None):
    start = D - timedelta(days=7)
    values = [reference] * 7 + [level] * count + ([] if extra is None else extra) + [reference]
    return {EUR: series(start, values)}


def run_in_batches(daily, *, batches, episodes=()):
    """Press the button once per batch of evaluated days, carrying stored episodes and watermark."""
    stored = {item.id: item for item in episodes}
    last = None
    plans = []
    for latest in batches:
        window, plan = run(daily, last_evaluated=last, episodes=list(stored.values()), latest=latest)
        for item in plan.opened + plan.updated:
            stored[item.id] = item
        last = plan.new_last_evaluated or last
        plans.append(plan)
    return stored, plans


def test_anchored_reference_keeps_a_sustained_rise_visible():
    daily = sustained()
    batches = [D + timedelta(days=offset) for offset in (2, 9, 15)]
    stored, plans = run_in_batches(daily, batches=batches)
    [item] = stored.values()
    assert item.reference_daily_cost == "1000.00"
    assert item.last_seen_date == D + timedelta(days=13)
    assert item.observation == "observed"
    # The fifteenth evaluated day is back at the reference: counted, adds 0.00, within tolerance.
    assert item.impact_day_count == 15
    assert item.accumulated_impact == "19600.00"
    assert item.severity == "P1"


def test_without_anchoring_the_mean_would_have_absorbed_the_rise():
    # Control: a fresh plan from day 8 of the rise, with no stored episode, does not trigger.
    daily = sustained()
    window = detection_window(today=TODAY, last_evaluated=D + timedelta(days=7), latest_observed=D + timedelta(days=9))
    plan = plan_detection(window, tenant_id="tenant-a", observed_days=set(daily[EUR]), daily=daily, episodes=[])
    assert plan.opened == []


def test_intermittent_spikes_within_tolerance_continue_the_episode():
    start = D - timedelta(days=7)
    # Triggers on day 0 (D) and day 3; days 1 and 2 are normal.
    daily = {EUR: series(start, ["400.00"] * 7 + ["550.00", "400.00", "400.00", "550.00", "400.00"])}
    stored, _ = run_in_batches(daily, batches=[D + timedelta(days=4)])
    [item] = stored.values()
    assert item.last_seen_date == D + timedelta(days=3)
    assert item.observation == "observed"
    assert item.accumulated_impact == "300.00"


def test_tolerance_exceeded_marks_no_longer_observed_and_freezes_impact():
    start = D - timedelta(days=7)
    daily = {EUR: series(start, ["400.00"] * 7 + ["550.00", "450.00", "450.00", "450.00", "450.00", "400.00"])}
    stored, plans = run_in_batches(daily, batches=[D + timedelta(days=5)])
    [item] = stored.values()
    assert item.observation == "no_longer_observed"
    assert item.no_longer_observed_on == D + timedelta(days=4)
    assert item.status == "new"
    # Days 1 to 3 are within tolerance and add their positive excess; day 4 ends it and adds nothing.
    assert item.accumulated_impact == "300.00"
    assert item.impact_through_date == D + timedelta(days=3)
    assert plans[0].no_longer_observed == 1


def test_return_after_end_opens_a_linked_new_episode():
    start = D - timedelta(days=7)
    values = ["400.00"] * 7 + ["550.00"] + ["400.00"] * 4 + ["400.00"] * 3 + ["560.00", "400.00"]
    daily = {EUR: series(start, values)}
    stored, _ = run_in_batches(daily, batches=[D + timedelta(days=5), D + timedelta(days=9)])
    first, second = sorted(stored.values(), key=lambda item: item.start_date)
    assert first.observation == "no_longer_observed"
    assert second.start_date == D + timedelta(days=8)
    assert second.previous_episode_id == first.id
    assert second.observation == "observed" and second.status == "new"


@pytest.mark.parametrize("status,observation", [
    ("resolved", "observed"), ("false_positive", "observed"), ("investigating", "no_longer_observed"),
])
def test_closed_or_ended_episode_is_never_reopened(status, observation):
    daily = sustained(count=3)
    stored, _ = run_in_batches(daily, batches=[D + timedelta(days=1)])
    [item] = stored.values()
    item.status, item.observation = status, observation
    later, plans = run_in_batches(daily, batches=[D + timedelta(days=3)], episodes=[item])
    assert later[item.id].status == status and later[item.id].observation == observation
    assert later[item.id].last_seen_date == D


def test_closed_while_high_falls_back_to_the_mean():
    daily = sustained(count=10)
    stored, _ = run_in_batches(daily, batches=[D + timedelta(days=1)])
    [item] = stored.values()
    item.status = "resolved"
    # From day 8 the mean has reached 2400, so nothing triggers and no episode reopens.
    window = detection_window(today=TODAY, last_evaluated=D + timedelta(days=7), latest_observed=D + timedelta(days=10))
    plan = plan_detection(window, tenant_id="tenant-a", observed_days=set(daily[EUR]), daily=daily, episodes=[item])
    assert plan.opened == [] and plan.updated == []


def test_days_below_reference_add_zero_and_never_reduce_impact():
    start = D - timedelta(days=7)
    daily = {EUR: series(start, ["400.00"] * 7 + ["550.00", "100.00", "550.00", "400.00"])}
    stored, _ = run_in_batches(daily, batches=[D + timedelta(days=3)])
    [item] = stored.values()
    assert item.accumulated_impact == "300.00"
    assert item.impact_day_count == 3


def test_episode_ids_are_deterministic_scoped_and_carry_rules():
    first = only(run(one_day("400.00", "550.00"))[1])
    again = only(run(one_day("400.00", "550.00"))[1])
    other = only(run(one_day("400.00", "550.00"), tenant="tenant-b")[1])
    assert first.id == again.id != other.id
    assert first.id.startswith("anomaly-")
    assert first.rules_version == RULES_VERSION
    assert first.rules == RULES
    assert first.rules["relative_increase_percent"] == "20" and first.rules["absolute_increase"] == "100.00"
    assert (first.rules["reference_days"], first.rules["tolerance_days"]) == (7, 3)


def test_skipped_days_do_not_extend_end_or_add_impact():
    start = D - timedelta(days=7)
    values = ["400.00"] * 7 + ["550.00", "400.00"]
    daily = {EUR: series(start, values)}
    stored, _ = run_in_batches(daily, batches=[D + timedelta(days=1)])
    [item] = stored.values()
    # Ten days without any tenant data, then data again: the gap days are skipped, not counted.
    later_start = D + timedelta(days=11)
    daily[EUR].update(series(later_start, ["400.00"] * 9))
    observed = set(daily[EUR])
    window = detection_window(today=TODAY, last_evaluated=D, latest_observed=later_start + timedelta(days=8))
    plan = plan_detection(window, tenant_id="tenant-a", observed_days=observed, daily=daily, episodes=[item.copy()])
    updated = {episode.id: episode for episode in plan.updated}
    assert updated[item.id].observation == "no_longer_observed"
    assert updated[item.id].accumulated_impact == "150.00"


# Severity ------------------------------------------------------------------

@pytest.mark.parametrize("impact,expected", [
    ("0.01", "P3"), ("499.99", "P3"), ("500.00", "P2"), ("2000.00", "P2"), ("2000.01", "P1"),
])
def test_severity_tiers_and_boundaries(impact, expected):
    assert severity(Decimal(impact) * 7) == expected


def test_severity_follows_accumulated_impact_not_the_opening_day():
    start = D - timedelta(days=7)
    daily = {EUR: series(start, ["400.00"] * 7 + ["550.00", "650.00", "750.00", "400.00"])}
    stored, _ = run_in_batches(daily, batches=[D + timedelta(days=3)])
    [item] = stored.values()
    assert item.accumulated_impact == "750.00"
    assert item.severity == "P2"


def test_severity_uses_the_exact_impact_before_display_rounding():
    # 499.996 is shown as 500.00 but stays below the P2 boundary of 500.00.
    item = only(run(one_day("400.00", "899.996"))[1])
    assert item.accumulated_impact == "500.00"
    assert item.severity == "P3"



DEMO_WEEKS = {
    "Compute": (["140"] * 5 + ["150"] * 2, ["140"] + ["377"] * 4 + ["376"] * 2, ["377"] * 7),
    "Analytics": (["314"] * 5 + ["315"] * 2, ["303", "303", "480", "303", "303", "304", "304"], ["305"] * 7),
    "Storage": (["114"] * 6 + ["116"], ["117"] * 6 + ["118"], ["117"] * 7),
    "Database": (["214"] * 5 + ["215"] * 2, ["171"] * 4 + ["172"] * 3, ["171", "300", "300", "300", "300", "300", "171"]),
    "Tools": (["1"] * 4 + ["2"] * 3, ["5"] * 2 + ["6"] * 5, ["6"] * 7),
    "Backup": (["0"] * 7, ["0", "0", "300", "0", "0", "0", "0"], ["0"] * 7),
    "Networking": ([None] * 7, [None] * 6 + ["600"], ["85"] * 7),
}


def demo_daily():
    start = date(2026, 9, 1)
    return {("EUR", service): series(start, sum(weeks, [])) for service, weeks in DEMO_WEEKS.items()}


def snapshot(stored):
    return sorted((e.service, e.start_date, e.last_seen_date, e.observation, e.no_longer_observed_on,
                   e.reference_week_cost, e.impact_numerator, e.impact_day_count, e.impact_through_date,
                   e.previous_episode_id) for e in stored.values())


def test_one_press_equals_one_press_per_day():
    daily = demo_daily()
    observed = {day for values in daily.values() for day in values}
    one, _ = run_in_batches(daily, batches=[date(2026, 9, 21)])
    daily_presses, _ = run_in_batches(daily, batches=[date(2026, 9, 1) + timedelta(days=n) for n in range(1, 21)])
    assert snapshot(one) == snapshot(daily_presses)
    assert {(e.service, e.severity, e.accumulated_impact) for e in one.values()} == {
        ("Compute", "P1", "2807.71"), ("Database", "P2", "642.86"), ("Analytics", "P3", "168.86")}
    assert min(observed) == date(2026, 9, 1)
