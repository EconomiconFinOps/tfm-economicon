from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier, Lock
from time import sleep
from types import SimpleNamespace
from unittest.mock import patch

from app.db.migration_runner import MigrationRunner


def test_worker_and_api_apply_each_migration_once(tmp_path):
    """Independent engines in the combined runtime must not migrate concurrently."""
    (tmp_path / "001_initial.py").touch()
    start = Barrier(2)
    transaction = Lock()
    applied = set()
    upgrades = []

    class Connection:
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

    def migrate():
        runner = MigrationRunner(Engine(), "migrations", tmp_path, "vector_schema_migrations")
        start.wait(timeout=5)
        runner.run()

    module = SimpleNamespace(upgrade=lambda connection: upgrades.append("001"))
    with patch("app.db.migration_runner.import_module", return_value=module):
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(migrate) for _ in range(2)]
            for future in futures:
                future.result(timeout=5)

    assert upgrades == ["001"]
    assert applied == {"001"}
