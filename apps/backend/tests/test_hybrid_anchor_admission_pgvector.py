"""Regression of hybrid anchor admission using actual generation/SQL retrieval."""
import pytest
from sqlalchemy import text

from app.services.retrieval_policy import anchors_match, query_policy
from test_tenant_isolation_vector import retrieval  # noqa: F401
from test_verified_retrieval_expansion_pgvector import generation, save


@pytest.mark.parametrize('body,question', [
    ('Close El grupo rg-prod-01 cuesta 20 EUR', '\u00bfQu\u00e9 cuesta RG-PROD-01?'),
    ('Close El grupo RG-PROD-01 cuesta 20 EUR', '\u00bfQu\u00e9 cuesta RG-PROD-01?'),
    ('Close Compa\u00f1\u00eda factura', '"Compan\u0303i\u0301a" factura'),
    ('Close El gasto mensual de ahorro es estable', '\u00bfCu\u00e1nto gasto y/o ahorro hay?'),
    ('Close El gasto del 17/10/2024 fue alto', 'gasto del 2024-10-17'),
])
def test_hybrid_keeps_dense_hit_despite_case_unicode_or_incidental_anchors(retrieval, body, question):
    save(retrieval, 'target', body)
    save(retrieval, 'foreign-target', body, tenant='tenant-b')
    plan = generation(retrieval, 'hybrid')
    rows = retrieval.search_chunks('tenant-a', [1., 0.] + [0.] * 1534,
        top_k=20, max_distance=.6, provider='mock', plan=plan, question=question)
    assert [row['document_id'] for row in rows] == ['target']
    assert rows[0]['distance'] == 0 and rows[0]['retrieval']['dense_rank'] == 1
    assert rows[0]['retrieval']['generation_id'] == plan['generation_id']


def test_hybrid_dense_boundary_is_inclusive_without_lexical_anchor_match(retrieval):
    save(retrieval, 'target', 'Close El gasto mensual de ahorro es estable')
    plan = generation(retrieval, 'hybrid')
    # Integer coordinates give cosine .4 exactly: norm(2,4,2,1) == 5.
    # This directly checks the .6 threshold, not a threshold adapted to output.
    boundary = '[2,4,2,1,' + ','.join(['0'] * 1532) + ']'
    with retrieval.engine.begin() as connection:
        connection.execute(text('''UPDATE embedding_cache e SET embedding=CAST(:vector AS vector)
            WHERE e.tenant_id='tenant-a' AND e.space_id=:space AND EXISTS (
                SELECT 1 FROM rag_chunk_vectors v JOIN rag_generation_members m
                ON m.tenant_id=v.tenant_id AND m.revision_id=v.revision_id
                WHERE v.tenant_id=e.tenant_id AND v.space_id=e.space_id AND v.text_hash=e.text_hash
                    AND m.generation_id=:generation AND m.document_id='target')'''),
            {'vector': boundary, 'space': plan['space_id'], 'generation': plan['generation_id']})
    options = dict(top_k=20, provider='mock', plan=plan, question='gasto y/o ahorro')
    rows = retrieval.search_chunks('tenant-a', [1., 0.] + [0.] * 1534, max_distance=.6, **options)
    assert [row['document_id'] for row in rows] == ['target']
    assert rows[0]['distance'] == .6 and rows[0]['retrieval']['dense_rank'] == 1
    assert retrieval.search_chunks('tenant-a', [1., 0.] + [0.] * 1534,
        max_distance=.599999, **options) == []


@pytest.mark.parametrize('question', ['JUP-125 cost > -20 EUR', 'JUP-125 versus JUP-124 cost'])
def test_unrelated_identifier_cannot_rescue_unsupported_comparison(retrieval, question):
    save(retrieval, 'target', 'JUP-125 JUP-124 cost > -20 EUR versus cost')
    plan = generation(retrieval, 'hybrid')
    assert not query_policy(question)['rescue']
    assert retrieval.search_chunks('tenant-a', [1., 0.] + [0.] * 1534,
        top_k=20, max_distance=.6, provider='mock', plan=plan, question=question) == []


def test_unicode_and_case_anchors_still_control_lexical_rescue(retrieval):
    save(retrieval, 'target', 'rg-prod-01 storage')
    save(retrieval, 'wrong-id', 'rg-prod-010 storage')
    save(retrieval, 'foreign-target', 'rg-prod-01 storage', tenant='tenant-b')
    plan = generation(retrieval, 'hybrid')
    rows = retrieval.search_chunks('tenant-a', [1., 0.] + [0.] * 1534,
        top_k=20, max_distance=.6, provider='mock', plan=plan, question='RG-PROD-01 storage')
    assert [row['document_id'] for row in rows] == ['target']
    assert rows[0]['retrieval']['dense_rank'] is None and rows[0]['retrieval']['lexical_rank'] == 1
    assert anchors_match(rows[0]['content'], query_policy('RG-PROD-01 storage'))
