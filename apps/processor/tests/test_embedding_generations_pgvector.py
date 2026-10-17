import pytest
from sqlalchemy import text
from app.embeddings.providers import MockEmbeddingProvider
from app.embeddings.space import EmbeddingSpace
from app.embeddings.tokenization import EmbeddingTokenCounter
from app.vector_store.pgvector_store import PgVectorStore
from app.vector_store.generations import GenerationStore, StaleGeneration
from app.vector_store.pgvector_store import StalePublication
from test_vector_settings_pgvector import vector_database, backend_query_store


@pytest.fixture
def setup(vector_database):
    store = PgVectorStore(vector_database.render_as_string(hide_password=False), 1536)
    try:
        store.initialize()
        counter = EmbeddingTokenCounter()
        identity = EmbeddingSpace('mock', 'mock/sha256_v1', 'a' * 64, counter.identity)
        generations = GenerationStore(store.engine, counter)
        yield store, generations, identity
    finally:
        store.close()


def publish(store, tenant='a', document='doc', content='Original evidence.'):
    return store.store_document(job_id=document, tenant_id=tenant, source='synthetic', artifact_uri=None,
        text_content=content, chunks=[content], embeddings=[[1.0] + [0.0] * 1535], provider_name='mock')


def legacy_rows(store):
    with store.engine.connect() as connection:
        return connection.execute(text('SELECT kd.id,dc.id,dc.content,ce.embedding::text FROM knowledge_documents kd JOIN document_chunks dc ON dc.document_id=kd.id JOIN chunk_embeddings ce ON ce.chunk_id=dc.id ORDER BY kd.id')).all()


def test_real_adaptive_migration_snapshot_cache_and_atomic_rollback(setup):
    store, generations, identity = setup
    publish(store)
    before = legacy_rows(store)
    class Counting(MockEmbeddingProvider):
        calls = 0
        def embed_batch(self, texts, **kwargs):
            self.calls += 1
            return super().embed_batch(texts)
    provider = Counting(1536)
    first = generations.build('a', identity, provider)
    second = generations.build('a', identity, provider)
    assert provider.calls == 1  # Generation identity is not a cache key.
    assert generations.active_plan('a')['generation_id'] is None
    head = generations.activate('a', first, expected_head=None, expected_version=0)
    head = generations.activate('a', second, expected_head=first, expected_version=head['version'])
    head = generations.rollback('a', expected_head=second, expected_version=head['version'])
    assert head['generation_id'] == first and legacy_rows(store) == before
    with store.engine.connect() as connection:
        assert list(connection.execute(text('SELECT version FROM vector_schema_migrations ORDER BY version')).scalars()) == ['001', '002', '003', '004']
        assert connection.execute(text('SELECT count(*) FROM embedding_cache')).scalar_one() == 1


def test_catalog_change_and_incomplete_generation_are_rejected_without_activation(setup):
    store, generations, identity = setup
    publish(store)
    candidate = generations.build('a', identity, MockEmbeddingProvider(1536))
    publish(store, document='new-document', content='Concurrent publication.')
    with pytest.raises(StaleGeneration, match='catalog'):
        generations.activate('a', candidate, expected_head=None, expected_version=0)
    candidate = generations.build('a', identity, MockEmbeddingProvider(1536))
    with store.engine.begin() as connection:
        connection.execute(text('DELETE FROM rag_chunk_vectors WHERE chunk_id=:id'), {'id': 'doc:chunk:0'})
    with pytest.raises(ValueError, match='Incomplete'):
        generations.activate('a', candidate, expected_head=None, expected_version=0)
    assert generations.active_plan('a')['generation_id'] is None


def test_tenant_isolation_and_authorization_before_state_changes(setup):
    store, generations, identity = setup
    publish(store)
    publish(store, tenant='b', document='foreign-doc', content='Foreign private evidence.')
    first = generations.build('a', identity, MockEmbeddingProvider(1536))
    with pytest.raises(ValueError):
        generations.activate('b', first, expected_head=None, expected_version=0)
    def denied():
        raise PermissionError('Not authorized')
    with pytest.raises(PermissionError):
        generations.activate('a', first, expected_head=None, expected_version=0, authorize=denied)
    with store.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM embedding_cache WHERE tenant_id=:tenant'), {'tenant': 'b'}).scalar_one() == 0
    assert generations.active_plan('a')['generation_id'] is None


