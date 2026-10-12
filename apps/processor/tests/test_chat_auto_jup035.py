"""Synthetic provider wire; no paid calls, model decisions are controlled."""
import asyncio
import copy
import io
import json
import threading
import time
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.clients.chat_gateway import ChatGateway
from test_chat_gateway_jup035 import ANSWER, _provider
from test_chat_private_jup035 import private, claim, run, signed


TOOL = {'id': 'call-auto', 'type': 'function', 'function': {
    'name': 'search_documentation', 'arguments': '{"query":"Synthetic policy"}'}}


@pytest.mark.parametrize('fragmented', [False, True])
def test_multiple_native_calls_fail_closed_before_search_without_retry(monkeypatch, caplog, fragmented):
    second = {**TOOL, 'id': 'call-extra'}
    calls = [{'index': 0, **TOOL}, {'index': 1, **second}]
    response = wire({'tool_calls': calls}, 'tool_calls')
    if fragmented:
        response = wire({'tool_calls': calls[:1]}, None).replace(b'data: [DONE]\n\n', b'') + wire({'tool_calls': calls[1:]}, 'tool_calls')
    gateway, requests = provider(monkeypatch, [response])
    async def search(assistant): pytest.fail('Multiple calls must never dispatch a partial search')
    async def exercise():
        return [r async for r in gateway({'messages': [], 'tool_protocol': 'auto-documentation-v2',
            'financial_metrics_allowed': False}, time.time()+60, tool_result=search)]
    records = asyncio.run(exercise())
    assert [r['type'] for r in records] == ['error']
    assert len(requests) == 1
    assert 'native_multiple_calls' in caplog.text
    assert 'call-extra' not in caplog.text and 'Synthetic policy' not in caplog.text


@pytest.mark.parametrize('search', [False, True])
def test_final_schema_uses_only_effective_authenticated_evidence(monkeypatch, search):
    source = {'id': 'corpus:current:0', 'kind': 'corpus', 'title': 'Current synthetic source',
              'source': 'Current manual', 'content': 'Synthetic authorized text'}
    delta = {'tool_calls': [{'index': 0, **TOOL}]} if search else {'content': 'Hello'}
    gateway, requests = provider(monkeypatch, [wire(delta, 'tool_calls' if search else 'stop'),
        wire({'content': json.dumps(_provider(ANSWER))})])
    async def result(assistant):
        return {'tool_call_id': TOOL['id'], 'content': json.dumps({'evidence': [source], 'omissions': []}), 'variable_tokens': 0}
    async def exercise():
        return [r async for r in gateway({'tool_protocol': 'auto-documentation-v2', 'financial_metrics_allowed': False,
            'messages': [], 'authorized_evidence': []}, time.time()+60, tool_result=result)]
    records = asyncio.run(exercise())
    assert records[-1]['type'] == 'candidate' and len(requests) == 2
    assert 'response_format' not in requests[0]
    schema = requests[1]['response_format']['json_schema']['schema']
    if search:
        choices = schema['$defs']['Evidence']['anyOf']
        assert len(choices) == 1
        assert {k: v['const'] for k, v in choices[0]['properties'].items()} == {k: source[k] for k in ('id','kind','title','source')}
    else:
        assert schema['properties']['evidence']['maxItems'] == 0
        assert not {'ok', 'partial'} & set(schema['properties']['status']['enum'])


def wire(delta, finish='stop', tokens=12):
    event = {'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}],
             'usage': {'prompt_tokens': tokens-2, 'completion_tokens': 2,
                       'total_tokens': tokens, 'cost': .001}}
    return ('data: '+json.dumps(event)+'\n\ndata: [DONE]\n\n').encode()


def provider(monkeypatch, responses):
    gateway = ChatGateway(SimpleNamespace(llm_model='economicon-chat',
        litellm_base_url='http://synthetic.invalid/v1', litellm_api_key=SecretStr('synthetic')))
    requests = []
    class Response(io.BytesIO):
        headers = {'Content-Type': 'text/event-stream'}
        def read1(self, size=-1):
            return super().read1(min(size, 7))  # split UTF-8/SSE/JSON on real byte boundaries
    def opened(req, **kwargs):
        requests.append(json.loads(req.data))
        response = responses[len(requests)-1]
        if isinstance(response, Exception): raise response
        return Response(response)
    monkeypatch.setattr(gateway.client.transport, 'open', opened)
    return gateway, requests


@pytest.mark.parametrize('search', [True, False])
def test_auto_parser_accepts_decision_without_exposing_text(monkeypatch, search):
    delta = {'tool_calls': [{'index': 0, **TOOL}]} if search else {'content': 'PROVISIONAL SECRET'}
    gateway, requests = provider(monkeypatch, [wire(delta, 'tool_calls' if search else 'stop')])
    records = list(gateway._records({'messages': [], 'financial_metrics_allowed': False},
        time.time()+60, {}, threading.Event(), 'auto'))
    assert [r['type'] for r in records] == ['tool_call' if search else 'decision']
    assert 'PROVISIONAL SECRET' not in json.dumps(records)
    assert 'response_format' not in requests[0]


