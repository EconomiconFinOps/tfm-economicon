"""Private operational/vector migrations before processor runtime is enabled."""
from pathlib import Path
from types import SimpleNamespace

from app.aws_bootstrap_common import grant_application_roles, require, run_entrypoint
from app.db.migration_runner import MigrationRunner


def execute(context, phase):
    if phase == 'fixtures':
        from app.aws_bootstrap_fixtures import load_fixture, seed_costs, seed_corpus
        from app.embeddings.providers import BedrockEmbeddingProvider
        from app.core.bedrock import TITAN_MODEL
        from app.vector_store.pgvector_store import PgVectorStore
        require(context.inputs['embedding']['dimension'] == 1024 and context.inputs['region'] == 'eu-south-2')
        fixture = load_fixture()
        engine = context.admin_engine('operational')
        try:
            seed_costs(engine, context.inputs, fixture)
        finally:
            engine.dispose()
        engine = context.admin_engine('vectors')
        try:
            store = PgVectorStore(engine.url.render_as_string(hide_password=False), 1024, engine=engine)
            store.initialize()
            provider = BedrockEmbeddingProvider(SimpleNamespace(embedding_model=TITAN_MODEL, embedding_dimension=1024,
                bedrock_region='eu-south-2', bedrock_timeout_seconds=30))
            seed_corpus(store, context.inputs, fixture, provider)
        finally:
            engine.dispose()
        return
    require(phase == 'database')
    dimension = context.inputs['embedding']['dimension']
    require(type(dimension) is int and dimension in {256, 512, 1024})
    for database, package, folder, ledger, kwargs in [
        ('operational', 'app.db.migrations', 'db/migrations', 'processor_schema_migrations', {}),
        ('vectors', 'app.vector_store.migrations', 'vector_store/migrations', 'vector_schema_migrations',
         {'001': {'embedding_dimension': dimension}}),
    ]:
        engine = context.admin_engine(database)
        try:
            MigrationRunner(engine, package, Path(__file__).parent / folder,
                            version_table=ledger, migration_kwargs=kwargs).run()
            grant_application_roles(engine, context.application_roles(database))
        finally:
            engine.dispose()


def main():
    return run_entrypoint('processor', execute)


if __name__ == '__main__':
    raise SystemExit(main())
