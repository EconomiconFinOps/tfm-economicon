"""Neighbors and complete policies must use only the captured verified generation."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

import pytest
from sqlalchemy import text

from app.core.chat_expressions import context_quantities
from app.core.chat_policy_sections import complete_sections, required_policy
from app.services.citations import DocumentCitations
from test_new_document_citation_titles import BUILD, processor
from test_tenant_isolation_vector import retrieval  # noqa: F401


def save(store, document, body, *, tenant='tenant-a', provider='mock', chunks=None, canonical=False):
    chunks = chunks or [body if canonical else DocumentCitations(body).normalized]
    now = datetime.now(timezone.utc)
    with store.engine.begin() as connection:
        connection.execute(text("""INSERT INTO knowledge_documents
            (id,job_id,tenant_id,source,text_content,chunk_count,created_at,updated_at,metadata)
            VALUES (:id,:id,:tenant,'guide.md',:body,:count,:now,:now,CAST(:metadata AS jsonb))"""),
            {'id': document, 'tenant': tenant, 'body': body, 'count': len(chunks), 'now': now,
             'metadata': json.dumps({'chunking': {'version': 1}} if canonical else {})})
        for index, content in enumerate(chunks):
            values = {'id': f'{document}:chunk:{index}', 'document': document, 'index': index,
                      'content': content, 'length': len(content), 'now': now, 'provider': provider}
            connection.execute(text("""INSERT INTO document_chunks
                (id,document_id,chunk_index,content,char_count,created_at)
                VALUES (:id,:document,:index,:content,:length,:now)"""), values)
            connection.execute(text("""INSERT INTO chunk_embeddings
                (id,chunk_id,embedding,dimension,provider,created_at)
                VALUES (:id,:id,'[0,1,0,0,0,0,0,0]'::vector,8,:provider,:now)"""), values)


def generation(store, mode):
    program = BUILD.replace('store = PgVectorStore', """class Fixed(MockEmbeddingProvider):
    def __init__(self):
        super().__init__(1536)
    def embed_batch(self, texts, **kwargs):
        return [[1., 0.] + [0.] * 1534 if value.startswith(('SEED', 'Close '))
                else [0., 1.] + [0.] * 1534 for value in texts]
