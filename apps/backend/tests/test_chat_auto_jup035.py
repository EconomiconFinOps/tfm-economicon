"""Auto decisions retain the existing evidence and atomic history boundary."""
import copy
import json

import pytest

from test_chat_operations_jup035 import ANSWER, api, body, headers, messages, path, run


@pytest.mark.parametrize('case',['valid','quote','metadata','metrics','savings'])
def test_explicit_recommendation_evidence_projection_keeps_atomic_history_and_authority(api,monkeypatch,case):
    import importlib.util
    import sys
    from pathlib import Path
    from app.core.chat_segments import render_response
    base=Path(__file__).parents[2]/'processor/app'
    def load(name,location):
        spec=importlib.util.spec_from_file_location(name,location)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        return module
    parser_module=load('recommendation_stream_parser',base/'clients/chat_stream_parser.py')
    schema_module=load('recommendation_provider_schema',base/'agents/schemas.py')
    source={'id':'sizing-policy','kind':'corpus','title':'Sizing policy','source':'guide',
        'content':'Compare observed demand before committing capacity.'}
    intro={**source,'id':'sizing-intro','content':'Sizing depends on observed demand.'}
    from app.core.chat_rules import QuantityCatalog
    catalog=QuantityCatalog({});catalog.authorized_sources=[intro,source]
    selected={'source_id':source['id'],'passage':source['content']}
    value=copy.deepcopy(ANSWER)
    value['scope'].pop('period');value['scope'].pop('subscription_ids')
    value.update(basis='authorized_evidence',status='ok',answer=[{'documentary':{'source_id':intro['id'],'passage':intro['content']}},{'inference':'Revisar la demanda observada.'}],limitations=[],
        evidence=[],
        recommendations=[{'category':'investigation','action':[{'inference':'Revisar la demanda.'}],
            'rationale':[{'documentary':selected}],
            'estimated_savings':None,'currency':None,'confidence':'medium','risk':'low',
            'requires_human_approval':True}])
    if case=='quote':selected['passage']='not an authorized passage'
    if case=='metadata':selected['source']='foreign source'
    if case=='metrics':value['metrics']=[{'name':'cost','value':'9','unit':'EUR','evidence_ids':[source['id']]}]
    if case=='savings':value['recommendations'][0].update(estimated_savings='9',currency='EUR')
    async def context_builder(scope,payload,descriptor):
        return {'prompt_version':descriptor['prompt_version'],'messages':[],
            'authorized_evidence':[intro,source],'financial_metrics_allowed':False,
            'source_citations':[{'evidence_id':item['id'],'kind':'corpus','title':item['title'],
                'source':item['source'],'excerpt':item['content'],'document_id':'doc',
                'reference':'document:doc/'+item['id'],'section':'Sizing','page':None} for item in (intro,source)],
            'screen_context':payload['screen_context']}
    monkeypatch.setattr(api[0].state,'chat_context_builder',context_builder)
    projected=[]
    async def stream(claim):
        parser=parser_module.SegmentAnswerJSON([],quantities=catalog)
        for char in json.dumps(value,ensure_ascii=True):
            delta=parser.feed(char)
            if delta:yield {'type':'delta','text':delta}
        rendered=render_response(value,[],quantities=catalog)
        result=schema_module.assemble_chat_response(rendered,None,authorized_evidence=[intro,source])
        assert parser.finish()==result['answer']
        projected.append(result)
        yield {'type':'candidate','result':result,'finish_reason':'stop'}
    monkeypatch.setattr(api[2],'stream',stream)
    async def scenario(client):
        response=await client.post(path(),json=body(),headers=headers())
        saved=messages(api[1])
        if case!='valid':
            assert 'event: final' not in response.text and saved==[]
        else:
            assert 'event: final' in response.text and len(saved)==2
            assistant=next(item for item in saved if item['role']=='assistant')
            assert assistant['content']==projected[0]['answer']
            assert assistant['metadata']['response']==projected[0]
            assert projected[0]['recommendations'][0]['evidence_ids']==['sizing-policy']
            assert projected[0]['metrics']==[]
    run(scenario,api)


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


