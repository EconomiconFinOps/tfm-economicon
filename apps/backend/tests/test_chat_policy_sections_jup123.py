"""Real corpus spans, independent backend schema and public firewall."""
import copy
import json
from pathlib import Path

import pytest

from app.core.chat_expressions import context_quantities
from app.core.chat_policy_sections import required_policy
from app.core.chat_segments import render_response
from app.schemas.chat import provider_response_schema, validate_response
from app.services.citations import DocumentCitations


def actual_catalog(question):
    root = Path(__file__).resolve().parents[3]
    document = DocumentCitations((root/'docs/assistant-corpus/business-rules/economicon-mvp-rules.md').read_text(encoding='utf-8'))
    sources = []
    for index, left in enumerate(range(0, len(document.normalized), 450)):
        content = document.normalized[left:left+500]
        sources.append({'id': f'rules:{index}', 'kind': 'corpus', 'source': 'rules',
                        'title': document.title, 'content': content,
                        'provenance': {'document_id': 'rules', 'chunk_index': index,
                                       'sections': document.section_spans(content)}})
    return context_quantities({'authorized_evidence': sources, 'messages': [
        {'content': 'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question': question})},
        {'content': 'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence': sources})}]})


@pytest.mark.parametrize('question,expected', [
    ('Enumera las reglas de tagging.', ('costcenter', 'businessunit', 'minusculas', 'PII', 'preferentemente')),
    ('¿Un presupuesto apaga las máquinas?', ('investigacion, no apagado automatico', 'prediccion', 'forecast y budget')),
])
def test_complete_corpus_policy_preserves_rules_in_backend_public_validation(question, expected):
    q = actual_catalog(question)
    bound = required_policy(q)
    assert bound is not None
    answer = {'policy_section': bound['id']}
    schema = provider_response_schema(authorized_evidence=q.authorized_sources, quantities=q)
    assert schema['properties']['answer'] == {'const': answer}
    value = {'schema_version': '1.0', 'status': 'ok', 'answer': answer,
             'scope': {'cloud': 'azure', 'data_environment': 'simulated', 'period': None, 'subscription_ids': []},
             'evidence': [], 'metrics': [], 'recommendations': [], 'assumptions': [], 'limitations': [], 'next_actions': []}
    rendered = render_response(value, [], quantities=q)
    public = json.loads(json.dumps(rendered))
    assert validate_response(public, q.authorized_sources, expected_period=None, expected_subscriptions=[]) == public
    assert all(part in public['answer'] for part in expected)
    tampered = copy.deepcopy(public)
    tampered['evidence'][0]['id'] = 'another-tenant:policy'
    with pytest.raises(ValueError): validate_response(tampered, q.authorized_sources)