def test_online_publication_switches_complete_snapshot_and_keeps_old_revision(setup):
    store, generations, identity = setup
    publish(store)
    first = generations.build('a', identity, MockEmbeddingProvider(1536))
    generations.activate('a', first, expected_head=None, expected_version=0)
    provider = MockEmbeddingProvider(1536)
    prepared = store.prepare_index_publication(tenant_id='a', job_id='doc', source='synthetic',
        text_content='Updated evidence.', chunks=['Updated evidence.'], document_metadata=None, provider=provider)
    published = store.store_document(job_id='doc', tenant_id='a', source='synthetic', artifact_uri=None,
        text_content='Updated evidence.', chunks=['Updated evidence.'], embeddings=prepared['plain_embeddings'],
        provider_name='mock', prepared_index=prepared)
    head = generations.active_plan('a')
    assert head['generation_id'] == published['index_generation_id'] != first and head['version'] == 2
    with store.engine.connect() as connection:
        revisions = list(connection.execute(text('SELECT content FROM rag_document_revisions ORDER BY content')).scalars())
        assert revisions == ['Original evidence.', 'Updated evidence.']
        assert connection.execute(text('SELECT count(*) FROM rag_generation_members')).scalar_one() == 2
    with pytest.raises(StaleGeneration, match='rebuild'):
        generations.rollback('a', expected_head=head['generation_id'], expected_version=head['version'])


def test_concurrent_preparation_and_changed_payload_leave_catalog_unchanged(setup):
    store, generations, identity = setup
    publish(store)
    first = generations.build('a', identity, MockEmbeddingProvider(1536))
    generations.activate('a', first, expected_head=None, expected_version=0)
    prepared = generations.prepare_publication('a', 'doc', 'synthetic', 'Updated.', ['Updated.'], {}, MockEmbeddingProvider(1536))
    before = legacy_rows(store)
    with pytest.raises(ValueError, match='does not match'):
        store.store_document(job_id='doc', tenant_id='a', source='synthetic', artifact_uri=None, text_content='Changed.',
            chunks=['Changed.'], embeddings=[[1.] + [0.] * 1535], provider_name='mock', prepared_index=prepared)
    assert legacy_rows(store) == before and generations.active_plan('a')['generation_id'] == first
    second = generations.build('a', identity, MockEmbeddingProvider(1536))
    generations.activate('a', second, expected_head=first, expected_version=1)
    with pytest.raises(StalePublication):
        store.store_document(job_id='doc', tenant_id='a', source='synthetic', artifact_uri=None, text_content='Updated.',
            chunks=['Updated.'], embeddings=prepared['plain_embeddings'], provider_name='mock', prepared_index=prepared)
    assert legacy_rows(store) == before and generations.active_plan('a')['generation_id'] == second


def test_real_backend_captured_generation_query_cache_and_online_snapshot(setup, backend_query_store):
    store, generations, identity = setup
    publish(store)
    first = generations.build('a', identity, MockEmbeddingProvider(1536))
    generations.activate('a', first, expected_head=None, expected_version=0)
    query = backend_query_store(store.database_url)
    class Counting(MockEmbeddingProvider):
        calls = []
        def embed(self, value):
            self.calls.append(value)
            return super().embed(value)
    provider = Counting(1536)
    try:
        assert query.resolve_retrieval_plan('a') is None  # Stable default remains legacy.
        plan = query.resolve_retrieval_plan('a', enabled=True)
        vector = query.embed_query('a', 'Original evidence.', provider, plan)
        assert query.embed_query('a', 'Original evidence.', provider, plan) == vector
        assert provider.calls == []  # Exact document text was already cached in the same space.
        query.embed_query('a', 'New question?', provider, plan)
        query.embed_query('a', 'New question?', provider, plan)
        assert provider.calls == ['New question?']
        prepared = generations.prepare_publication('a', 'doc', 'synthetic', 'Updated.', ['Updated.'], {}, provider)
        store.store_document(job_id='doc', tenant_id='a', source='synthetic', artifact_uri=None, text_content='Updated.',
            chunks=['Updated.'], embeddings=prepared['plain_embeddings'], provider_name='mock', prepared_index=prepared)
        old = query.search_chunks('a', vector, provider='mock', max_distance=2, plan=plan, question='Original evidence.')
        new_plan = query.resolve_retrieval_plan('a', enabled=True)
        new = query.search_chunks('a', vector, provider='mock', max_distance=2, plan=new_plan, question='Original evidence.')
        assert [item['content'] for item in old] == ['Original evidence.']
        assert [item['content'] for item in new] == ['Updated.']
        assert old[0]['retrieval']['generation_id'] == first != new[0]['retrieval']['generation_id']
        with pytest.raises(ValueError, match='scope'):
            query.search_chunks('b', vector, provider='mock', plan=plan, question='Original evidence.')
    finally:
        query.close()