@pytest.mark.parametrize('classification',[False,True,'quantities','boolean','boolean-corpus','scenario','scenario-zero','scenario-explained','request','request-specific','documentary'])
def test_rendered_arithmetic_stream_candidate_and_saved_pair_are_identical(api, monkeypatch, classification):
    from app.core.chat_expressions import quantities,ExpressionRenderer
    from app.core.chat_segments import render_segments,render_classified_answer,render_response
    import importlib.util
    from pathlib import Path
    location=Path(__file__).parents[2]/'processor/app/clients/chat_stream_parser.py'
    spec=importlib.util.spec_from_file_location('segmented_stream_parser',location)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    question = 'Ejemplo hipotético: 73 EUR y 20 EUR.'
    context = {'messages': [{'role': 'user', 'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})}]}
    catalog=quantities(question)
    difference={'operation':'difference','current':{'quantity':'73 EUR'},'baseline':{'quantity':'20 EUR'}}
    comparison={'operation':'compare','left':difference,'right':{'quantity':'20 EUR'},'relation':'gt'}
    segments=[{'inference':'  Ejemplo 😀: '},{'expression':difference},{'inference':'Criterio: '},{'expression':comparison},{'inference':'Resultado hipotético.  '}]
    authorized=[]
    if classification is True:
        from test_chat_interval_rules_jup035 import catalog as rule_catalog, sources, percent
        question='rework 7 EUR; remaining 93 EUR.'
        authorized=sources()
        catalog=rule_catalog(question,authorized)
        segments={'calculations':[],'classification':{'operation':'classify',
            'rule_id':catalog.rules[0]['id'],'value':percent('7','93')}}
        async def context_builder(scope,payload,descriptor):
            return {'prompt_version':descriptor['prompt_version'],'messages':[],
                'authorized_evidence':authorized,'financial_metrics_allowed':False,
                'source_citations':[{'evidence_id':source['id'],'kind':'corpus',
                    'title':source['title'],'source':source['source'],'excerpt':source['content'][:140],
                    'document_id':'doc','reference':'document:doc/'+source['id'],
                    'section':'Rework','page':None} for source in authorized],
                'screen_context':payload['screen_context']}
        monkeypatch.setattr(api[0].state,'chat_context_builder',context_builder)
    if classification=='quantities':
        question='Importes: 100 EUR y 100 USD.'
        catalog=quantities(question)
        segments=[{'quantity':'100 EUR'},{'quantity':'100 USD'}]
    if classification=='scenario':
        question='Importes separados: 37 EUR y 42 USD.'
        catalog=quantities(question)
        segments={'scenario':{'calculations':[],'quantities':['37 EUR','42 USD']}}
    if classification=='scenario-zero':
        question='Base 0 EUR; observado 37 EUR.'
        catalog=quantities(question)
        segments={'scenario':{'calculations':[
            {'operation':'difference','current':{'quantity':'37 EUR'},'baseline':{'quantity':'0 EUR'}},
            {'operation':'relative_change','current':{'quantity':'37 EUR'},'baseline':{'quantity':'0 EUR'}}],
            'quantities':[]}}
    if classification=='scenario-explained':
        question='Sandbox-z, marzo: Compute 73 EUR y Network 20 EUR.'
        catalog=quantities(question)
        segments={'scenario':{'segments':[{'inference':'En marzo, sandbox-z, Compute tiene mayor importe que Network. 😀 Diferencia: '},
            {'expression':difference}]}}
    if classification=='request':
        segments={'request':{'reason':'authorized_cost_data'}}
    if classification=='request-specific':
        segments={'request':{'reason':'missing_documentation','missing_requirement':'La política del ámbito sandbox-z. 😀'}}
    if classification in ('boolean','boolean-corpus'):
        from test_chat_boolean_rules_jup035 import catalog as boolean_catalog, request, answer
        question=request()
        document=None
        if classification=='boolean-corpus':
            question='¿Se cumple la regla?\n\nBaseline 80 EUR/día; observado 96 EUR/día.'
            document='# Policy\n## Changes\nrelative_delta >20 % AND absolute_delta >12 EUR/day\n## Next\nOther policy.'
        catalog=boolean_catalog(question,document)
        authorized=catalog.rule_sources
        segments=answer(catalog)
        if authorized:
            async def context_builder(scope,payload,descriptor):
                return {'prompt_version':descriptor['prompt_version'],'messages':[],
                    'authorized_evidence':authorized,'financial_metrics_allowed':False,
                    'source_citations':[{'evidence_id':source['id'],'kind':'corpus',
                        'title':source['title'],'source':source['source'],'excerpt':source['content'][:140],
                        'document_id':'doc','reference':'document:doc/'+source['id'],
                        'section':'Changes','page':None} for source in authorized],
                    'screen_context':payload['screen_context']}
            monkeypatch.setattr(api[0].state,'chat_context_builder',context_builder)
    if classification=='documentary':
        from app.core.chat_rules import QuantityCatalog
        source={'id':'guide','kind':'corpus','title':'Guide','source':'guide.md',
                'content':'Confirm the scope before comparison.'}
        authorized=[source];catalog=QuantityCatalog({});catalog.authorized_sources=authorized
        segments=[{'documentary':{'source_id':'guide','passage':source['content']}},
                  {'inference':'Conviene contrastar el ámbito aportado. 😀'}]
        async def context_builder(scope,payload,descriptor):
            return {'prompt_version':descriptor['prompt_version'],'messages':[],
                'authorized_evidence':authorized,'financial_metrics_allowed':False,
                'source_citations':[{'evidence_id':'guide','kind':'corpus','title':'Guide','source':'guide.md',
                    'excerpt':source['content'],'document_id':'doc','reference':'document:doc/guide','section':'Scope','page':None}],
                'screen_context':payload['screen_context']}
        monkeypatch.setattr(api[0].state,'chat_context_builder',context_builder)
    basis=None;actions=[]
    if isinstance(segments,dict) and 'scenario' in segments:
        scenario=segments['scenario']
        segments=scenario.get('segments',[*[{'quantity':key} for key in scenario.get('quantities',[])],
            *[{'expression':node} for node in scenario.get('calculations',[])]])
    if classification in ('request','request-specific'):
        basis='missing_data'
        segments=[{'inference':'Necesito contrastar la fuente de costes del ámbito sandbox-z. 😀'}]
        actions=[[{'inference':'Aporta la fuente y el período aplicables.'}]]
    elif isinstance(segments,list):basis='authorized_evidence' if classification=='documentary' else 'user_scenario'
    raw = json.dumps(({'basis':basis} if basis else {})|{'answer':segments},ensure_ascii=True)
    private_result={**copy.deepcopy(ANSWER),'answer':segments,'evidence':[],
        'assumptions':[],'limitations':[],'next_actions':actions,'recommendations':[],'metrics':[]}
    if basis:
        private_result['basis']=basis
        private_result['status']='insufficient_data'
    if classification=='boolean':private_result['status']='insufficient_data'
    if classification=='boolean-corpus':private_result['status']='ok'
    result=render_response(private_result,[],quantities=catalog)
    async def stream(claim):
        renderer = module.SegmentAnswerJSON([],quantities=catalog)
        for char in raw:
            text = renderer.feed(char)
            if text: yield {'type': 'delta', 'text': text}
        assert renderer.finish()==result['answer']
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
        return {'prompt_version': 'synthetic-v2', 'tool_protocol': 'server-documentation-v4',
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
    assistant = {'action':'search' if duplicate else 'unknown','query':'policy'}
    calls = []
    async def build(scope, payload, descriptor):
        return {'prompt_version': 'synthetic-v2', 'tool_protocol': 'server-documentation-v4',
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