@pytest.mark.parametrize('search', [True, False])
def test_auto_finalizes_in_two_calls_and_sums_usage(monkeypatch, search):
    delta = {'tool_calls': [{'index': 0, **TOOL}]} if search else {'content': 'PROVISIONAL SECRET'}
    gateway, requests = provider(monkeypatch, [wire(delta, 'tool_calls' if search else 'stop'),
        wire({'content': json.dumps(_provider(ANSWER))}, tokens=24)])
    context = {'tool_protocol': 'auto-documentation-v2', 'financial_metrics_allowed': False,
               'messages': [{'role': 'system', 'content': 'Synthetic'}, {'role': 'user', 'content': 'Hello'}]}
    calls = []
    async def result(assistant):
        calls.append(assistant)
        return {'tool_call_id': TOOL['id'], 'content': '{"evidence":[],"omissions":[]}', 'variable_tokens': 0}
    async def exercise():
        return [r async for r in gateway(context, time.time()+60, tool_result=result)]
    records = asyncio.run(exercise())
    assert len(requests) == 2
    assert [p['tool_choice'] for p in requests] == ['auto', 'none']
    assert 'response_format' not in requests[0]
    assert requests[1]['response_format']['json_schema']['strict'] is True
    assert len(calls) == int(search)
    assert records[-1]['type'] == 'candidate'
    assert records[-1]['usage']['total_tokens'] == 36
    assert records[-1]['usage']['cost_usd'] == '0.002'
    assert not any(r['type'] == 'decision' for r in records)
    assert 'PROVISIONAL SECRET' not in json.dumps(records+requests[1:])
    if not search:
        assert requests[1]['messages'] == context['messages']


@pytest.mark.parametrize('arguments', ['{', '{"query":""}', '{"query":"x","tenant":"other"}'])
def test_auto_rejects_malformed_arguments(monkeypatch, arguments):
    tool = copy.deepcopy(TOOL)
    tool['function']['arguments'] = arguments
    gateway, requests = provider(monkeypatch, [wire({'tool_calls': [{'index': 0, **tool}]}, 'tool_calls')])
    records = list(gateway._records({'messages': [], 'financial_metrics_allowed': False}, time.time()+60, {}, threading.Event(), 'auto'))
    assert records[-1]['type'] == 'error'
    assert len(requests) == 1


@pytest.mark.parametrize('failure', ['second_tool', 'invalid_final', 'eof', 'length_decision', 'wrong_id', 'unknown_tool'])
def test_auto_failures_cannot_dispatch_a_third_call(monkeypatch, failure):
    tool = copy.deepcopy(TOOL)
    if failure == 'unknown_tool': tool['function']['name'] = 'other'
    decision = wire({'tool_calls': [{'index': 0, **tool}]}, 'tool_calls')
    final = wire({'content': json.dumps(_provider(ANSWER))})
    if failure == 'second_tool': final = decision
    if failure == 'invalid_final': final = wire({'content': '{"answer":"not strict"}'})
    if failure == 'eof': final = final.replace(b'data: [DONE]\n\n', b'')
    if failure == 'length_decision': decision = wire({'content': 'incomplete'}, 'length')
    gateway, requests = provider(monkeypatch, [decision, final])
    async def result(assistant):
        return {'tool_call_id': 'wrong' if failure == 'wrong_id' else TOOL['id'],
                'content': '{"evidence":[],"omissions":[]}', 'variable_tokens': 0}
    async def exercise():
        return [r async for r in gateway({'messages': [], 'tool_protocol': 'auto-documentation-v2',
            'financial_metrics_allowed': False}, time.time()+60, tool_result=result)]
    if failure == 'wrong_id':
        with pytest.raises(ValueError, match='correlation'): asyncio.run(exercise())
    else:
        records = asyncio.run(exercise())
        assert records[-1]['type'] == 'error'
        assert all(r['type'] != 'candidate' for r in records)
    assert len(requests) == (1 if failure in ('length_decision','wrong_id','unknown_tool') else 2)


@pytest.mark.parametrize('phase', ['decision', 'search', 'final'])
def test_auto_cancellation_closes_work_without_candidate(monkeypatch, phase):
    gateway, requests = provider(monkeypatch, [])
    entered = threading.Event()
    stopped = threading.Event()
    deadlines = []
    def records(context, deadline, holder, cancelled, choice=None):
        deadlines.append(deadline)
        if (phase == 'decision' and choice == 'auto') or (phase == 'final' and choice == 'none'):
            entered.set()
            assert cancelled.wait(2), 'Cancellation must reach the streaming worker'
            stopped.set()
            return
        yield {'type': 'tool_call', 'assistant': {'role':'assistant','content':None,'tool_calls':[TOOL]}, 'usage': None}
    monkeypatch.setattr(gateway, '_records', records)
    async def result(assistant):
        if phase == 'search':
            entered.set()
            try: await asyncio.Event().wait()
            finally: stopped.set()
        return {'tool_call_id': TOOL['id'], 'content': '{"evidence":[],"omissions":[]}', 'variable_tokens': 0}
    async def exercise():
        deadline = time.time()+60
        async def consume():
            return [r async for r in gateway({'tool_protocol':'auto-documentation-v2','messages':[]}, deadline, tool_result=result)]
        task = asyncio.create_task(consume())
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
        assert await asyncio.to_thread(stopped.wait, 2)
        assert deadlines and all(d == deadline for d in deadlines)
    asyncio.run(exercise())