def test_real_fts_literal_comparators_lexical_rescue_and_independent_flags(setup, backend_query_store):
    store, generations, identity = setup
    publish(store, document='correct', content='cost > 20 EUR')
    publish(store, document='wrong-op', content='cost >= 20 EUR')
    publish(store, document='wrong-number', content='cost > 200 EUR')
    class Orthogonal(MockEmbeddingProvider):
        def embed(self, value):
            return [0., 1.] + [0.] * 1534
    candidate = generations.build('a', identity, Orthogonal(1536), retrieval_mode='hybrid', rrf_k=120)
    generations.activate('a', candidate, expected_head=None, expected_version=0)
    query = backend_query_store(store.database_url)
    try:
        with pytest.raises(ValueError, match='disabled'):
            query.resolve_retrieval_plan('a', enabled=True)
        plan = query.resolve_retrieval_plan('a', enabled=True, hybrid=True)
        vector = [1.] + [0.] * 1535
        hits = query.search_chunks('a', vector, max_distance=.6, provider='mock', plan=plan, question='`cost > 20 EUR`')
        assert [item['document_id'] for item in hits] == ['correct']
        assert hits[0]['distance'] == 1. and hits[0]['retrieval']['dense_rank'] is None
        assert hits[0]['retrieval']['lexical_rank'] == 1
        assert hits[0]['retrieval']['rrf_score'] == pytest.approx(1/121) and plan['retrieval_config']['rrf_k'] == 120
        assert query.search_chunks('a', vector, max_distance=.6, provider='mock', plan=plan, question='20') == []
        with store.engine.connect() as connection:
            assert 'USING gin (search_vector)' in connection.execute(text("SELECT indexdef FROM pg_indexes WHERE indexname='rag_revision_chunks_fts'")).scalar_one()
    finally:
        query.close()


@pytest.mark.parametrize('dense', [False, True])
@pytest.mark.parametrize('number', ['20', '20.5'])
def test_real_unquoted_percent_rejects_wrong_units_from_both_lanes(setup, backend_query_store, dense, number):
    store, generations, identity = setup
    for identifier, content in [('correct', f'utilization > {number}%'), ('wrong-unit', f'utilization > {number} USD'),
                                ('wrong-op', f'utilization >= {number}%'), ('wrong-number', 'utilization > 200%')]:
        publish(store, document=identifier, content=content)
    class Fixed(MockEmbeddingProvider):
        def embed(self, value):
            return [0., 1.] + [0.] * 1534
    candidate = generations.build('a', identity, Fixed(1536), retrieval_mode='hybrid')
    generations.activate('a', candidate, expected_head=None, expected_version=0)
    query = backend_query_store(store.database_url)
    try:
        plan = query.resolve_retrieval_plan('a', enabled=True, hybrid=True)
        vector = ([0., 1.] if dense else [1., 0.]) + [0.] * 1534
        hits = query.search_chunks('a', vector, max_distance=.6, provider='mock', plan=plan,
                                   question=f'utilization > {number}%')
        assert [item['document_id'] for item in hits] == ['correct']
        assert hits[0]['retrieval']['dense_rank'] == (1 if dense else None)
        assert hits[0]['retrieval']['lexical_rank'] == 1
        assert hits[0]['distance'] == (0. if dense else 1.)
    finally:
        query.close()


