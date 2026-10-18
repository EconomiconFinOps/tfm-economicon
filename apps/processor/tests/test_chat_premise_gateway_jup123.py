"""Exercise retrieval/draft/final, schema validation and public assembly offline."""
import asyncio
import copy
import json
import time

import pytest
from test_chat_auto_jup035 import provider, wire, review_wires
from test_chat_reporting_jup123 import catalog as reporting_catalog, response as reporting_response, QUESTION as REPORTING_QUESTION
from test_chat_missing_spend_jup123 import catalog as missing_catalog, response as missing_response, QUESTION as MISSING_QUESTION
from app.core.chat_resources import validate_search_call


@pytest.mark.parametrize('kind', ['reporting', 'missing_spend'])
@pytest.mark.parametrize('read_size', [1, 17, 8192])
@pytest.mark.parametrize('contradictory_auxiliary', [False, True])
def test_premise_terminal_survives_full_gateway_or_rejects_contradiction(monkeypatch, kind, read_size, contradictory_auxiliary):
    if kind == 'reporting':
        q = reporting_catalog(); question = REPORTING_QUESTION; value = reporting_response(q)
    else:
        q = missing_catalog(); question = MISSING_QUESTION; value = missing_response(q)
    sources = copy.deepcopy(q.authorized_sources)
    value.update(schema_version='1.0', scope={'cloud': 'azure', 'data_environment': 'simulated'})
    if contradictory_auxiliary:
        value['limitations'] = [[{'inference': 'La calidad es insuficiente y el gasto es cero.'}]]
    gateway, requests = provider(monkeypatch, review_wires(wire({'content': json.dumps(value)})), read_size=read_size)
    context = {'tool_protocol': 'server-documentation-v4', 'financial_metrics_allowed': False,
               'authorized_evidence': [], 'messages': [{'role': 'user',
                'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})}]}
    searches = []
    async def retrieve(control):
        searches.append(control)
        return {'tool_call_id': validate_search_call(control, context)[0],
                'content': json.dumps({'evidence': sources, 'omissions': []}), 'variable_tokens': 0}
    async def exercise():
        return [record async for record in gateway(context, time.time()+60, tool_result=retrieve)]
    records = asyncio.run(exercise())
    assert len(searches) == 1 and len(requests) == 2
    assert all('tools' not in request and request['num_retries'] == 0 for request in requests)
    if contradictory_auxiliary:
        assert records[-1]['type'] == 'error'
        assert not any(record['type'] == 'candidate' for record in records)
    else:
        assert records[-1]['type'] == 'candidate', records
        result = records[-1]['result']
        assert ''.join(record['text'] for record in records if record['type'] == 'delta') == result['answer']
        assert result['scope']['period'] is None and result['scope']['subscription_ids'] == []
        if kind == 'reporting':
            assert 'corresponde a showback' in result['answer']
            assert 'no se concluye que sea suficiente ni insuficiente' in result['answer']
            assert [item['id'] for item in result['evidence']] == ['policy:1']
        else:
            assert result['status'] == 'insufficient_data'
            assert 'No se puede concluir' in result['answer']
            assert result['evidence'] == [] and result['metrics'] == []
