"""Versioned migrations; opt-in schema steps commit DDL before version DML."""
from importlib import import_module
from pathlib import Path
from sqlalchemy import text


class MigrationRunner:
    def __init__(self, engine, migration_package: str, migrations_dir: Path):
        self.engine=engine
        self.migration_package=migration_package
        self.migrations_dir=migrations_dir

    def verify(self) -> None:
        from sqlalchemy import inspect
        from app.core.runtime_secrets import StartupError
        try:
            with self.engine.connect() as connection:
                versions={row.version for row in connection.execute(text('SELECT version FROM schema_migrations'))}
                if not {'001','002','003','004','005'}.issubset(versions):
                    raise ValueError('Incomplete migration.')
                for name in ('tenants','users','user_tenants','conversations','messages','jobs'):
                    if not inspect(connection).has_table(name):
                        raise ValueError('Missing legacy table.')
                module=import_module(f'{self.migration_package}.005_reconcile_chat_anomalies')
                module.verify(connection)
        except Exception:
            raise StartupError('Backend schema is not ready; run the exclusive migrator.') from None

    def run(self) -> None:
        files = sorted(self.migrations_dir.glob("[0-9][0-9][0-9]_*.py"))
        groups = {}
        for file in files:
            groups.setdefault(file.stem.split('_', 1)[0], []).append(file)
        reconcile = any(file.stem == '005_reconcile_chat_anomalies' for file in files)
        for version, entries in groups.items():
            if len(entries) > 1 and not (reconcile and version == '002' and
                    {entry.stem for entry in entries} == {'002_chat_operations','002_anomaly_episodes'}):
                raise RuntimeError('Duplicate migration identifier.')
        with self.engine.begin() as connection:
            connection.execute(text("""CREATE TABLE IF NOT EXISTS schema_migrations (
                version STRING PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"""))
            applied={row.version for row in connection.execute(text("SELECT version FROM schema_migrations"))}
        for migration_file in files:
            version=migration_file.stem.split("_",maxsplit=1)[0]
            if version in applied and not (reconcile and version == '002'): continue
            register = not (reconcile and version == '002' and migration_file != groups[version][-1])
            module=import_module(f"{self.migration_package}.{migration_file.stem}")
            if hasattr(module,'schema_steps'):
                for index,statement in enumerate(module.schema_steps()):
                    # A single ephemeral migrator is required. Each step is
                    # separately committed, inspectable and restartable.
                    with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
                        if not module.step_applied(connection,index):
                            connection.execute(text(statement))
                        if not module.step_applied(connection,index):
                            raise RuntimeError('Schema step is not ready.')
                if hasattr(module,'backfill'):
                    module.backfill(self.engine)
                with self.engine.begin() as connection:
                    module.verify(connection)
                    if register and version not in applied:
                        connection.execute(text("INSERT INTO schema_migrations(version) VALUES(:version)"),{'version':version})
            else:
                # Legacy 001 remains on its existing transaction path.
                with self.engine.begin() as connection:
                    module.upgrade(connection)
                    if register and version not in applied:
                        connection.execute(text("INSERT INTO schema_migrations(version) VALUES(:version)"),{'version':version})

            if register:
                applied.add(version)
