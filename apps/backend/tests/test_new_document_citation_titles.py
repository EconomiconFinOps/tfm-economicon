"""New-generation documents keep the title and section that older documents showed in citations."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from app.services.citations import resolve_citations
from test_tenant_isolation_vector import retrieval  # noqa: F401  (disposable real pgvector fixture)

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


def generate(kind):
    processor = Path(__file__).resolve().parents[2] / 'processor'
    run = subprocess.run([sys.executable, '-B', '-c', PROGRAM], input=json.dumps([BODY, kind]), capture_output=True,
                         text=True, check=True, cwd=processor,
                         env={**os.environ, 'PYTHONPATH': str(processor), 'PYTHONDONTWRITEBYTECODE': '1'})
    return json.loads(run.stdout)


@pytest.mark.parametrize('kind', ['md', 'manual'])
def test_new_documents_show_the_heading_title_and_section_like_legacy_ones(retrieval, kind):  # noqa: F811
    generated = generate(kind)
    now = datetime.now(timezone.utc)
    identifier = 'new-' + kind
    with retrieval.engine.begin() as connection:
        connection.execute(text('''INSERT INTO knowledge_documents
            (id,job_id,tenant_id,source,artifact_uri,text_content,chunk_count,created_at,updated_at,metadata)
            VALUES (:id,:id,'tenant-a','guide.md',NULL,:body,:count,:now,:now,CAST(:metadata AS jsonb))'''),
            {'id': identifier, 'body': generated['document']['text'], 'count': len(generated['result']['chunks']),
             'now': now, 'metadata': json.dumps(generated['parent'])})
        for chunk in generated['result']['chunks']:
            params = {'id': chunk['chunk_id'], 'doc': identifier, 'index': chunk['chunk_index'], 'content': chunk['content'],
                      'count': len(chunk['content']), 'metadata': json.dumps(chunk['metadata']), 'now': now}
            connection.execute(text('''INSERT INTO document_chunks
                (id,document_id,chunk_index,content,char_count,created_at,metadata)
                VALUES (:id,:doc,:index,:content,:count,:now,CAST(:metadata AS jsonb))'''), params)
            connection.execute(text('''INSERT INTO chunk_embeddings
                (id,chunk_id,embedding,dimension,provider,created_at)
                VALUES (:id,:id,'[1,0,0,0,0,0,0,0]'::vector,8,'mock',:now)'''), params)
    records = [item for item in retrieval.search_chunks('tenant-a', [1.0] + [0.0] * 7, top_k=10, provider='mock')
               if item['document_id'] == identifier]
    assert records
    citations = resolve_citations([item['chunk_id'] for item in records], records, 'tenant-a')
    assert {citation['title'] for citation in citations} == {'New evidence'}
    assert all(citation['section'] and citation['section'].startswith('New evidence') or citation['section'] == 'Detail' for citation in citations)