@pytest.mark.parametrize('search', [True, False])
def test_auto_deadline_is_not_reset_after_decision(monkeypatch, search):
    gateway, _ = provider(monkeypatch, [])
    deadline = time.time()+60
    seen = []
    def records(context, limit, holder, cancelled, choice=None):
        seen.append((limit, choice))
        if choice == 'auto':
            monkeypatch.setattr(time, 'time', lambda: deadline-4)
            yield {'type': 'tool_call', 'assistant': {'role':'assistant','content':None,'tool_calls':[TOOL]}} if search else {'type':'decision'}
        else: pytest.fail('Expired attempt reached second generation')
    monkeypatch.setattr(gateway, '_records', records)
    async def result(assistant): pytest.fail('Expired attempt reached retrieval')
    async def exercise():
        return [r async for r in gateway({'tool_protocol':'auto-documentation-v2','messages':[]}, deadline, tool_result=result)]
    result_records = asyncio.run(exercise())
    assert result_records[-1] == {'type':'error','category':'timeout'}
    assert seen == [(deadline, 'auto')]


@pytest.mark.parametrize('search', [True, False])
def test_private_endpoint_runs_real_auto_gateway_and_hmac_continuation(private, monkeypatch, search):
    delta = {'tool_calls': [{'index':0, **TOOL}]} if search else {'content':'PROVISIONAL SECRET'}
    gateway, requests = provider(monkeypatch, [wire(delta, 'tool_calls' if search else 'stop'),
        wire({'content':json.dumps(_provider(ANSWER))})])
    monkeypatch.setattr(private[0].state, 'chat_gateway', gateway)
    async def scenario(client):
        payload = claim(context={'prompt_version':'synthetic-v2', 'messages':[
            {'role':'user','content':'Synthetic policy'}], 'financial_metrics_allowed':False,
            'tool_protocol':'auto-documentation-v2'})
        raw = json.dumps(payload).encode()
        task = asyncio.create_task(client.post('/internal/chat/v2/attempts', content=raw,
            headers=signed('POST','/internal/chat/v2/attempts',raw)))
        try:
            if search:
                for _ in range(200):
                    pending = [e for e in private[0].state.chat_attempts.values() if e['tool_future'] is not None]
                    if pending: break
                    await asyncio.sleep(.005)
                assert pending
                endpoint = '/internal/chat/v2/attempts/attempt/tool-result'
                value = {'v':2,'claim':payload,'tool_result':{'tool_call_id':TOOL['id'],
                    'content':'{"evidence":[],"omissions":[]}', 'variable_tokens':0}}
                raw_result = json.dumps(value).encode()
                response = await client.post(endpoint, content=raw_result, headers=signed('POST',endpoint,raw_result))
                assert response.status_code == 200, response.text
            response = await asyncio.wait_for(task, 3)
            records = [json.loads(line) for line in response.text.splitlines()]
            assert records[-1]['type'] == 'candidate_end', response.text
            assert records[-1]['usage']['total_tokens'] == 24
            assert sum(r['type']=='tool_call' for r in records) == int(search)
            assert 'PROVISIONAL SECRET' not in response.text
            assert len(requests) == 2
        finally:
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)
    run(private[0], scenario)


@pytest.mark.parametrize('phase', ['decision','final'])
def test_auto_429_never_retries_or_changes_provider(monkeypatch, phase):
    from urllib.error import HTTPError
    failure = HTTPError('http://synthetic.invalid', 429, 'Synthetic', {'Retry-After':'17'}, io.BytesIO())
    responses = [failure] if phase == 'decision' else [wire({'content':'private decision'}), failure]
    gateway, requests = provider(monkeypatch, responses)
    async def exercise():
        return [r async for r in gateway({'tool_protocol':'auto-documentation-v2',
            'messages':[], 'financial_metrics_allowed':False}, time.time()+60)]
    records = asyncio.run(exercise())
    assert records[-1] == {'type':'error','status':429,'retry_after':'17'}
    assert len(requests) == len(responses)
    assert all(p['num_retries']==0 and p['provider']=={
        'order':['deepinfra/fp4'],'allow_fallbacks':False,'require_parameters':True} for p in requests)
    if phase == 'final': assert requests[1]['timeout'] <= requests[0]['timeout']


def test_old_protocol_cannot_silently_become_a_direct_generation(monkeypatch):
    gateway, requests = provider(monkeypatch, [])
    async def exercise():
        return [r async for r in gateway({'tool_protocol':'required-documentation-v1'}, time.time()+60)]
    assert asyncio.run(exercise()) == [{'type':'error','status':422,'category':'invalid_response'}]
    assert requests == []