def test_preparation_warnings_survive_build_cache_hits_and_online_publication(setup):
    from dataclasses import replace
    from app.embeddings.normalized import manual_document, parent_metadata
    from app.embeddings.structural_chunker import StructuredChunker
    store, generations, identity = setup
    provider = MockEmbeddingProvider(1536)
    contextual = replace(identity, preparation='contextual_embedding_v1')
    def payload(identifier, title):
        document = manual_document({'job_id': identifier, 'tenant_id': 'a', 'source': 'synthetic', 'text_content': 'Evidence.'})
        document['file_metadata']['title'] = title
        result = StructuredChunker(counter=generations.counter).chunk_document(document)
        return result['chunks'], parent_metadata(document, result['manifest'])
    def save(identifier, title, prepared=None):
        chunks, metadata = payload(identifier, title)
        return store.store_document(job_id=identifier, tenant_id='a', source='synthetic', artifact_uri=None,
            text_content='Evidence.', chunks=chunks, embeddings=[provider.embed('Evidence.')],
            provider_name='mock', document_metadata=metadata, prepared_index=prepared)
    def prepare(identifier, title):
        chunks, metadata = payload(identifier, title)
        return generations.prepare_publication('a', identifier, 'synthetic', 'Evidence.', chunks, metadata, provider)
    save('long', 'a' * 600)
    save('exact', 'a' * 512)
    first = generations.build('a', contextual, provider)
    inspected = generations.inspect('a', first)['generations'][0]
    diagnostics = inspected['manifest']['preparation_warnings']
    assert len(diagnostics) == 1 and diagnostics[0]['document_id'] == 'long'
    assert diagnostics[0]['warnings'] == ['embedding_context_truncated']
    assert diagnostics[0]['chunk_id'] == payload('long', 'a' * 600)[0][0]['chunk_id']
    with store.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM embedding_cache')).scalar_one() == 1
        assert connection.execute(text("SELECT metadata->>'title' FROM knowledge_documents WHERE id='long'")).scalar_one() == 'a' * 600
    plain = generations.build('a', identity, provider)
    assert generations.inspect('a', plain)['generations'][0]['manifest']['preparation_warnings'] == []
    generations.activate('a', first, expected_head=None, expected_version=0)
    title = '漢字🙂' * 600
    prepared = prepare('online', title)
    assert prepared['preparation_warnings'] == [['embedding_context_truncated']]
    online = save('online', title, prepared)['index_generation_id']
    assert {item['document_id'] for item in generations.inspect('a', online)['generations'][0]['manifest']['preparation_warnings']} == {'long', 'online'}
    # The exact same embedding text is cached, but the new unshortened source
    # has no warning. Old snapshots keep their diagnostic and canonical content.
    prepared = prepare('long', 'a' * 512)
    assert prepared['preparation_warnings'] == [[]]
    updated = save('long', 'a' * 512, prepared)['index_generation_id']
    assert [item['document_id'] for item in generations.inspect('a', updated)['generations'][0]['manifest']['preparation_warnings']] == ['online']
    assert generations.inspect('a', first)['generations'][0]['manifest']['preparation_warnings'] == diagnostics
    with store.engine.connect() as connection:
        assert set(connection.execute(text('SELECT content FROM rag_revision_chunks')).scalars()) == {'Evidence.'}


def test_failed_build_resumes_exact_generation_and_reuses_completed_cache(setup):
    store, generations, identity = setup
    publish(store, document='a', content='First evidence.')
    publish(store, document='b', content='Second evidence.')
    class Interrupted(MockEmbeddingProvider):
        calls = 0
        def embed_batch(self, values, **kwargs):
            self.calls += 1
            if self.calls == 2: raise RuntimeError('synthetic interrupted build')
            return super().embed_batch(values)
    provider = Interrupted(1536)
    with pytest.raises(RuntimeError): generations.build('a', identity, provider)
    failed = generations.inspect('a')['generations'][0]
    assert failed['state'] == 'failed' and failed['complete'] is False
    assert generations.resume('a', failed['id'], provider) == failed['id']
    assert provider.calls == 3  # First document was not sent a second time.
    assert generations.inspect('a', failed['id'])['generations'][0]['complete']
    assert generations.active_plan('a')['generation_id'] is None


