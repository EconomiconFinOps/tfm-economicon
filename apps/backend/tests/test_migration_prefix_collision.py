"""Separate migration identities after merging independently numbered changes."""
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, event, text

from app.db import migration_runner


@pytest.mark.parametrize("legacy_prefix", [False, True])
def test_colliding_prefixes_both_apply_once(tmp_path, monkeypatch, legacy_prefix):
    engine = create_engine("sqlite://")
    event.listen(engine, "before_cursor_execute",
                 lambda c, cursor, sql, args, context, many:
                 (sql.replace("DEFAULT now()", "DEFAULT CURRENT_TIMESTAMP"), args), retval=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY)"))
        if legacy_prefix:
            connection.execute(text("INSERT INTO schema_migrations VALUES ('002')"))
    for name in ("002_anomaly_episodes", "002_chat_operations"):
        (tmp_path / (name + ".py")).touch()
    calls = []

    def module(name):
        def upgrade(connection):
            calls.append(name)
            connection.execute(text("CREATE TABLE IF NOT EXISTS " + name.rsplit(".", 1)[-1] + "_table (id INT)"))
        return SimpleNamespace(upgrade=upgrade)

    # Table names cannot begin with a digit in SQLite.
    def module_for(name):
        result = module(name.replace("002_", "migration_"))
        return result

    monkeypatch.setattr(migration_runner, "import_module", module_for)
    runner = migration_runner.MigrationRunner(engine, "test", tmp_path)
    runner.run()
    runner.run()
    assert calls == ["test.migration_anomaly_episodes", "test.migration_chat_operations"]
    with engine.connect() as connection:
        versions = set(connection.execute(text("SELECT version FROM schema_migrations")).scalars())
    assert {"002_anomaly_episodes", "002_chat_operations"} <= versions
    engine.dispose()
