"""Private backend owner migration; normal services only verify the schema."""
from pathlib import Path

from app.aws_bootstrap_common import grant_application_roles, require, run_entrypoint
from app.db.migration_runner import MigrationRunner


def execute(context, phase):
    if phase == 'fixtures':
        from app.aws_bootstrap_identity import ensure_identity, bind_identity
        identity = ensure_identity(context)
        engine = context.admin_engine('operational')
        try:
            bind_identity(engine, identity)
        finally:
            engine.dispose()
        return
    if phase == 'broker':
        from app.aws_bootstrap_broker import configure_broker
        configure_broker(context)
        return
    require(phase == 'database')
    engine = context.admin_engine('operational')
    try:
        MigrationRunner(engine, 'app.db.migrations', Path(__file__).parent / 'db/migrations').run()
        grant_application_roles(engine, context.application_roles('operational'))
    finally:
        engine.dispose()


def main():
    return run_entrypoint('backend', execute)


if __name__ == '__main__':
    raise SystemExit(main())