store = PgVectorStore""").replace('MockEmbeddingProvider(1536)', 'Fixed()')
    processor(program, environment={
        'SYNTHETIC_VECTOR_URL': store.engine.url.render_as_string(hide_password=False),
        'SYNTHETIC_RETRIEVAL_MODE': mode})
    return store.resolve_retrieval_plan('tenant-a', enabled=True, hybrid=mode == 'hybrid')


def search(store, plan, **options):
    return store.search_chunks('tenant-a', [1., 0.] + [0.] * 1534, top_k=20,
        max_distance=.01, provider='mock', plan=plan, question='evidence', **options)


@pytest.mark.parametrize('mode', ['dense', 'hybrid'])
def test_verified_neighbor_outside_dense_pool_retains_snapshot(retrieval, mode):
    save(retrieval, 'a-seed', 'SEED evidence\nNeighbor evidence\nNonrecursive evidence',
         chunks=['SEED evidence', 'Neighbor evidence', 'Nonrecursive evidence'])
    for index in range(21):
        save(retrieval, f'close-{index:02}', f'Close evidence {index}')
    save(retrieval, 'foreign-neighbor', 'Foreign marker', tenant='tenant-b')
    plan = generation(retrieval, mode)
    with retrieval.engine.begin() as connection:
        connection.execute(text("UPDATE document_chunks SET content='MUTABLE LEGACY' WHERE document_id='a-seed'"))
    rows = search(retrieval, plan, neighbor_seed_count=1)
    assert len(rows) == 20
    assert rows[0]['chunk_id'] == 'a-seed:chunk:0'
    assert rows[1]['chunk_id'] == 'a-seed:chunk:1' and rows[1]['distance'] > .01
    assert rows[1]['content'] == 'Neighbor evidence'
    assert 'a-seed:chunk:2' not in {row['chunk_id'] for row in rows}
    assert all(row['tenant_id'] == 'tenant-a' for row in rows)


POLICY = '# Guide\r\n\r\n## Reglas De Tagging\r\nPolicy  content.\r\n## Next\r\nEnd.'


@pytest.mark.parametrize('mode', ['dense', 'hybrid'])
@pytest.mark.parametrize('canonical', [False, True])
@pytest.mark.parametrize('bounded', [False, True])
def test_verified_complete_policy_outside_threshold_uses_revision_and_coordinate_domain(retrieval, mode, canonical, bounded):
    save(retrieval, 'policy', POLICY, canonical=canonical)
    save(retrieval, 'foreign-policy', POLICY, tenant='tenant-b')
    plan = generation(retrieval, mode)
    # Legacy provider labels do not define verified membership: only the captured
    # generation/space does. This later publication must stay outside that plan.
    save(retrieval, 'inactive-policy', POLICY, provider='inactive')
    with retrieval.engine.begin() as connection:
        connection.execute(text("UPDATE knowledge_documents SET text_content='MUTABLE LEGACY' WHERE id='policy'"))
        connection.execute(text("UPDATE document_chunks SET content='MUTABLE LEGACY' WHERE document_id='policy'"))
    bounds = {'deadline': time.time() + 10, 'cancelled': Event()} if bounded else {}
    rows = search(retrieval, plan, policy_section='Reglas De Tagging', **bounds)
    assert len(rows) == 1 and rows[0]['document_id'] == 'policy' and rows[0]['policy_priority']
    assert rows[0]['content'] == (POLICY if canonical else DocumentCitations(POLICY).normalized)
    source = {'id': rows[0]['chunk_id'], 'kind': 'corpus', 'content': rows[0]['content'],
              'provenance': {'document_id': 'policy', 'chunk_index': 0, 'sections': rows[0]['section_spans']}}
    [section] = complete_sections([source], 'Reglas De Tagging')
    assert 'Policy' in section['body'] and 'MUTABLE LEGACY' not in section['body']
    expected = POLICY if canonical else DocumentCitations(POLICY).normalized
    assert section['section_start'] == expected.index('## Reglas De Tagging')


@pytest.mark.parametrize('reason', ['ambiguous', 'oversize', 'fragments', 'repeated'])
def test_verified_policy_preserves_ambiguity_byte_fragment_and_literal_guards(retrieval, reason):
    body = POLICY
    chunks = None
    if reason == 'oversize':
        body += '\n' + '\u00e1' * 40000
        value = DocumentCitations(body).normalized
        chunks = [value[index:index + 400] for index in range(0, len(value), 400)]
    elif reason == 'fragments':
        body = '# Guide\n## Reglas De Tagging\n' + ''.join(f'Clause {i}; ' for i in range(20)) + '\n## Next\nEnd.'
        value = DocumentCitations(body).normalized
        chunks = [value[index:index + 50] for index in range(0, len(value), 20)]
    elif reason == 'repeated':
        body = POLICY + '\n' + POLICY
    save(retrieval, 'policy', body, chunks=chunks)
    if reason == 'ambiguous':
        save(retrieval, 'second-policy', body)
    plan = generation(retrieval, 'dense')
    assert search(retrieval, plan, policy_section='Reglas De Tagging') == []


@pytest.mark.parametrize('mode', ['dense', 'hybrid'])
@pytest.mark.parametrize('canonical', [False, True])
def test_verified_budget_policy_keeps_companion_definition(retrieval, mode, canonical):
    corpus = Path(__file__).resolve().parents[3] / 'docs/assistant-corpus'
    for document, relative in [('rules', 'business-rules/economicon-mvp-rules.md'),
                               ('finops', 'finops/azure-finops-mvp.md')]:
        body = (corpus / relative).read_text(encoding='utf-8')
        value = body if canonical else DocumentCitations(body).normalized
        chunks = [value[index:index + 500].strip() for index in range(0, len(value), 450)]
        save(retrieval, document, body, chunks=chunks, canonical=canonical)
    plan = generation(retrieval, mode)
    rows = search(retrieval, plan, policy_section='Budgets Y Forecast')
    assert {row['document_id'] for row in rows} == {'rules', 'finops'}
    assert all(row['policy_priority'] for row in rows) and len(rows) <= 12
    sources = [{'id': row['chunk_id'], 'kind': 'corpus', 'title': row['title'],
                'source': row['source'], 'content': row['content'],
                'provenance': {'document_id': row['document_id'], 'chunk_index': row['chunk_index'],
                               'sections': row['section_spans']}} for row in rows]
    catalog = context_quantities({'authorized_evidence': sources, 'messages': [
        {'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': 'Un presupuesto apaga recursos?'})},
        {'content': 'UNTRUSTED_RETRIEVAL_CONTEXT\n' + json.dumps({'evidence': sources})}]})
    policy = required_policy(catalog)
    assert policy is not None and 'investigacion, no apagado automatico' in policy['text']


@pytest.mark.parametrize('canonical', [False, True])
@pytest.mark.parametrize('count', [64, 65])
def test_verified_citations_preserve_section_span_cap(retrieval, canonical, count):
    body = ''.join(f'## Section {index}\nValue {index}.\n' for index in range(count))
    save(retrieval, 'sections', body, canonical=canonical)
    plan = generation(retrieval, 'dense')
    rows = retrieval.search_chunks('tenant-a', [1., 0.] + [0.] * 1534, top_k=20,
        max_distance=2, provider='mock', plan=plan, question='Section')
    [record] = [row for row in rows if row['document_id'] == 'sections']
    assert len(record['section_spans']) == (64 if count == 64 else 0)