def test_retention_protects_head_previous_evaluation_and_retirement_grace(setup):
    store, generations, identity = setup
    publish(store)
    provider = MockEmbeddingProvider(1536)
    ids = [generations.build('a', identity, provider) for _ in range(4)]
    for version, identifier in enumerate(ids[:3]):
        generations.activate('a', identifier, expected_head=ids[version-1] if version else None, expected_version=version)
    with store.engine.begin() as connection:
        connection.execute(text("UPDATE rag_generations SET retired_at=clock_timestamp()-interval '20 minutes' WHERE id=:id"), {'id': ids[0]})
    first = generations.prune('a', keep=[ids[0]])
    assert first['removed_generations'] == [] and first['retired_generations'] == [ids[3]]
    assert generations.prune('a', keep=[ids[0]])['removed_generations'] == []
    with store.engine.begin() as connection:
        connection.execute(text("UPDATE rag_generations SET retired_at=clock_timestamp()-interval '20 minutes' WHERE id=:id"), {'id': ids[3]})
    assert generations.prune('a', keep=[ids[0]], limit=1)['removed_generations'] == [ids[3]]
    assert {item['id'] for item in generations.inspect('a')['generations']} == set(ids[:3])
    with store.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM embedding_cache')).scalar_one() == 1
    with pytest.raises(ValueError): generations.prune('a', grace_seconds=599)


def test_rollback_rebuild_uses_current_catalog_not_old_document_snapshot(setup):
    store, generations, identity = setup
    publish(store)
    provider = MockEmbeddingProvider(1536)
    first = generations.build('a', identity, provider)
    generations.activate('a', first, expected_head=None, expected_version=0)
    prepared = generations.prepare_publication('a', 'new', 'synthetic', 'New evidence.', ['New evidence.'], {}, provider)
    store.store_document(job_id='new', tenant_id='a', source='synthetic', artifact_uri=None, text_content='New evidence.',
        chunks=['New evidence.'], embeddings=prepared['plain_embeddings'], provider_name='mock', prepared_index=prepared)
    head = generations.active_plan('a')
    new = generations.rebuild_previous('a', provider, expected_head=head['generation_id'], expected_version=head['version'])
    assert new['generation_id'] not in {first, head['generation_id']}
    inspected = generations.inspect('a', new['generation_id'])['generations'][0]
    assert [item['id'] for item in inspected['manifest']['documents']] == ['doc', 'new']
    assert inspected['complete'] and inspected['catalog_revision'] == 2


def test_revoked_authority_after_vectorization_marks_failed_without_activation(setup):
    store, generations, identity = setup
    publish(store)
    calls = []
    def authorize():
        calls.append(True)
        if len(calls) == 3: raise PermissionError('synthetic revoked authority')
    with pytest.raises(PermissionError):
        generations.build('a', identity, MockEmbeddingProvider(1536), authorize=authorize)
    assert generations.inspect('a')['generations'][0]['state'] == 'failed'
    assert generations.active_plan('a')['generation_id'] is None


def test_two_real_concurrent_online_publications_keep_both_after_stale_reprepare(setup):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    store, generations, identity = setup
    publish(store)
    provider = MockEmbeddingProvider(1536)
    initial = generations.build('a', identity, provider)
    generations.activate('a', initial, expected_head=None, expected_version=0)
    prepared = {key: generations.prepare_publication('a', key, 'synthetic', key, [key], {}, provider) for key in ['new-a', 'new-b']}
    barrier = threading.Barrier(2)
    def save(key, value):
        return store.store_document(job_id=key, tenant_id='a', source='synthetic', artifact_uri=None, text_content=key,
            chunks=[key], embeddings=value['plain_embeddings'], provider_name='mock', prepared_index=value)
    def concurrent(key):
        barrier.wait(timeout=5)
        try:
            save(key, prepared[key])
            return None
        except StalePublication:
            return key
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(concurrent, prepared))
    assert results.count(None) == 1
    loser = next(key for key in results if key is not None)
    save(loser, generations.prepare_publication('a', loser, 'synthetic', loser, [loser], {}, provider))
    current = generations.inspect('a', generations.active_plan('a')['generation_id'])['generations'][0]
    assert current['complete'] and {item['id'] for item in current['manifest']['documents']} == {'doc', 'new-a', 'new-b'}


