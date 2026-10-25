"""Native dimensions and actual SQL retrieval; Bedrock SDK alone is scripted."""
from io import BytesIO
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import text

from app.core.bedrock import TITAN_MODEL
from app.core.config import Settings
from app.db.migration_runner import MigrationRunner
from app.embeddings.providers import get_embedding_provider
from app.embeddings.space import EmbeddingSpace, canonical
from app.vector_store.pgvector_store import PgVectorStore
from test_embedding_generations_pgvector import setup, publish, legacy_rows
from test_vector_settings_pgvector import vector_database, backend_query_store


def test_native_generation_keeps_legacy_vectors_and_space_isolation(setup, backend_query_store):
    from app.embeddings.providers import MockEmbeddingProvider
    store, generations, old_space = setup
    publish(store)
    original = legacy_rows(store)
    old_id = generations.build('a', old_space, MockEmbeddingProvider(1536))
    generations.activate('a',old_id,expected_head=None,expected_version=0)
    settings = Settings(embedding_provider='bedrock',embedding_model=TITAN_MODEL,
        embedding_dimension=1024,bedrock_region='eu-west-1',_env_file=None)
    provider = get_embedding_provider('bedrock',1024,settings)
    sdk = Mock()
    sdk.invoke_model.side_effect = lambda **kwargs: {'body': BytesIO(json.dumps({
        'embedding':[1.0]+[0.0]*1023,'inputTextTokenCount':4}).encode())}
    provider.runtime._client = sdk
    native = EmbeddingSpace('bedrock',TITAN_MODEL,provider.mapping_sha256,generations.counter.identity,dimension=1024)
    native_id = generations.build('a',native,provider)
    generations.activate('a',native_id,expected_head=old_id,expected_version=1)
    query = backend_query_store(store.database_url)
    try:
        plan = query.resolve_retrieval_plan('a',enabled=True)
        assert plan['descriptor']['dimension'] == 1024
        vector = query.embed_query('a','Original evidence.',provider,plan)
        assert len(vector) == 1024
        result = query.search_chunks('a',vector,provider='bedrock',plan=plan,max_distance=2,question='Original evidence.')
        assert [row['content'] for row in result] == ['Original evidence.']
        assert result[0]['retrieval']['generation_id'] == native_id
        assert legacy_rows(store) == original
        with store.engine.connect() as connection:
            assert set(connection.execute(text('SELECT DISTINCT vector_dims(embedding) FROM embedding_cache')).scalars()) == {1024,1536}
        with pytest.raises(ValueError):
            query.embed_query('b','texto',provider,plan)
        provider.mapping_sha256 = 'f'*64
        with pytest.raises(ValueError):
            query.embed_query('a','texto',provider,plan)
    finally:
        query.close()


def test_cache_dimension_migration_preserves_existing_rows(vector_database,tmp_path):
    store = PgVectorStore(vector_database.render_as_string(hide_password=False),1536)
    old = tmp_path/'pre-native-cache'
    old.mkdir()
    for name in ('001_initial','002_tenant_search_index','003_chunking_metadata','004_embedding_generations'):
        (old/f'{name}.py').touch()
    try:
        MigrationRunner(store.engine,'app.vector_store.migrations',old,version_table='vector_schema_migrations',
            migration_kwargs={'001':{'embedding_dimension':1536}}).run()
        space = EmbeddingSpace('mock','mock/sha256_v1','a'*64,'fixture-tokenizer')
        value = '['+','.join(['1']+['0']*1535)+']'
        with store.engine.begin() as connection:
            connection.execute(text('INSERT INTO embedding_spaces(id,descriptor) VALUES(:id,CAST(:data AS jsonb))'),
                {'id':space.id,'data':canonical(space.descriptor())})
            connection.execute(text("INSERT INTO embedding_cache(tenant_id,space_id,text_hash,embedding,token_count) VALUES('a',:space,'before',CAST(:vector AS vector),1)"),
                {'space':space.id,'vector':value})
        store.initialize()
        store.initialize()
        with store.engine.connect() as connection:
            row = connection.execute(text("SELECT vector_dims(embedding),embedding::text FROM embedding_cache WHERE text_hash='before'")).one()
            assert row == (1536,value)
            assert connection.execute(text("SELECT version FROM vector_schema_migrations WHERE version='005'")).scalar_one() == '005'
    finally:
        store.close()
