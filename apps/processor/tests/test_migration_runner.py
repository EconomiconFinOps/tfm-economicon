from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier, Lock
from time import sleep
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text

from app.db.migration_runner import MigrationRunner


@pytest.mark.parametrize("transactional", [True, False], ids=["transaction", "autocommit"])
def test_worker_and_api_apply_each_migration_once(tmp_path, transactional):
    """Independent engines in the combined runtime must not migrate concurrently."""
    (tmp_path / "001_initial.py").touch()
    start = Barrier(2)
    transaction = Lock()
    applied = set()
    upgrades = []

    class Connection:
        def execution_options(self, **options):
            assert options == {"isolation_level": "AUTOCOMMIT"}
            return self

        def execute(self, statement, parameters=None):
            sql = str(statement).strip()
            if sql.startswith("SELECT version"):
                return [SimpleNamespace(version=version) for version in applied]
            if sql.startswith("INSERT INTO"):
                assert parameters["version"] not in applied
                applied.add(parameters["version"])
            return []

    class Engine:
        @contextmanager
        def begin(self):
            # Model PostgreSQL's conflicting concurrent DDL on an empty schema.
            assert transaction.acquire(blocking=False), "concurrent migration transaction"
            try:
                sleep(0.05)
                yield Connection()
            finally:
                transaction.release()

        connect = begin

    def migrate():
        runner = MigrationRunner(Engine(), "migrations", tmp_path, "vector_schema_migrations")
        start.wait(timeout=5)
        runner.run()

    module = SimpleNamespace(
        upgrade=lambda connection: upgrades.append("001"), transactional=transactional,
    )
    with patch("app.db.migration_runner.import_module", return_value=module):
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(migrate) for _ in range(2)]
            for future in futures:
                future.result(timeout=5)

    assert upgrades == ["001"]
    assert applied == {"001"}


@pytest.fixture
def runner_factory(monkeypatch):
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "before_cursor_execute", retval=True)
    def ledger_default(connection, cursor, statement, parameters, context, executemany):
        # SQLite supplies real commit/rollback behavior; only this SQL default differs.
        if "CREATE TABLE IF NOT EXISTS schema_migrations" in statement:
            statement = statement.replace("now()", "CURRENT_TIMESTAMP")
        return statement, parameters

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE effects (version TEXT PRIMARY KEY)"))

    def make_runner(modules):
        names = {f"{version}_test": module for version, module in modules.items()}
        monkeypatch.setattr(
            "app.db.migration_runner.import_module",
            lambda name: names[name.rsplit(".", 1)[1]],
        )
        directory = SimpleNamespace(glob=lambda pattern: [Path(name + ".py") for name in reversed(names)])
        return MigrationRunner(engine, "test_migrations", directory)

    yield engine, make_runner
    engine.dispose()


def _versions(engine, table):
    with engine.connect() as connection:
        return list(connection.execute(text(f"SELECT version FROM {table} ORDER BY version")).scalars())


def _migration(version, **flags):
    def upgrade(connection):
        connection.execute(text("INSERT INTO effects (version) VALUES (:version)"), {"version": version})

    return SimpleNamespace(upgrade=upgrade, **flags)


@pytest.mark.parametrize("explicit_transaction", [False, True], ids=["default", "explicit"])
@pytest.mark.parametrize("failure", ["upgrade", "ledger"])
def test_transactional_failure_rolls_back_only_current_migration(
    runner_factory, explicit_transaction, failure,
):
    engine, make_runner = runner_factory
    failing = _migration("002", **({"transactional": True} if explicit_transaction else {}))
    original_upgrade = failing.upgrade

    def fail_upgrade(connection):
        original_upgrade(connection)
        assert list(connection.execute(text("SELECT version FROM schema_migrations ORDER BY version")).scalars()) == ["001"]
        raise RuntimeError("injected upgrade failure")

    def fail_ledger(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("INSERT INTO schema_migrations") and parameters == ("002",):
            raise RuntimeError("injected ledger failure")

    if failure == "upgrade":
        failing.upgrade = fail_upgrade
    else:
        event.listen(engine, "before_cursor_execute", fail_ledger)
    runner = make_runner({"001": _migration("001"), "002": failing, "003": _migration("003")})
    try:
        with pytest.raises(RuntimeError, match=f"injected {failure} failure"):
            runner.run()
    finally:
        if failure == "ledger":
            event.remove(engine, "before_cursor_execute", fail_ledger)

    assert _versions(engine, "schema_migrations") == ["001"]
    assert _versions(engine, "effects") == ["001"]
    failing.upgrade = original_upgrade
    runner.run()
    assert _versions(engine, "schema_migrations") == ["001", "002", "003"]
    assert _versions(engine, "effects") == ["001", "002", "003"]
    runner.run()  # Re-executing any completed upgrade would violate the effects primary key.
    assert _versions(engine, "effects") == ["001", "002", "003"]


@pytest.mark.parametrize("acknowledged_commit", [False, True], ids=["insert-fails", "ack-lost"])
def test_autocommit_completion_retry_and_subsequent_transaction_isolation(
    runner_factory, acknowledged_commit,
):
    engine, make_runner = runner_factory
    upgrade_calls = []

    def upgrade(connection):
        upgrade_calls.append("003")
        assert list(connection.execute(text("SELECT version FROM schema_migrations ORDER BY version")).scalars()) == ["001"]
        connection.execute(text("INSERT INTO effects (version) VALUES ('003') ON CONFLICT DO NOTHING"))

    def fail_completion(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().startswith("INSERT INTO schema_migrations") and parameters == ("003",):
            raise RuntimeError("injected completion failure")

    def later_upgrade(connection):
        connection.execute(text("INSERT INTO effects (version) VALUES ('004')"))
        raise RuntimeError("injected later failure")

    runner = make_runner({
        "001": _migration("001"),
        "003": SimpleNamespace(upgrade=upgrade, transactional=False),
        "004": SimpleNamespace(upgrade=later_upgrade),
    })
    hook = "after_cursor_execute" if acknowledged_commit else "before_cursor_execute"
    event.listen(engine, hook, fail_completion)
    try:
        with pytest.raises(RuntimeError, match="injected completion failure"):
            runner.run()
    finally:
        event.remove(engine, hook, fail_completion)

    assert _versions(engine, "effects") == ["001", "003"]
    assert _versions(engine, "schema_migrations") == (["001", "003"] if acknowledged_commit else ["001"])
    assert upgrade_calls == ["003"]

    with pytest.raises(RuntimeError, match="injected later failure"):
        runner.run()
    assert upgrade_calls == (["003"] if acknowledged_commit else ["003", "003"])
    assert _versions(engine, "schema_migrations") == ["001", "003"]
    assert _versions(engine, "effects") == ["001", "003"]
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO effects (version) VALUES ('probe')"))
        connection.rollback()
    assert _versions(engine, "effects") == ["001", "003"]