def test_verified_plan_cache_and_snapshot_honor_real_bounded_transport(setup, backend_query_store):
    import time
    import threading
    store, generations, identity = setup
    publish(store)
    provider = MockEmbeddingProvider(1536)
    candidate = generations.build('a', identity, provider)
    generations.activate('a', candidate, expected_head=None, expected_version=0)
    query = backend_query_store(store.database_url)
    try:
        assert query.ping()
        bounded = {'deadline': time.time() + 5, 'cancelled': threading.Event()}
        plan = query.resolve_retrieval_plan('a', enabled=True, **bounded)
        vector = query.embed_query('a', 'Bounded new question?', provider, plan, **bounded)
        assert len(query.search_chunks('a', vector, provider='mock', max_distance=2, plan=plan,
            question='Bounded new question?', **bounded)) == 1
        bounded['cancelled'].set()
        with pytest.raises(TimeoutError):
            query.resolve_retrieval_plan('a', enabled=True, **bounded)
    finally:
        query.close()


def test_operator_cli_build_inspect_activate_rechecks_existing_tenant_and_document_authority(setup, tmp_path):
    from types import SimpleNamespace
    from sqlalchemy import create_engine
    from app.reprocess_document import index_operation
    from app.core.config import Settings
    store, generations, identity = setup
    publish(store)
    engine = create_engine('sqlite://')
    try:
        with engine.begin() as connection:
            for statement in ['CREATE TABLE users(id TEXT PRIMARY KEY)',
                'CREATE TABLE user_tenants(user_id TEXT,tenant_id TEXT)',
                'CREATE TABLE jobs(id TEXT,tenant_id TEXT,created_by TEXT,status TEXT)',
                "INSERT INTO users VALUES ('operator'),('owner')",
                "INSERT INTO user_tenants VALUES ('operator','a'),('owner','a')",
                "INSERT INTO jobs VALUES ('doc','a','owner','completed')"]:
                connection.execute(text(statement))
        path = tmp_path / 'descriptor.json'
        path.write_text(__import__('json').dumps(identity.descriptor()), encoding='utf-8')
        args = SimpleNamespace(action='build', tenant_id='a', created_by='operator', resume_generation=None,
            space_file=str(path), retrieval_mode='dense', generation_id=None)
        settings = Settings(embedding_dimension=1536)
        database = SimpleNamespace(engine=engine)
        built = index_operation(args, settings, database, store)['generations'][0]
        assert built['complete'] and generations.active_plan('a')['generation_id'] is None
        args.action, args.generation_id = 'activate', built['id']
        args.expected_head, args.expected_version = 'legacy', 0
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM user_tenants WHERE user_id='owner'"))
        with pytest.raises(PermissionError): index_operation(args, settings, database, store)
        assert generations.active_plan('a')['generation_id'] is None
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO user_tenants VALUES ('owner','a')"))
        assert index_operation(args, settings, database, store)['generation_id'] == built['id']
        args.action = 'inspect'
        assert index_operation(args, settings, database, store)['generations'][0]['complete']
        args.created_by = 'foreign'
        with pytest.raises(PermissionError): index_operation(args, settings, database, store)
    finally:
        engine.dispose()


def test_concurrent_cache_misses_return_one_canonical_winner_and_do_not_cross_tenants(setup):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from app.embeddings.context import prepare_embedding
    store, generations, identity = setup
    prepared = [prepare_embedding({'content': 'Shared exact input.', 'metadata': {}}, {}, identity, generations.counter)]
    barrier = threading.Barrier(2)
    class Candidate(MockEmbeddingProvider):
        def __init__(self, axis): super().__init__(1536); self.axis = axis
        def embed_batch(self, values, **kwargs):
            barrier.wait(timeout=5)
            return [[float(index == self.axis) for index in range(1536)] for _ in values]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(generations.cache_embeddings, 'a', identity, prepared, Candidate(axis)) for axis in [0, 1]]
        results = [future.result(timeout=10) for future in futures]
    assert results[0] == results[1]
    with store.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM embedding_cache')).scalar_one() == 1
    foreign = generations.cache_embeddings('b', identity, prepared, MockEmbeddingProvider(1536))
    assert foreign != results[0]
    with store.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM embedding_cache')).scalar_one() == 2



