"""Exclusive, explicit migration/seed entrypoint; never run by verify-only API."""
from pathlib import Path

from app.core.config import get_settings
from app.core.runtime_secrets import startup_boundary
from app.db.database import Database
from app.db.migration_runner import MigrationRunner


@startup_boundary
def main():
    database=Database(get_settings().database_url.get_secret_value())
    try:
        runner=MigrationRunner(database.engine,'app.db.migrations',Path(__file__).parent/'db/migrations')
        runner.run()
        runner.verify()
        database._seed_defaults()
    finally:
        database.dispose()


if __name__=='__main__':
    main()
