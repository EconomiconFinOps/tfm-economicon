from importlib import import_module
from pathlib import Path
import os
from threading import Lock

from sqlalchemy import inspect, text
from app.core.runtime_secrets import StartupError


# run_all starts the worker and API in separate threads, both of which migrate.
# Serialize the entire run, including per-migration transactions and autocommit DDL.
_migration_lock = Lock()


def initialize_schema(runner, required_tables):
    mode = os.getenv('PROCESSOR_SCHEMA_MODE', 'migrate')
    if mode == 'verify':
        runner.verify(required_tables)
    elif mode == 'migrate':
        runner.run()
    else:
        raise StartupError('Invalid processor schema mode.')


class MigrationRunner:
    def __init__(
        self,
        engine,
        migration_package: str,
        migrations_dir: Path,
        version_table: str,
        *,
        migration_kwargs: dict[str, dict[str, object]] | None = None,
    ):
        self.engine = engine
        self.migration_package = migration_package
        self.migrations_dir = migrations_dir
        self.version_table = version_table
        self.migration_kwargs = migration_kwargs or {}

    def verify(self, required_tables):
        """Read-only admission for tasks whose role cannot execute migrations."""
        try:
            expected = {path.stem.split('_', 1)[0]
                        for path in self.migrations_dir.glob('[0-9][0-9][0-9]_*.py')}
            if not expected:
                raise ValueError()
            with self.engine.connect() as connection:
                applied = set(connection.execute(text(f'SELECT version FROM {self.version_table}')).scalars())
                if not expected.issubset(applied):
                    raise ValueError()
                inspector = inspect(connection)
                for table, required in required_tables.items():
                    actual = {column['name'] for column in inspector.get_columns(table)}
                    if not required.issubset(actual):
                        raise ValueError()
        except Exception:
            raise StartupError('Processor schema is not ready; run the exclusive bootstrap migrator.') from None

    def run(self) -> None:
        with _migration_lock:
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self.version_table} (
                            version TEXT PRIMARY KEY,
                            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        )
                        """
                    )
                )
                applied = {
                    row.version
                    for row in connection.execute(text(f"SELECT version FROM {self.version_table}"))
                }

            for migration_file in sorted(self.migrations_dir.glob("[0-9][0-9][0-9]_*.py")):
                version = migration_file.stem.split("_", maxsplit=1)[0]
                if version in applied:
                    continue
                module = import_module(f"{self.migration_package}.{migration_file.stem}")
                transactional = getattr(module, "transactional", True) is not False
                with (self.engine.begin() if transactional else self.engine.connect()) as connection:
                    if not transactional:
                        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
                    module.upgrade(connection, **self.migration_kwargs.get(version, {}))
                    connection.execute(
                        text(f"INSERT INTO {self.version_table} (version) VALUES (:version)"),
                        {"version": version},
                    )