@pytest.mark.parametrize('old_fails', [False, True])
@pytest.mark.parametrize('new_finishes_first', [False, True])
def test_superseded_build_cannot_finish_or_fail_new_execution(setup, backend_query_store, old_fails, new_finishes_first):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    store, generations, identity = setup
    publish(store)
    old_started, old_release = threading.Event(), threading.Event()
    new_started, new_release = threading.Event(), threading.Event()
    class Gated(MockEmbeddingProvider):
        def __init__(self, started, release, fails=False):
            super().__init__(1536)
            self.started, self.release, self.fails = started, release, fails
        def embed_batch(self, values, **kwargs):
            self.started.set()
            assert self.release.wait(8), 'Controlled provider was not released'
            if self.fails: raise RuntimeError('Original executor failed late')
            return super().embed_batch(values, **kwargs)
    def snapshot(identifier):
        with store.engine.connect() as connection:
            return dict(connection.execute(text('SELECT state,manifest,retired_at FROM rag_generations WHERE tenant_id=:tenant AND id=:id'),
                                           {'tenant':'a','id':identifier}).mappings().one())
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(generations.build, 'a', identity, Gated(old_started, old_release, old_fails))
        try:
            assert old_started.wait(5)
            with store.engine.connect() as connection:
                identifier = connection.execute(text("SELECT id FROM rag_generations WHERE state='building'")).scalar_one()
            old_token = snapshot(identifier)['manifest']['build_execution_id']
            second = pool.submit(generations.resume, 'a', identifier, Gated(new_started, new_release))
            assert new_started.wait(5)
            new_state = snapshot(identifier)
            assert new_state['manifest']['build_execution_id'] != old_token
            if new_finishes_first:
                new_release.set()
                assert second.result(timeout=8) == identifier
                generations.activate('a', identifier, expected_head=None, expected_version=0)
                new_state = snapshot(identifier)
            old_release.set()
            with pytest.raises(RuntimeError if old_fails else StaleGeneration):
                first.result(timeout=8)
            assert snapshot(identifier) == new_state
            if not new_finishes_first:
                new_release.set()
                assert second.result(timeout=8) == identifier
                generations.activate('a', identifier, expected_head=None, expected_version=0)
        finally:
            old_release.set()
            new_release.set()
    final = snapshot(identifier)
    assert final['state'] == 'ready' and 'build_execution_id' not in final['manifest']
    query = backend_query_store(store.database_url)
    try:
        plan = query.resolve_retrieval_plan('a', enabled=True)
        assert plan['generation_id'] == identifier
        assert query.search_chunks('a', MockEmbeddingProvider(1536).embed('Original evidence.'),
                                   provider='mock', plan=plan, question='Original evidence.', max_distance=2)
    finally:
        query.close()


@pytest.mark.parametrize('cold', [False, True])
def test_backend_query_cache_concurrency_keeps_canonical_sources_without_inference_retry(setup, backend_query_store, cold):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    import time
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    store, generations, identity = setup
    publish(store)
    candidate = generations.build('a', identity, MockEmbeddingProvider(1536))
    generations.activate('a', candidate, expected_head=None, expected_version=0)
    query = backend_query_store(store.database_url)
    providers = []
    provider_barrier, sql_barrier = threading.Barrier(2), threading.Barrier(2)
    class Controlled(MockEmbeddingProvider):
        def __init__(self, axis): super().__init__(1536); self.axis=axis; self.calls=[]
        def embed(self, question):
            self.calls.append(question)
            assert cold, 'A valid hit must not call inference'
            provider_barrier.wait(timeout=5)
            return [float(index == self.axis) for index in range(1536)]
    question = 'One exact concurrent query'
    try:
        assert query.ping()
        plan = query.resolve_retrieval_plan('a', enabled=True)
        if not cold:
            query.embed_query('a', question, MockEmbeddingProvider(1536), plan)
        def synchronize(connection, cursor, statement, parameters, context, executemany):
            prefix = 'INSERT INTO embedding_cache' if cold else 'UPDATE embedding_cache SET last_used_at'
            if statement.startswith(prefix):
                # Both insert transactions must have an established RR snapshot.
                if cold: connection.execute(text('SELECT txid_current_snapshot()'))
                if not getattr(context, '_bm0_synchronized', False):
                    context._bm0_synchronized=True
                    # Only the initial pair, never the fresh SQL retry.
                    with guard:
                        count[0]+=1
                        initial=count[0] <= 2
                    if initial: sql_barrier.wait(timeout=5)
        count, guard = [0], threading.Lock()
        event.listen(Engine, 'before_cursor_execute', synchronize)
        try:
            providers=[Controlled(0),Controlled(1)]
            def execute(provider):
                bounded={'deadline':time.time()+10, 'cancelled':threading.Event()}
                vector=query.embed_query('a', question, provider, plan, **bounded)
                sources=query.search_chunks('a', vector, provider='mock', plan=plan,
                                            question=question, max_distance=2, **bounded)
                return vector, sources
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(execute,providers))
        finally:
            event.remove(Engine,'before_cursor_execute',synchronize)
        assert results[0][0] == results[1][0]
        assert all(len(sources)==1 for _,sources in results)
        assert [len(provider.calls) for provider in providers] == ([1,1] if cold else [0,0])
        assert query.embed_query('a',question,providers[0],plan) == results[0][0]
        cancelled=threading.Event(); cancelled.set()
        with pytest.raises(TimeoutError):
            query.embed_query('a',question,providers[0],plan,deadline=time.time()+1,cancelled=cancelled)
    finally:
        query.close()


