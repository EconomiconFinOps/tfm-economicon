"""New structured documents retain titles and locations in every retrieval path."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from app.services.citations import resolve_citations
from test_tenant_isolation_vector import retrieval

BODY = '# New evidence\n\nExact new normalized evidence.\n\n## Detail\n\nMore exact evidence.\n'
PROGRAM = '''
import json, sys
from app.documents.extractors import markdown
from app.embeddings.normalized import manual_document, parent_metadata
from app.embeddings.structural_chunker import StructuredChunker
body, kind = json.load(sys.stdin)
if kind == 'md':
    value, blocks, metadata, warnings, method = markdown(body.encode('utf-8'))
    document = {'schema_version': 1, 'document_id': 'new-' + kind, 'tenant_id': 'tenant-a', 'original_format': 'md',
                'text': value, 'blocks': blocks, 'file_metadata': metadata}
else:
    document = manual_document({'job_id': 'new-' + kind, 'tenant_id': 'tenant-a', 'source': 'guide.md', 'text_content': body})
result = StructuredChunker().chunk_document(document)
print(json.dumps({'document': document, 'result': result, 'parent': parent_metadata(document, result['manifest'])}))
'''
BUILD = '''
import importlib, os
from app.vector_store.generations import GenerationStore
from app.vector_store.pgvector_store import PgVectorStore
from app.embeddings.providers import MockEmbeddingProvider
from app.embeddings.space import EmbeddingSpace
from app.embeddings.tokenization import EmbeddingTokenCounter
store = PgVectorStore(os.environ['SYNTHETIC_VECTOR_URL'], 8)
try:
    with store.engine.begin() as connection:
        importlib.import_module('app.vector_store.migrations.004_embedding_generations').upgrade(connection)
    counter = EmbeddingTokenCounter()
    generations = GenerationStore(store.engine, counter)
    space = EmbeddingSpace('mock', 'mock/sha256_v1', 'a' * 64, counter.identity)
    identifier = generations.build('tenant-a', space, MockEmbeddingProvider(1536),
                                  retrieval_mode=os.environ['SYNTHETIC_RETRIEVAL_MODE'])
    generations.activate('tenant-a', identifier, expected_head=None, expected_version=0)
finally:
    store.close()
'''


def processor(program, *, value=None, environment=None):
    root = Path(__file__).resolve().parents[2] / 'processor'
    result = subprocess.run([sys.executable, '-B', '-c', program],
        input=json.dumps(value) if value is not None else None, capture_output=True,
        text=True, cwd=root, timeout=30,
        env={**os.environ, 'PYTHONPATH': str(root), 'PYTHONDONTWRITEBYTECODE': '1', **(environment or {})})
    assert result.returncode == 0, 'Synthetic processor preparation failed; private connection output is not exposed'
    return result.stdout


@pytest.mark.parametrize('mode', ['legacy', 'dense', 'hybrid'])
@pytest.mark.parametrize('kind', ['md', 'manual'])
def test_new_documents_keep_heading_title_section_and_provenance(retrieval, kind, mode):
    generated = json.loads(processor(PROGRAM, value=[BODY, kind]))
    now = datetime.now(timezone.utc)
    identifier = 'new-' + kind
    chunks = generated['result']['chunks']
    with retrieval.engine.begin() as connection:
        connection.execute(text('''INSERT INTO knowledge_documents
            (id,job_id,tenant_id,source,artifact_uri,text_content,chunk_count,created_at,updated_at,metadata)
            VALUES (:id,:id,'tenant-a','guide.md',NULL,:body,:count,:now,:now,CAST(:metadata AS jsonb))'''),
            {'id': identifier, 'body': generated['document']['text'], 'count': len(chunks),
             'now': now, 'metadata': json.dumps(generated['parent'])})
        for chunk in chunks:
            params = {'id': chunk['chunk_id'], 'doc': identifier, 'index': chunk['chunk_index'],
                'content': chunk['content'], 'count': len(chunk['content']),
                'metadata': json.dumps(chunk['metadata']), 'now': now}
            connection.execute(text('''INSERT INTO document_chunks
                (id,document_id,chunk_index,content,char_count,created_at,metadata)
                VALUES (:id,:doc,:index,:content,:count,:now,CAST(:metadata AS jsonb))'''), params)
            connection.execute(text('''INSERT INTO chunk_embeddings
                (id,chunk_id,embedding,dimension,provider,created_at)
                VALUES (:id,:id,'[1,0,0,0,0,0,0,0]'::vector,8,'mock',:now)'''), params)
    options, dimension = {}, 8
    if mode != 'legacy':
        processor(BUILD, environment={
            'SYNTHETIC_VECTOR_URL': retrieval.engine.url.render_as_string(hide_password=False),
            'SYNTHETIC_RETRIEVAL_MODE': mode})
        plan = retrieval.resolve_retrieval_plan('tenant-a', enabled=True, hybrid=mode == 'hybrid')
        options, dimension = {'plan': plan, 'question': 'Exact new normalized evidence'}, 1536
    records = retrieval.search_chunks('tenant-a', [1.] + [0.] * (dimension - 1),
        top_k=10, max_distance=2, provider='mock', **options)
    assert not any(item['tenant_id'] != 'tenant-a' or item['document_id'] == 'foreign' for item in records)
    records = [item for item in records if item['document_id'] == identifier]
    assert {item['chunk_id'] for item in records} == {item['chunk_id'] for item in chunks}
    citations = resolve_citations([item['chunk_id'] for item in records], records, 'tenant-a')
    assert {citation['title'] for citation in citations} == {'New evidence'}
    assert all(citation['section'] and (citation['section'].startswith('New evidence')
               or citation['section'] == 'Detail') for citation in citations)
    originals = {item['chunk_id']: item for item in chunks}
    for record, citation in zip(records, citations):
        original = originals[record['chunk_id']]
        assert record['content'] == original['content']
        assert record['chunk_metadata'] == original['metadata']
        assert citation['source'] == 'guide.md' and citation['page'] is None
        assert record['source_spans'] == original['metadata']['source_spans']
