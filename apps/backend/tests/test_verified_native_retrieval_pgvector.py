"""Public operation/current server retrieval with actual SQL and scripted generation."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from test_chat_context_assembly_jup035 import prepared, initialize
from test_chat_operations_jup035 import api, body, headers, path, run, messages, ANSWER
from test_tenant_isolation_vector import retrieval


@pytest.mark.parametrize('preparation,mode', [('plain_v1', 'dense'), ('plain_v1', 'hybrid'),
    ('contextual_embedding_v1', 'dense'), ('contextual_embedding_v1', 'hybrid')])
def test_native_operation_persists_verified_snapshot_and_citations_without_financial_authority(prepared, retrieval, monkeypatch, preparation, mode):
    from app.core.config import get_settings
    from app.services.embedding_provider import MockEmbeddingProvider
    application, database, processor, clock = prepared[0]
    # Build with the actual processor in a separate interpreter: both applications
    # deliberately own a top-level package named app. No module substitution.
    bootstrap = '''
import importlib,os
from app.vector_store.pgvector_store import PgVectorStore
from app.vector_store.generations import GenerationStore
from app.embeddings.space import EmbeddingSpace
from app.embeddings.providers import MockEmbeddingProvider
from app.embeddings.tokenization import EmbeddingTokenCounter
from app.embeddings.normalized import manual_document,parent_metadata
from app.embeddings.structural_chunker import StructuredChunker
store=PgVectorStore(os.environ['SYNTHETIC_VECTOR_URL'],8)
try:
    with store.engine.begin() as connection:
        importlib.import_module('app.vector_store.migrations.004_embedding_generations').upgrade(connection)
    document=manual_document({'job_id':'doc','tenant_id':'t','source':'synthetic','text_content':'# Scheduling\\n\\nReview before scheduling.'})
    document['file_metadata']['title']='Scheduling'
    chunks=StructuredChunker().chunk_document(document)
    store.store_document(job_id='doc',tenant_id='t',source='synthetic',artifact_uri=None,text_content=document['text'],chunks=chunks['chunks'],document_metadata=parent_metadata(document,chunks['manifest']),embeddings=[[1.]+[0.]*7 for _ in chunks['chunks']],provider_name='mock')
    counter=EmbeddingTokenCounter()
    generations=GenerationStore(store.engine,counter)
    space=EmbeddingSpace('mock','mock/sha256_v1','a'*64,counter.identity,preparation=os.environ['SYNTHETIC_PREPARATION'])
    candidate=generations.build('t',space,MockEmbeddingProvider(1536),retrieval_mode=os.environ['SYNTHETIC_RETRIEVAL_MODE'])
    generations.activate('t',candidate,expected_head=None,expected_version=0)
finally:
    store.close()
'''
    processor_root = Path(__file__).resolve().parents[2] / 'processor'
    environment = {**os.environ, 'PYTHONPATH': str(processor_root),
                   'SYNTHETIC_VECTOR_URL': retrieval.engine.url.render_as_string(hide_password=False),
                   'SYNTHETIC_PREPARATION': preparation, 'SYNTHETIC_RETRIEVAL_MODE': mode}
    process = subprocess.run([sys.executable, '-B', '-c', bootstrap], cwd='/tmp', env=environment,
                             capture_output=True, timeout=20)
    assert process.returncode == 0, 'Synthetic processor bootstrap failed; no credential-bearing subprocess output is exposed'
    assert retrieval.ping()
    monkeypatch.setenv('EMBEDDING_DIMENSION', '1536')
    monkeypatch.setenv('RAG_VERIFIED_ENABLED', 'true')
    monkeypatch.setenv('RAG_HYBRID_ENABLED', 'true' if mode == 'hybrid' else 'false')
    monkeypatch.setenv('RAG_CONTEXTUAL_ENABLED', 'true' if preparation == 'contextual_embedding_v1' else 'false')
    monkeypatch.setenv('RETRIEVAL_MAX_DISTANCE', '2')
    get_settings.cache_clear()
    monkeypatch.setattr(application.state, 'vector_store', retrieval, raising=False)
    monkeypatch.setattr(application.state, 'embedding_provider', MockEmbeddingProvider(1536), raising=False)
    original = processor.descriptor
    async def descriptor():
        return {**await original(), 'tool_protocol': 'server-documentation-v4'}
    monkeypatch.setattr(processor, 'descriptor', descriptor)
    recovered = []
    async def tool_result(claim, result):
        recovered.append(json.loads(result['content']))
    async def stream(claim):
        from app.core.chat_resources import retrieval_control
        yield {'type': 'tool_call', 'assistant': retrieval_control(claim['context'])}
        assert len(recovered[0]['evidence']) == 1 and recovered[0]['evidence'][0]['id'].startswith('doc:chunk:')
        candidate = copy.deepcopy(ANSWER)
        candidate.update(status='ok', answer='Review before scheduling.', limitations=[],
            evidence=[{key: recovered[0]['evidence'][0][key] for key in ['id', 'kind', 'title', 'source']}])
        yield {'type': 'candidate', 'result': candidate, 'finish_reason': 'stop', 'usage': None}
    monkeypatch.setattr(processor, 'tool_result', tool_result, raising=False)
    monkeypatch.setattr(processor, 'stream', stream)
    async def scenario(client):
        await initialize(application)
        response = await client.post(path(), json=body(content='Review before scheduling.'), headers=headers())
        assert response.status_code == 200 and 'event: final' in response.text
        assistant = next(item for item in messages(database) if item['role'] == 'assistant')
        metadata = assistant['metadata']
        chunk_id = recovered[0]['evidence'][0]['id']
        assert metadata['citations'] == [chunk_id]
        assert 'Review before scheduling.' in metadata['source_citations'][0]['excerpt']
        assert metadata['response']['metrics'] == []
        diagnostic = metadata['generation']['context_manifest']['retrieval'][0]
        assert diagnostic['chunk_id'] == chunk_id and diagnostic['mode'] == mode
        assert len(diagnostic['space_id']) == 64 and 0 <= diagnostic['distance'] <= 2
        assert 'foreign-secret-marker' not in json.dumps(recovered) + json.dumps(metadata, default=str)
        if os.environ.get('RAG_TEST_CAPTURE_DIR'):
            capture = json.loads((Path(os.environ['RAG_TEST_CAPTURE_DIR'])/'alice-chat.json').read_text())
            assert capture['operation_id'] == metadata['generation']['operation_id']
            assert capture['attempt_id'] == metadata['generation']['attempt_id']
            assert [item['chunk_id'] for item in capture['retrieved']] == [chunk_id]
            assert capture['retrieved'][0]['content'] == recovered[0]['evidence'][0]['content']
    try:
        run(scenario, prepared[0])
    finally:
        get_settings.cache_clear()
