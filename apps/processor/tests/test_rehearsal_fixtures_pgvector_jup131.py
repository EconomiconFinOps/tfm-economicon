"""Real disposable SQL/generations; only native Bedrock responses are scripted."""
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, text

from app.aws_bootstrap_common import BootstrapError
from app.core.bedrock import TITAN_MODEL
from app.db.migration_runner import MigrationRunner
from app.embeddings.providers import BedrockEmbeddingProvider
from app.vector_store.pgvector_store import PgVectorStore
from test_vector_settings_pgvector import vector_database, backend_query_store


def config():
    return {'cycle_id': 'ensayo1', 'source_sha': 'a' * 40, 'region': 'eu-south-2', 'embedding': {'dimension': 1024}}


@pytest.fixture
def fixture_store(vector_database):
    engine = create_engine(vector_database)
    try:
        MigrationRunner(engine, 'app.db.migrations', Path(__file__).resolve().parents[1] / 'app/db/migrations',
                        version_table='processor_schema_migrations').run()
        store = PgVectorStore(vector_database.render_as_string(hide_password=False), 1024, engine=engine)
        store.initialize()
        yield engine, store
        store.close()
    finally:
        engine.dispose()


def native_provider():
    provider = BedrockEmbeddingProvider(SimpleNamespace(embedding_model=TITAN_MODEL, embedding_dimension=1024,
        bedrock_region='eu-south-2', bedrock_timeout_seconds=30))
    sdk = Mock()
    sdk.invoke_model.side_effect = lambda **kwargs: {'body': BytesIO(json.dumps({
        'embedding': [1.0] + [0.0] * 1023, 'inputTextTokenCount': 20}).encode())}
    provider.runtime._client = sdk
    return provider, sdk


def test_costs_and_native_corpus_are_restartable_and_tenant_scoped(fixture_store, backend_query_store):
    from app.aws_bootstrap_fixtures import seed_costs, seed_corpus, load_fixture
    engine, store = fixture_store
    provider, sdk = native_provider()
    fixture = load_fixture()
    seed_costs(engine, config(), fixture)
    first = seed_corpus(store, config(), fixture, provider)
    before = sdk.invoke_model.call_count
    seed_costs(engine, config(), fixture)
    assert seed_corpus(store, config(), fixture, provider) == first
    assert sdk.invoke_model.call_count == before
    assert before > 0
    with engine.connect() as connection:
        costs = connection.execute(text('SELECT tenant_id,pretax_cost::text FROM azure_cost_records ORDER BY tenant_id')).all()
        assert [(tenant, float(cost)) for tenant, cost in costs] == [('tenant-core', 12.5), ('tenant-growth', 999.99)]
        assert connection.execute(text("SELECT bool_and(request->'synthetic'='true'::jsonb) FROM azure_cost_ingestion_runs")).scalar_one()
    query = backend_query_store(store.database_url)
    try:
        plan = query.resolve_retrieval_plan('tenant-core', enabled=True)
        assert plan['descriptor']['provider'] == 'bedrock' and plan['descriptor']['dimension'] == 1024
        vector = query.embed_query('tenant-core', 'Guía sintética de ahorro', provider, plan)
        rows = query.search_chunks('tenant-core', vector, provider='bedrock', plan=plan, max_distance=2,
                                   question='Guía sintética de ahorro')
        assert rows and all(row['document_id'] == 'jup131-aws-v1-core' for row in rows)
        assert all('COSTE_GROWTH_PRIVADO' not in row['content'] for row in rows)
    finally:
        query.close()


def test_fixture_collision_fails_without_overwriting_costs_or_corpus(fixture_store):
    from app.aws_bootstrap_fixtures import seed_costs, seed_corpus, load_fixture
    engine, store = fixture_store
    fixture = load_fixture()
    provider, sdk = native_provider()
    seed_costs(engine, config(), fixture)
    seed_corpus(store, config(), fixture, provider)
    before = sdk.invoke_model.call_count
    with engine.begin() as connection:
        connection.execute(text("UPDATE azure_cost_records SET pretax_cost=33 WHERE tenant_id='tenant-core'"))
    with pytest.raises(BootstrapError):
        seed_costs(engine, config(), fixture)
    with store.engine.begin() as connection:
        connection.execute(text("UPDATE knowledge_documents SET text_content='foreign-content' WHERE id='jup131-aws-v1-core'"))
    with pytest.raises(BootstrapError):
        seed_corpus(store, config(), fixture, provider)
    assert sdk.invoke_model.call_count == before
    with engine.connect() as connection:
        assert float(connection.execute(text("SELECT pretax_cost FROM azure_cost_records WHERE tenant_id='tenant-core'")).scalar_one()) == 33