def test_query_cache_busy_touch_does_not_wait_for_row_lock(setup, backend_query_store):
    import threading, time
    store, generations, identity = setup
    publish(store)
    candidate=generations.build('a',identity,MockEmbeddingProvider(1536))
    generations.activate('a',candidate,expected_head=None,expected_version=0)
    query=backend_query_store(store.database_url)
    try:
        assert query.ping()
        plan=query.resolve_retrieval_plan('a',enabled=True)
        expected=query.embed_query('a','Busy touch',MockEmbeddingProvider(1536),plan)
        with store.engine.begin() as locked:
            locked.execute(text('UPDATE embedding_cache SET last_used_at=clock_timestamp()'))
            started=time.time()
            assert query.embed_query('a','Busy touch',MockEmbeddingProvider(1536),plan,
                                     deadline=started+1,cancelled=threading.Event()) == expected
            assert time.time()-started < 1
    finally:
        query.close()


@pytest.mark.parametrize('comparison', ['> -20%', '> +20%', '> 20e3%', '> .20%', '> 20..5%', '> 20,,5%'])
def test_unsupported_comparison_cannot_rescue_by_another_identifier(setup, backend_query_store, comparison):
    store,generations,identity=setup
    publish(store,content='JUP-125 utilization >= 200 USD')
    provider=MockEmbeddingProvider(1536)
    candidate=generations.build('a',identity,provider,retrieval_mode='hybrid')
    generations.activate('a',candidate,expected_head=None,expected_version=0)
    query=backend_query_store(store.database_url)
    try:
        plan=query.resolve_retrieval_plan('a',enabled=True,hybrid=True)
        opposite=[-value for value in provider.embed('JUP-125 utilization >= 200 USD')]
        assert query.search_chunks('a',opposite,provider='mock',plan=plan,max_distance=.2,
                                   question='JUP-125 utilization '+comparison) == []
        assert query.search_chunks('a',opposite,provider='mock',plan=plan,max_distance=.2,
                                   question='JUP-125 utilization >= 200 USD')
    finally:
        query.close()



@pytest.mark.parametrize('question,wrong', [
    ('JUP-125 cost > 20 EUR.', 'JUP-125 cost > 20 USD with EUR'),
    ('JUP-125 utilization >= 20 %.', 'JUP-125 utilization >= 20 USD'),
])
def test_terminal_unit_punctuation_never_rescues_wrong_unit_in_real_fts(setup, backend_query_store, question, wrong):
    store,generations,identity=setup
    publish(store,content=wrong)
    provider=MockEmbeddingProvider(1536)
    candidate=generations.build('a',identity,provider,retrieval_mode='hybrid')
    generations.activate('a',candidate,expected_head=None,expected_version=0)
    query=backend_query_store(store.database_url)
    try:
        plan=query.resolve_retrieval_plan('a',enabled=True,hybrid=True)
        opposite=[-value for value in provider.embed(wrong)]
        assert query.search_chunks('a',opposite,provider='mock',plan=plan,max_distance=.2,question=question)==[]
    finally:query.close()
