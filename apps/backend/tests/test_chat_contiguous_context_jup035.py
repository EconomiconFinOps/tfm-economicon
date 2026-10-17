"""Synthetic split rules; no benchmark questions or expected financial answers."""
from types import SimpleNamespace

from app.services.chat_context import ChatContext


def chunk(index, document='manual', tenant='t', content='Synthetic context'):
    return {'chunk_id': f'{document}:{index}', 'document_id': document,
        'tenant_id': tenant, 'chunk_index': index, 'title': 'Synthetic manual',
        'source': 'synthetic', 'content': content, 'distance': .2}


def context(monkeypatch, candidates, top_k=1):
    from app.core import config
    monkeypatch.setattr(config, 'get_settings', lambda: SimpleNamespace(
        retrieval_top_k=top_k, retrieval_max_distance=.4))
    calls = []
    def search(tenant, vector, **options):
        calls.append((tenant, vector, options))
        return candidates
    application = SimpleNamespace(state=SimpleNamespace(
        embedding_provider=SimpleNamespace(name='synthetic-provider', embed=lambda question: [1.0]),
        vector_store=SimpleNamespace(search_chunks=search)))
    return ChatContext(application, None), calls


def test_split_rule_uses_real_immediate_neighbors_and_original_citations(monkeypatch):
    candidates = [chunk(4, content='Dispatch rule: use channel'),
        chunk(8), chunk(5, content=' amber for delayed delivery.'), chunk(3)]
    service, calls = context(monkeypatch, candidates)
    evidence, citations, _ = service.retrieve({'tenant_id': 't'}, 'Explain dispatch rules')
    assert [item['id'] for item in evidence] == ['manual:4', 'manual:5', 'manual:3']
    assert evidence[0]['content'] == candidates[0]['content']
    assert evidence[1]['content'] == candidates[2]['content']
    assert [item['evidence_id'] for item in citations] == [item['id'] for item in evidence]
    assert citations[1]['reference'] == 'document:manual/chunk:5'
    assert calls == [('t', [1.0], {'top_k': 20, 'max_distance': .4, 'provider': 'synthetic-provider'})]


def test_primary_order_dedup_and_document_boundary(monkeypatch):
    candidates = [chunk(4), chunk(5), chunk(3, document='other'), chunk(6), chunk(3)]
    service, _ = context(monkeypatch, candidates, top_k=2)
    evidence, _, _ = service.retrieve({'tenant_id': 't'}, 'Synthetic')
    assert [item['id'] for item in evidence] == ['manual:4', 'manual:5', 'manual:3', 'manual:6']


def test_financial_evidence_capacity_bounds_neighbors_with_explicit_omission(monkeypatch):
    service, _ = context(monkeypatch, [chunk(4), chunk(3), chunk(5)])
    evidence, _, omission = service.retrieve({'tenant_id': 't'}, 'Synthetic', evidence_limit=2)
    assert [item['id'] for item in evidence] == ['manual:4', 'manual:3']
    assert omission['reason'] == 'contiguous_context_bounded'
    assert omission['omitted_neighbors'] == 1 and omission['candidate_limit'] == 20


def test_foreign_tenant_candidates_fail_closed_without_unsafe_fallback(monkeypatch):
    service, calls = context(monkeypatch, [chunk(4), chunk(5, tenant='foreign')])
    evidence, citations, omission = service.retrieve({'tenant_id': 't'}, 'Synthetic')
    assert not evidence and not citations
    assert omission['reason'] == 'retrieval_unavailable' and len(calls) == 1


def test_missing_neighbor_is_not_fabricated(monkeypatch):
    service, _ = context(monkeypatch, [chunk(4), chunk(9)])
    evidence, _, omission = service.retrieve({'tenant_id': 't'}, 'Synthetic')
    assert [item['id'] for item in evidence] == ['manual:4']
    assert omission['reason'] == 'contiguous_context_bounded'
    assert omission['candidate_limit'] == 20 and omission['omitted_neighbors'] == 0
