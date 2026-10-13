import copy

import pytest

from test_chat_operations_jup035 import ANSWER, api, body, headers, path, run


def test_subscription_scope_comes_only_from_canonical_selection():
    from app.services.chat_context import response_subscriptions
    assert response_subscriptions({'selection': {}, 'datasets': []}) == []
    screen = {'identity': {'tenant_id': 'not-a-subscription'},
        'selection': {'filters': {'subscriptions': [' subscription-b ', ' subscription-a ', 'subscription-a']}},
        'datasets': [{'selection': {'filters': {'subscriptions': ['not-selected']}}}]}
    assert response_subscriptions(screen) == ['subscription-a', 'subscription-b']
    from app.schemas.chat import validate_response
    normalized_response = copy.deepcopy(ANSWER)
    normalized_response['scope']['subscription_ids'] = ['subscription-a', 'subscription-b']
    assert validate_response(normalized_response, [],
        expected_subscriptions=response_subscriptions(screen)) == normalized_response
    from app.db.chat_repository import ChatError
    with pytest.raises(ChatError) as caught:
        response_subscriptions({'selection': {'filters': {'subscriptions': ['s' + str(n) for n in range(21)]}}})
    assert caught.value.status == 422 and caught.value.code == 'subscription_scope_limit'
    assert len(response_subscriptions({'selection': {'filters': {'subscriptions': ['s' + str(n) for n in range(20)] + [' s0 ']}}})) == 20
    assert response_subscriptions({'selection': {'filters': {'subscriptions': ['x', 'y' * 256]}}}) == ['x', 'y' * 256]
    for invalid in ['', '   ', 'x' * 257]:
        with pytest.raises(ChatError) as caught:
            response_subscriptions({'selection': {'filters': {'subscriptions': [invalid]}}})
        assert caught.value.status == 422


@pytest.mark.parametrize('subscriptions', [['s' + str(n) for n in range(21)], ['   ']])
def test_unrepresentable_scope_is_422_before_provider_claim(api, monkeypatch, subscriptions):
    from app.services.chat_context import response_subscriptions
    original = api[0].state.chat_context_builder
    async def builder(scope, payload, descriptor):
        selected = response_subscriptions(payload['screen_context'])
        context = await original(scope, payload, descriptor)
        context['response_subscriptions'] = selected
        return context
    monkeypatch.setattr(api[0].state, 'chat_context_builder', builder)
    async def scenario(client):
        payload = body()
        payload['screen_context']['selection'] = {'filters': {'subscriptions': subscriptions}}
        response = await client.post(path(), json=payload, headers=headers())
        assert response.status_code == 422
        assert not api[2].claims
    run(scenario, api)


def test_backend_validates_subscription_scope_without_changing_public_schema():
    from app.schemas.chat import provider_response_schema, response_schema, validate_response
    assert 'subscription_ids' not in provider_response_schema()['$defs']['ResponseScope']['properties']
    assert 'subscription_ids' in response_schema()[0]['$defs']['ResponseScope']['required']
    assert all(b['properties']['metrics']['maxItems']==0 for b in provider_response_schema()['anyOf'])
    allowed_branches = provider_response_schema(financial_metrics_allowed=True)['anyOf']
    assert any(b['properties']['answer'].get('type') == 'array' for b in allowed_branches)
    for branch in allowed_branches:
        narrative = branch['properties']['answer'].get('type') == 'array'
        assert branch['properties']['metrics']['maxItems'] == (20 if narrative else 0)
    assert response_schema()[0]['properties']['metrics']['maxItems'] == 20
    from app.schemas.chat import _validate
    metric = {'name': 'total_cost', 'value': '0.00', 'unit': 'EUR', 'evidence_ids': ['cost:verified']}
    restricted = provider_response_schema()
    for branch in restricted['anyOf']:
        with pytest.raises(ValueError):
            _validate([metric], branch['properties']['metrics'], restricted)
        _validate([], branch['properties']['metrics'], restricted)
    allowed = provider_response_schema(financial_metrics_allowed=True)
    for branch in allowed['anyOf']:
        if branch['properties']['answer'].get('type') == 'array':
            _validate([metric], branch['properties']['metrics'], allowed)
        else:
            with pytest.raises(ValueError):
                _validate([metric], branch['properties']['metrics'], allowed)
        _validate([], branch['properties']['metrics'], allowed)
    response = copy.deepcopy(ANSWER)
    assert validate_response(response, [], expected_subscriptions=[]) == response
    response['scope']['subscription_ids'] = ['tenant-core']
    with pytest.raises(ValueError) as caught:
        validate_response(response, [], expected_subscriptions=[])
    assert caught.value.rule_code == 'subscription_context'


