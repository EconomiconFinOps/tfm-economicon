"""JUP-114: daily reads and transactional detection runs on real CockroachDB."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
import threading

import pytest
from sqlalchemy import text

from app.schemas.billing import AmbiguousCostSource
from app.services.anomaly_episodes import DetectionConflict, EpisodeConflict, EpisodeNotFound
from anomaly_episode_support import D, episode_rows, episode_store, load_series
from billing_support import billing_schema, insert_cost, insert_run
from tenant_isolation_support import tenant_cockroach_database


TODAY = date(2026, 10, 12)
SPIKE = ["400.00"] * 7 + ["550.00", "400.00"]


def test_daily_read_keeps_only_completed_tenant_records_per_service_currency_and_day(episode_store):
    db = episode_store
    with db.engine.begin() as connection:
        insert_run(connection, "run-a")
        insert_run(connection, "foreign", tenant="tenant-b")
        insert_run(connection, "running", status="running")
        insert_cost(connection, "a1", day="2026-09-01", cost="10.004", service="Compute")
        insert_cost(connection, "a2", day="2026-09-01", cost="0.002", service="Compute")
        insert_cost(connection, "a3", day="2026-09-01", cost="5.00", service="compute")
        insert_cost(connection, "a4", day="2026-09-01", cost="7.00", service=" ")
        insert_cost(connection, "a5", day="2026-09-02", cost="-1.00", service="Compute", currency="USD")
        insert_cost(connection, "undated", day=None, service="Compute")
        insert_cost(connection, "outside", day="2026-09-03", service="Compute")
        insert_cost(connection, "foreign", run="foreign", tenant="tenant-b", day="2026-09-01", service="Compute")
        insert_cost(connection, "wrong-tenant", tenant="tenant-b", day="2026-09-01", service="Compute")
        insert_cost(connection, "running", run="running", day="2026-09-01", service="Compute")
    with db.engine.connect() as connection:
        observed, daily = db.read_daily_service_costs(connection, "tenant-a", start_date=date(2026, 9, 1),
                                                      end_date=date(2026, 9, 3))
        latest = db.latest_observed_cost_day(connection, "tenant-a")
    assert observed == {date(2026, 9, 1), date(2026, 9, 2)}
    assert daily == {
        ("EUR", "Compute"): {date(2026, 9, 1): Decimal("10.006")},
        ("EUR", "compute"): {date(2026, 9, 1): Decimal("5.00")},
        ("EUR", None): {date(2026, 9, 1): Decimal("7.00")},
        ("USD", "Compute"): {date(2026, 9, 2): Decimal("-1.00")},
    }
    assert latest == date(2026, 9, 3)


def test_daily_read_rejects_overlapping_sources_inside_the_range_only(episode_store):
    db = episode_store
    with db.engine.begin() as connection:
        insert_run(connection, "run-a")
        insert_run(connection, "run-b")
        insert_cost(connection, "a", day="2026-09-01", service="Compute")
        insert_cost(connection, "b", run="run-b", day="2026-09-01", service="Compute")
    with db.engine.connect() as connection:
        with pytest.raises(AmbiguousCostSource):
            db.read_daily_service_costs(connection, "tenant-a", start_date=date(2026, 9, 1), end_date=date(2026, 9, 2))
        observed, _ = db.read_daily_service_costs(connection, "tenant-a", start_date=date(2026, 9, 2),
                                                  end_date=date(2026, 9, 3))
    assert observed == set()


def test_run_opens_stores_and_repeats_as_up_to_date(episode_store):
    db = episode_store
    load_series(db, SPIKE)
    first = db.run_anomaly_detection("tenant-a", today=TODAY)
    assert first["status"] == "completed"
    assert first["opened"] == 1 and first["last_complete_day"] == D.isoformat()
    assert first["evaluated_days"] == [D.isoformat()]
    [row] = episode_rows(db)
    assert (row["tenant_id"], row["currency"], row["service"], row["service_key"]) == ("tenant-a", "EUR", "Compute", '"Compute"')
    assert (row["start_date"], row["last_seen_date"], row["status"], row["observation"]) == (D, D, "new", "observed")
    assert (row["reference_week_cost"], row["impact_numerator"], row["severity"]) == (Decimal("2800.00"), Decimal("1050.00"), "P3")
    assert row["rules_version"] == "jup019-daily-v1" and row["rules"]["tolerance_days"] == 3
    second = db.run_anomaly_detection("tenant-a", today=TODAY)
    assert second["status"] == "up_to_date" and second["opened"] == 0
    assert episode_rows(db) == [row]


def test_run_continues_on_later_presses_and_stores_impact(episode_store):
    db = episode_store
    load_series(db, ["400.00"] * 7 + ["550.00", "650.00", "750.00", "400.00"])
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records WHERE usage_date > :day"), {"day": D + timedelta(days=1)})
    db.run_anomaly_detection("tenant-a", today=TODAY)
    load_series(db, [None, None, "750.00", "400.00"], start=D, prefix="later")
    result = db.run_anomaly_detection("tenant-a", today=TODAY)
    assert result["continued"] == 1 and result["opened"] == 0
    [row] = episode_rows(db)
    assert row["impact_numerator"] == Decimal("5250.00") and row["impact_day_count"] == 3
    assert row["severity"] == "P2" and row["last_seen_date"] == D + timedelta(days=2)


def test_runs_are_tenant_scoped(episode_store):
    db = episode_store
    load_series(db, SPIKE)
    load_series(db, ["400.00"] * 7 + ["9000.00", "400.00"], tenant="tenant-b", run="run-b-tenant")
    db.run_anomaly_detection("tenant-a", today=TODAY)
    assert {row["tenant_id"] for row in episode_rows(db)} == {"tenant-a"}
    db.run_anomaly_detection("tenant-b", today=TODAY)
    a, b = episode_rows(db, "tenant-a"), episode_rows(db, "tenant-b")
    assert len(a) == len(b) == 1 and a[0]["id"] != b[0]["id"]
    assert b[0]["impact_numerator"] == Decimal("60200.00")
    assert [item["id"] for item in db.fetch_anomaly_episodes("tenant-a", scope="all")] == [a[0]["id"]]
    assert db.fetch_anomaly_episode("tenant-a", b[0]["id"]) is None


def test_ambiguous_source_stores_nothing(episode_store):
    db = episode_store
    load_series(db, SPIKE)
    load_series(db, [None] * 7 + ["1.00"], run="run-dup", prefix="dup")
    with pytest.raises(AmbiguousCostSource):
        db.run_anomaly_detection("tenant-a", today=TODAY)
    assert episode_rows(db) == []
    with db.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM anomaly_detection_state")).scalar_one() == 0


def test_insufficient_data_stores_nothing(episode_store):
    db = episode_store
    load_series(db, ["400.00", "9000.00", "400.00"], start=D)
    result = db.run_anomaly_detection("tenant-a", today=TODAY)
    assert result["status"] == "insufficient_data"
    assert episode_rows(db) == []
    with db.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM anomaly_detection_state")).scalar_one() == 0


def test_concurrent_runs_store_a_single_run(episode_store):
    db = episode_store
    load_series(db, SPIKE)
    barrier = threading.Barrier(2)
    original = db.read_daily_service_costs

    def slow_read(*args, **kwargs):
        result = original(*args, **kwargs)
        barrier.wait(timeout=20)
        return result

    db.read_daily_service_costs = slow_read
    try:
        def press():
            try:
                return db.run_anomaly_detection("tenant-a", today=TODAY)["status"]
            except DetectionConflict:
                return "conflict"

        with ThreadPoolExecutor(2) as pool:
            outcomes = sorted(pool.map(lambda _: press(), range(2)))
    finally:
        del db.read_daily_service_costs
    assert outcomes.count("completed") == 1 and outcomes.count("conflict") == 1
    assert len(episode_rows(db)) == 1


def test_status_change_records_traceability_and_rejects_invalid_steps(episode_store):
    db = episode_store
    load_series(db, SPIKE)
    db.run_anomaly_detection("tenant-a", today=TODAY)
    [row] = episode_rows(db)
    investigating = db.change_anomaly_episode_status("tenant-a", row["id"], status="investigating", reason=None, actor="alice")
    assert investigating["status"] == "investigating" and investigating["status_changed_by"] == "alice"
    with pytest.raises(EpisodeConflict):
        db.change_anomaly_episode_status("tenant-a", row["id"], status="new", reason=None, actor="alice")
    resolved = db.change_anomaly_episode_status("tenant-a", row["id"], status="resolved", reason="Escalado revertido", actor="bob")
    [stored] = episode_rows(db)
    assert stored["status_changed_by"] == "bob" and stored["closure_reason"] == "Escalado revertido"
    assert stored["first_reviewed_at"] == investigating["first_reviewed_at"] < stored["closed_at"]
    assert resolved["closed_at"] == stored["closed_at"]
    for target in ("false_positive", "investigating"):
        with pytest.raises(EpisodeConflict):
            db.change_anomaly_episode_status("tenant-a", row["id"], status=target, reason="x", actor="alice")


def test_status_change_never_reaches_another_tenant(episode_store):
    db = episode_store
    load_series(db, SPIKE, tenant="tenant-b", run="run-b-tenant")
    db.run_anomaly_detection("tenant-b", today=TODAY)
    [row] = episode_rows(db)
    for identifier in (row["id"], "anomaly-" + "0" * 64):
        with pytest.raises(EpisodeNotFound):
            db.change_anomaly_episode_status("tenant-a", identifier, status="investigating", reason=None, actor="alice")
    assert episode_rows(db) == [row]


def test_concurrent_status_changes_have_exactly_one_winner(episode_store):
    db = episode_store
    load_series(db, SPIKE)
    db.run_anomaly_detection("tenant-a", today=TODAY)
    [row] = episode_rows(db)
    barrier = threading.Barrier(2)

    def close(target):
        barrier.wait(timeout=20)
        try:
            db.change_anomaly_episode_status("tenant-a", row["id"], status=target, reason="motivo", actor=target)
            return "ok"
        except EpisodeConflict:
            return "conflict"

    with ThreadPoolExecutor(2) as pool:
        outcomes = sorted(pool.map(close, ["resolved", "false_positive"]))
    assert outcomes == ["conflict", "ok"]
    [stored] = episode_rows(db)
    assert stored["status"] == stored["status_changed_by"]
