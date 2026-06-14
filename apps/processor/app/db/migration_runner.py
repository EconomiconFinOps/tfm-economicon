from importlib import import_module
from pathlib import Path

from sqlalchemy import text


class MigrationRunner:
    def __init__(
        self,
        engine,
        migration_package: str,
        migrations_dir: Path,
        version_table: str = "schema_migrations",
    ):
        self.engine = engine
        self.migration_package = migration_package
        self.migrations_dir = migrations_dir
        self.version_table = version_table

    def run(self) -> None:
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
                module.upgrade(connection)
                connection.execute(
                    text(f"INSERT INTO {self.version_table} (version) VALUES (:version)"),
                    {"version": version},
                )