@pytest.mark.parametrize('financial_allowed', [False, True])
def test_private_schema_requires_actionable_evidence_and_preserves_base(financial_allowed):
    import importlib.util
    import json
    from pathlib import Path
    import sys
    from app.schemas.chat import _validate, provider_response_schema, response_schema
    schema = provider_response_schema(financial_metrics_allowed=financial_allowed)
    candidate = copy.deepcopy(ANSWER)
    candidate['scope'].pop('period')
    candidate['scope'].pop('subscription_ids')
    candidate['answer']=[{'text':candidate['answer']}]
    for field in ('assumptions','limitations','next_actions'):
        candidate[field]=[[{'text':item}] for item in candidate[field]]
    for status in ('ok', 'partial', 'no_data', 'insufficient_data', 'unsupported', 'refused', 'error'):
        candidate['status'] = status
        with pytest.raises(ValueError):
            _validate(candidate, schema, schema)
        candidate['evidence'] = [{'id': 'manual:synthetic', 'kind': 'corpus',
            'title': 'Synthetic manual', 'source': 'synthetic'}]
        _validate(candidate, schema, schema)
        candidate['evidence'] = []
    neutral = copy.deepcopy(candidate)
    neutral.pop('status')
    neutral['answer'] = {'request': {'reason': 'clarification'}}
    for field in ('metrics', 'recommendations', 'evidence', 'assumptions', 'limitations', 'next_actions'):
        neutral[field] = []
    _validate(neutral, schema, schema)
    # Complete branches preserve all constraints without duplicate root
    # intersections. References remain rooted in the original $defs.
    narratives = [branch for branch in schema['anyOf'] if branch['properties']['answer'].get('type') == 'array']
    requests = [branch for branch in schema['anyOf'] if 'request' in branch['properties']['answer'].get('properties', {})]
    assert len(narratives) == 2 and len(requests) == 1
    assert len(schema['anyOf']) == len(narratives) + len(requests)
    assert 'properties' not in schema and 'required' not in schema
    public,_=response_schema()
    for branch in schema['anyOf']:
        narrative = branch in narratives
        expected_required = public['required'] if narrative else [key for key in public['required'] if key != 'status']
        assert branch['required'] == expected_required
        assert branch['additionalProperties'] is False
        assert branch['properties']['metrics']['maxItems'] == (20 if financial_allowed and narrative else 0)
        valid = copy.deepcopy(candidate if narrative else neutral)
        if narrative:
            valid['status'] = branch['properties']['status']['enum'][0]
            valid['evidence'] = [{'id': 'manual:synthetic', 'kind': 'corpus',
                'title': 'Synthetic manual', 'source': 'synthetic'}]
        _validate(valid, branch, schema)
        invalid = copy.deepcopy(valid)
        invalid['extra'] = 'not allowed'
        with pytest.raises(ValueError):
            _validate(invalid, {'$defs': schema['$defs'], 'anyOf': [branch]}, schema)
    path = Path(__file__).resolve().parents[2] / 'processor/app/agents/schemas.py'
    spec = importlib.util.spec_from_file_location('processor_schema_parity', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        assert schema == module.chat_provider_schema(financial_metrics_allowed=financial_allowed)
    finally:
        sys.modules.pop(spec.name, None)
    assert response_schema()[1] == 'baf067ac8fe35a693848012c5358cb1c6ab8883ebaa02a63166b00f7d8298018'
    json.dumps(schema, allow_nan=False)


def test_chat_output_budget_is_separate_from_ingestion(monkeypatch):
    from app.core.context_budget import budget
    assert budget('chat')['output_tokens'] == 3200
    monkeypatch.setenv('CHAT_MAX_OUTPUT_TOKENS', '1600')
    assert budget('chat')['output_tokens'] == 1600
    for value in ['0', '3201', '-1', '1.5']:
        monkeypatch.setenv('CHAT_MAX_OUTPUT_TOKENS', value)
        with pytest.raises(ValueError):
            budget('chat')


def test_hypothetical_answer_does_not_turn_user_numbers_into_financial_evidence():
    from app.schemas.chat import validate_response
    response = copy.deepcopy(ANSWER)
    response.update(answer='Ejemplo hipotetico: 125 EUR por dos unidades son 250 EUR.',
        assumptions=['Cifras aportadas por el usuario; multiplicacion.'],
        limitations=['No son costes Azure contrastados.'])
    assert validate_response(response, [], expected_subscriptions=[]) == response
    source = {'id': 'definition', 'kind': 'corpus', 'source': 'synthetic', 'title': 'Definition'}
    response.update(status='partial', evidence=[source],
        metrics=[{'name': 'total_cost', 'value': '250', 'unit': 'EUR', 'evidence_ids': ['definition']}])
    with pytest.raises(ValueError) as caught:
        validate_response(response, [source], expected_subscriptions=[])
    assert caught.value.rule_code == 'financial_metric_unverified'
    financial = {'id': 'cost:verified', 'kind': 'cost_query', 'source': 'billing-summary-v2',
        'title': 'Verified', 'metrics': [{'name': 'total_cost', 'value': '0.00', 'unit': 'EUR'}]}
    response.update(status='ok', evidence=[{k: financial[k] for k in ('id', 'kind', 'source', 'title')}],
        metrics=[{'name': 'total_cost', 'value': '0.00', 'unit': 'EUR', 'evidence_ids': ['cost:verified']}])
    assert validate_response(response, [financial]) == response


def test_server_does_not_autocite_retrieved_but_unused_evidence():
    from app.schemas.chat import response_citations
    from app.services.citations import resolve_citations
    chunks = [{'chunk_id': name, 'document_id': 'synthetic-manual', 'tenant_id': 't',
        'chunk_index': index, 'title': 'Manual', 'source': 'synthetic',
        'content': 'Synthetic unrelated section ' + name} for index, name in enumerate(['used', 'unused'])]
    evidence = [{'id': item['chunk_id'], 'kind': 'corpus', 'title': item['title'],
        'source': item['source'], 'content': item['content']} for item in chunks]
    context = {'authorized_evidence': evidence,
        'source_citations': resolve_citations(['used', 'unused'], chunks, 't')}
    candidate = {'evidence': [{key: value for key, value in evidence[0].items() if key != 'content'}]}
    ids, citations = response_citations(candidate, context)
    assert ids == ['used'] and [item['evidence_id'] for item in citations] == ['used']
    assert response_citations({'evidence': []}, context) == ([], [])
