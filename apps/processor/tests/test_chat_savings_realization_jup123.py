"""Savings stages and formula operands remain server-owned and source-bound."""
import copy
import json
from decimal import Decimal
from itertools import permutations

import pytest

from app.agents.schemas import chat_provider_schema, assemble_chat_response
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_expressions import context_quantities
from app.core.chat_savings_realization import required_savings_realization, savings_realization_answer
from app.core.chat_segments import render_response


def catalog(identified='200',estimated='150',verified='80',unit='EUR/mes',
            order=('identificado','implementado estimado','verificado'),question=None,scenario=None,records=()):
    question=question or '¿Cuánto ahorro hemos conseguido con las recomendaciones?'
    amounts=dict(zip(('identificado','implementado estimado','verificado'),(identified,estimated,verified)))
    fields='; '.join(f'ahorro {role} {amounts[role]} {unit}' for role in order)
    scenario=scenario or ('Escenario sintético: '+fields+'. Para este ejercicio, '
                         'realization = verificado / identificado * 100.')
    return context_quantities({'authorized_evidence':list(records),'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question+'\n\nContexto del escenario: '+scenario})}]})


def response(q):
    return {'schema_version':'1.0','scope':{'cloud':'azure','data_environment':'simulated'},
            'status':'insufficient_data','answer':{'savings_realization':required_savings_realization(q)['id']},
            'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}


@pytest.mark.parametrize('width',[1,17,8192])
@pytest.mark.parametrize('question',['¿Cuánto ahorro hemos conseguido con las recomendaciones?',
    'Calcula el savings realization.','¿Cuánto ahorro se ha verificado?'])
def test_all_three_stages_and_realization_are_complete_in_stream_and_public_final(width,question):
    q=catalog(question=question);value=response(q);wire=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    stream=''.join(parser.feed(wire[i:i+width]) for i in range(0,len(wire),width))
    rendered=render_response(value,[],quantities=q)
    public=assemble_chat_response(rendered,None,authorized_evidence=[])
    assert stream==parser.finish()==public['answer']
    for expected in ('Ahorro identificado: 200 EUR/mes','Ahorro implementado estimado: 150 EUR/mes',
                     'Ahorro verificado según el escenario: 80 EUR/mes',
                     'realizado corresponde sólo al verificado: 80 EUR/mes','80 / 200 × 100 = 40 %'):
        assert expected in stream
    assert 'no se suman' in stream and 'no verificado financieramente' in stream
    assert public['evidence']==public['metrics']==public['limitations']==[]
    assert public['status']=='insufficient_data'


@pytest.mark.parametrize('order',list(permutations(('identificado','implementado estimado','verificado'))))
def test_role_identity_does_not_depend_on_field_order_or_numeric_equality(order):
    q=catalog(identified='120',estimated='120',verified='30',order=order,unit='GBP/año')
    bound=required_savings_realization(q)
    assert bound['amounts']=={'identificado':Decimal(120),'implementado estimado':Decimal(120),'verificado':Decimal(30)}
    assert bound['realization']==25 and bound['unit']=='GBP/año'
    assert len(bound['source_spans'])==3 and len(bound['id'])==64


@pytest.mark.parametrize('identified,estimated,verified,unit,expect',[
    ('80','40','120','USD','120 / 80 × 100 = 150 %'),
    ('0','0','0','EUR/mes','Realization indefinida'),
    ('0','50','20','CAD/hora','Realization indefinida'),
    ('3','1','1','GBP/dia','1 / 3 × 100 ≈ 33.333333 %'),
    ('0,5','0.25','0.125','CHF/mes','0.125 / 0.5 × 100 = 25 %'),
    ('0.000000000001','1','1','JPY','1 / 0.000000000001 × 100 = 100000000000000 %'),
])
def test_amounts_zero_denominator_and_rounding_do_not_invent_stage_relationships(identified,estimated,verified,unit,expect):
    q=catalog(identified,estimated,verified,unit=unit)
    text=savings_realization_answer(response(q)['answer'],q)
    assert expect in text
    if unit.endswith('/dia'):assert 'GBP/día' in text
    if Decimal(identified.replace(',','.'))==0:
        assert required_savings_realization(q)['realization'] is None
        assert 'No se inventa un porcentaje' in text


@pytest.mark.parametrize('change',[
    {'identified':'-1'}, {'verified':'1e3'}, {'estimated':'1000000000001'},
    {'unit':'EUR/USD'}, {'unit':'EUR/meses'},
    {'order':('identificado','identificado','verificado')},
    {'order':('identificado','verificado')},
    {'question':'¿Cuánto ahorro hemos conseguido? ¿Y cuál servicio cuesta más?'},
    {'question':'No calcula el savings realization.'},
    {'records':[{'id':'billing','kind':'cost_query'}]},
    {'scenario':'Escenario sintético: ahorro identificado 200 EUR/mes; ahorro implementado estimado 150 USD/mes; '
                'ahorro verificado 80 EUR/mes. Para este ejercicio, realization = verificado / identificado * 100.'},
    {'scenario':'Escenario sintético: ahorro identificado 200 EUR/mes; ahorro implementado estimado 150 EUR/día; '
                'ahorro verificado 80 EUR/mes. Para este ejercicio, realization = verificado / identificado * 100.'},
    {'scenario':'Escenario sintético: ahorro identificado 200 EUR/mes; ahorro implementado estimado 150 EUR/mes; '
                'ahorro verificado 80 EUR/mes. Para este ejercicio, realization = estimado / identificado * 100.'},
    {'scenario':'Escenario sintético: ahorro identificado 200 EUR/mes; ahorro implementado estimado 150 EUR/mes; '
                'ahorro verificado 80 EUR/mes. Para este ejercicio, realization = verificado / identificado * 100. '
                'Verificado corresponde a otro ámbito.'},
    {'scenario':'Escenario sintético: ahorro identificado 200 EUR/mes; ahorro implementado estimado 150 EUR/mes; '
                'ahorro verificado 80 EUR/mes.'},
])
def test_ambiguous_stages_units_formulas_or_scope_keep_general_route(change):
    assert required_savings_realization(catalog(**change)) is None


def test_private_schema_prevents_free_equations_forged_roles_and_auxiliary_claims():
    q=catalog();value=response(q);schema=chat_provider_schema(quantities=q,authorized_evidence=[])
    assert schema['properties']['answer']=={'const':value['answer']}
    assert schema['properties']['status']['enum']==['insufficient_data']
    for field in ('evidence','metrics','recommendations','assumptions','limitations','next_actions'):
        assert schema['properties'][field]['maxItems']==0
        bad=copy.deepcopy(value);bad[field]=['Ahorro realizado 150 EUR/mes']
        with pytest.raises(ValueError):render_response(bad,[],quantities=q)
    for update in ({'answer':[{'inference':'80 / 200 = 40'}]},
                   {'answer':{'savings_realization':'foreign'}},{'status':'ok'},{'basis':'user_scenario'}):
        with pytest.raises(ValueError):render_response({**value,**update},[],quantities=q)
    changed=catalog(verified='90')
    with pytest.raises(ValueError):savings_realization_answer(value['answer'],changed)


def test_retrieval_or_extra_paragraph_cannot_supply_or_change_user_roles():
    q=catalog();q.classification_question=q.classification_question.split('\n\n')[0]
    assert required_savings_realization(q) is None
    q=catalog();q.classification_question+='\n\nAhorro verificado alternativo 100 EUR/mes.'
    assert required_savings_realization(q) is None


@pytest.mark.parametrize('read_size',[1,7,8192])
@pytest.mark.parametrize('invalid',[False,True])
def test_gateway_review_and_stream_use_closed_terminal_without_weakening_equation_guard(monkeypatch,read_size,invalid):
    import asyncio,time
    from test_chat_auto_jup035 import provider,review_wires,wire
    from app.core.chat_resources import validate_search_call
    q=catalog();value=response(q)
    if invalid:value['answer']=[{'inference':'80 / 200 × 100 = 40'}]
    gateway,requests=provider(monkeypatch,review_wires(wire({'content':json.dumps(value)})),read_size=read_size)
    context={'tool_protocol':'server-documentation-v4','financial_metrics_allowed':False,'authorized_evidence':[],
             'messages':[{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':q.classification_question})}]}
    searches=[]
    async def retrieve(control):
        searches.append(control)
        return {'tool_call_id':validate_search_call(control)[0],
                'content':'{"evidence":[],"omissions":[]}','variable_tokens':0}
    async def exercise():return [r async for r in gateway(context,time.time()+60,tool_result=retrieve)]
    records=asyncio.run(exercise())
    assert len(searches)==1 and len(requests)==2
    assert all('tools' not in request and request['num_retries']==0 for request in requests)
    schema=requests[-1]['response_format']['json_schema']['schema']
    # This closed normal form admits exactly the one structured terminal, not
    # merely the positive example and a couple of rejected alternatives.
    assert schema['properties']['answer']=={
        'type':'object',
        'properties':{'savings_realization':{'type':'string','enum':[response(q)['answer']['savings_realization']]}},
        'required':['savings_realization'],'additionalProperties':False}
    from jsonschema import Draft202012Validator
    answer_validator=Draft202012Validator(schema['properties']['answer'])
    assert answer_validator.is_valid(response(q)['answer'])
    assert not answer_validator.is_valid({'savings_realization':'another-scenario'})
    assert not answer_validator.is_valid([{'inference':'80 / 200 × 100 = 40'}])
    if invalid:
        assert records[-1]['type']=='error' and records[-1]['category']=='invalid_response'
        assert not any(r['type']=='candidate' for r in records)
    else:
        assert records[-1]['type']=='candidate'
        assert records[-1]['result']['answer']==savings_realization_answer(response(q)['answer'],q)
        assert ''.join(r['text'] for r in records if r['type']=='delta')==records[-1]['result']['answer']
        assert records[-1]['usage_report']['complete'] is True
