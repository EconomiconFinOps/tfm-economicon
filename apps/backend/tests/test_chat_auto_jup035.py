"""Auto decisions retain the existing evidence and atomic history boundary."""
import copy
import json

import pytest

from test_chat_operations_jup035 import ANSWER, api, body, headers, messages, path, run


def test_calculation_diagnostic_is_closed_and_contains_no_rejected_text(api, monkeypatch, caplog):
    from app.core.chat_calculations import CalculationError
    async def stream(claim):
        raise CalculationError('secret synthetic payload should not be logged')
        yield
    monkeypatch.setattr(api[2], 'stream', stream)
    async def scenario(client):
        response = await client.post(path(), json=body(), headers=headers())
        assert 'event: final' not in response.text and messages(api[1]) == []
    run(scenario, api)
    assert 'calculation_validation' in caplog.text and 'calculation_invalid' in caplog.text
    assert 'secret synthetic payload' not in caplog.text


def test_rendered_arithmetic_stream_candidate_and_saved_pair_are_identical(api, monkeypatch):
    from app.core.chat_calculations import CalculationStream, calculate, render_text
    question = 'Ejemplo hipotético: 73 EUR y 20 EUR.'
    context = {'messages': [{'role': 'user', 'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})}]}
    plan = [{'left': '73', 'right': '20', 'operator': 'subtract', 'left_unit': 'EUR', 'right_unit': 'EUR'}]
    calculations = calculate(context, plan)
    raw = 'Ejemplo 😀: [[calc:0]]. Resultado hipotético.'
    result = copy.deepcopy(ANSWER)
    result['answer'] = render_text(raw, calculations)
    async def stream(claim):
        renderer = CalculationStream(calculations)
        for char in raw:
            text = renderer.feed(char)
            if text: yield {'type': 'delta', 'text': text}
        tail = renderer.feed('', final=True)
        if tail: yield {'type': 'delta', 'text': tail}
        yield {'type': 'candidate', 'result': result, 'finish_reason': 'stop'}
    monkeypatch.setattr(api[2], 'stream', stream)
    async def scenario(client):
        response = await client.post(path(), json=body(content=question), headers=headers())
        assert 'event: final' in response.text
        deltas = []
        for block in response.text.split('\n\n'):
            if 'event: delta' in block:
                data = json.loads(next(line[6:] for line in block.splitlines() if line.startswith('data: ')))
                deltas.append(data['text'])
        saved = messages(api[1])
        assert len(saved) == 2
        assistant = next(row for row in saved if row['role'] == 'assistant')
        assert ''.join(deltas) == result['answer'] == assistant['content']
        assert assistant['metadata']['response'] == result
        assert api[1].fetch_messages('alice-chat', 't', 'alice') == saved
    run(scenario, api)


@pytest.mark.parametrize('case', ['greeting', 'clarification', 'billing', 'invented_citation', 'user_number', 'corpus_number'])
def test_no_search_keeps_server_authority_and_one_pair(api, monkeypatch, case):
    source = {'id': 'authorized', 'kind': 'cost_query' if case == 'billing' else 'corpus',
              'title': 'Synthetic', 'source': 'server',
              'metrics': [{'name': 'cost', 'value': '12', 'unit': 'EUR'}]}
    authorized = [source] if case in ('billing', 'user_number', 'corpus_number') else []
    answer = copy.deepcopy(ANSWER)
    if case == 'greeting':
        answer['answer'] = 'Hola. ¿Qué consulta FinOps quieres realizar?'
    if case == 'clarification':
        answer.update(status='insufficient_data', answer='Necesito la política interna para responder con sustento.')
    if case in ('billing', 'invented_citation', 'user_number', 'corpus_number'):
        answer.update(status='partial', evidence=[{k: source[k] for k in ('id','kind','title','source')}])
    if case in ('billing', 'user_number', 'corpus_number'):
        answer['metrics'] = [{**source['metrics'][0], 'evidence_ids': ['authorized']}]
    async def build(scope, payload, descriptor):
        return {'prompt_version': 'synthetic-v2', 'tool_protocol': 'structured-documentation-v3',
                'messages': [], 'authorized_evidence': authorized, 'source_citations': [],
                'financial_metrics_allowed': case == 'billing', 'response_period': None,
                'response_subscriptions': []}
    async def forbidden(*args):
        pytest.fail('Zero-tool decision must not retrieve or post a tool result')
    build.tool_extension = forbidden
    monkeypatch.setattr(api[0].state, 'chat_context_builder', build)
    monkeypatch.setattr(api[2], 'tool_result', forbidden, raising=False)
    async def stream(claim):
        yield {'type': 'candidate', 'finish_reason': 'stop', 'result': answer,
               'usage': {'prompt_tokens': 30, 'completion_tokens': 4, 'total_tokens': 34}}
    monkeypatch.setattr(api[2], 'stream', stream)
    async def scenario(client):
        response = await client.post(path(), json=body(), headers=headers())
        saved = messages(api[1])
        if case in ('invented_citation', 'user_number', 'corpus_number'):
            assert 'event: final' not in response.text
            assert saved == []
        else:
            assert 'event: final' in response.text, response.text
            assert len(saved) == 2
            persisted = next(x for x in saved if x['role'] == 'assistant')
            assert persisted['content'] == answer['answer']
            assert persisted['metadata']['response'] == answer
            assert persisted['metadata']['generation']['usage']['total_tokens'] == 34
            assert api[1].fetch_messages('alice-chat','t','alice') == saved
    run(scenario, api)


@pytest.mark.parametrize('duplicate', [False, True])
def test_invalid_or_second_tool_never_persists(api, monkeypatch, duplicate):
    assistant = {'action':'search' if duplicate else 'unknown','query':'policy','calculations':[]}
    calls = []
    async def build(scope, payload, descriptor):
        return {'prompt_version': 'synthetic-v2', 'tool_protocol': 'structured-documentation-v3',
                'messages': [], 'authorized_evidence': []}
    async def extension(scope, context, call, deadline):
        from app.core.chat_resources import validate_search_call
        validate_search_call(call)
        calls.append(call)
        return {}, context
    build.tool_extension = extension
    monkeypatch.setattr(api[0].state, 'chat_context_builder', build)
    async def send(*args): pass
    monkeypatch.setattr(api[2], 'tool_result', send, raising=False)
    async def stream(claim):
        yield {'type': 'tool_call', 'assistant': assistant}
        yield {'type': 'tool_call', 'assistant': assistant}
        yield {'type': 'candidate', 'finish_reason': 'stop', 'result': ANSWER}
    monkeypatch.setattr(api[2], 'stream', stream)
    async def scenario(client):
        response = await client.post(path(), json=body(), headers=headers())
        assert 'event: final' not in response.text
        assert messages(api[1]) == []
        assert len(calls) == int(duplicate)
    run(scenario, api)
