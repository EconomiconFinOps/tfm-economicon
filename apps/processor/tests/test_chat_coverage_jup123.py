import copy
import json

import pytest

from app.core.chat_budget_comparison import explicit_comparison, comparison_text
from app.core.chat_expressions import context_quantities
from app.core.chat_segments import render_response
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.agents.schemas import chat_provider_schema


def catalog(text, sources=()):
    return context_quantities({'messages':[{'role':'user','content':
        'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':text})}],
        'authorized_evidence':list(sources)})


def scenario(fields='forecast al cierre 1200 EUR; budget mensual 1000 EUR'):
    return '¿Hay riesgo de superar el presupuesto?\n\nEscenario: gasto acumulado 500 EUR; '+fields+'.'


def candidate(answer):
    return {'basis':'user_scenario','status':'insufficient_data','answer':answer,
            'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],
            'limitations':[],'next_actions':[]}


@pytest.mark.parametrize('fields,difference,relative',[
    ('forecast al cierre 1200 EUR; budget mensual 1000 EUR','200','20'),
    ('presupuesto: 200 GBP; forecast: 150 GBP','-50','-25'),
    ('forecast 500,5 USD; budget 500 USD','0.5','0.100'),
    ('forecast 100 EUR; presupuesto 100 EUR','0','0'),
])
def test_adjacent_explicit_roles_compute_the_whole_comparison(fields,difference,relative):
    bound=explicit_comparison(catalog(scenario(fields)))
    assert str(bound['difference'])==difference
    assert bound['relative']==__import__('decimal').Decimal(relative)
    assert len(bound['source_spans'])==2 and len(bound['question_sha256'])==64


@pytest.mark.parametrize('fields',[
    'forecast 1200 EUR; budget 1000 USD',
    'forecast 1200 EUR; budget 0 EUR',
    'forecast 1200 EUR; budget -10 EUR',
    'forecast 1200 EUR; forecast 1300 EUR; budget 1000 EUR',
    'forecast de julio 1200 EUR; budget de agosto 1000 EUR',
    'no hay forecast 1200 EUR; budget 1000 EUR',
    'forecast 1200 EUR; en otra suscripcion budget 1000 EUR',
    'forecast 1200 EUR; budget 1000 EUR/día',
    'forecast 1200 EUR; budget 1000 EUR para otro periodo',
])
def test_ambiguous_or_incompatible_operands_do_not_enter_the_comparison(fields):
    assert explicit_comparison(catalog(scenario(fields))) is None


def test_corpus_or_financial_observations_do_not_become_hypothetical_user_facts():
    q=catalog('¿Qué es un presupuesto?')
    q.authorized_sources=[{'kind':'corpus','content':'forecast 1200 EUR; budget 1000 EUR'}]
    assert comparison_text(q)==''
    q=catalog(scenario(),[{'id':'verified','kind':'cost_query'}])
    assert comparison_text(q)==''


@pytest.mark.parametrize('width',[1,7,8192])
@pytest.mark.parametrize('basis_first',[True,False])
def test_missing_relative_calculation_is_server_owned_in_stream_and_final(width,basis_first):
    q=catalog(scenario())
    keys={entry['value']:key for key,entry in q.items() if entry['unit']=='EUR'}
    # Reproduce the relevant omission: the model emits the forecast/budget
    # ratio, but no relative_change expression for the excess.
    value=candidate([{'expression':{'operation':'percentage',
        'numerator':{'quantity':keys['1200']},'denominator':{'quantity':keys['1000']}}},
        {'inference':'El forecast indica un riesgo al cierre, no un gasto ya realizado.'}])
    if not basis_first:value['basis']=value.pop('basis')
    raw=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    stream=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    result=render_response(value,[],quantities=q)
    assert stream==parser.finish()==result['answer']
    assert '200 EUR' in stream and 'desviación relativa respecto al presupuesto: 20 %' in stream
    assert '120 %' in stream and 'no gasto realizado' in stream
    assert result['status']=='insufficient_data' and result['evidence']==result['metrics']==[]


SOURCE={'id':'method','kind':'corpus','title':'Método','source':'guide',
        'content':'Confirmar ámbito y periodo. Agrupar por servicio y recurso.'}


@pytest.mark.parametrize('width',[1,7,8192])
def test_repeated_literal_selections_do_not_overflow_or_change_stream_parity(width):
    q=catalog('¿Cómo se investiga?', [SOURCE])
    first={'documentary':{'source_id':'method','passage':'Confirmar ámbito y periodo.'}}
    second={'documentary':{'source_id':'method','passage':'Agrupar por servicio y recurso.'}}
    value=candidate([first]*100+[second]);value.update(basis='authorized_evidence',status='ok')
    # The original public/renderer bounds remain compatible; the new request
    # grammar separately limits generation to24 blocks to bound repetition.
    value['limitations']=[[copy.deepcopy(first)]]
    raw=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    stream=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    result=render_response(value,[],quantities=q)
    assert stream==parser.finish()==result['answer']
    assert stream.count('Confirmar ámbito y periodo.')==1
    assert 'Agrupar por servicio y recurso.' in stream and len(stream)<4000
    assert result['limitations'][0] and len(result['evidence'])==1
    value['answer'].append({'documentary':{'source_id':'method','passage':'Inventado.'}})
    with pytest.raises(ValueError):render_response(value,[],quantities=q)


def test_request_grammar_has_a_bounded_main_answer_without_losing_short_field_limits():
    schema=chat_provider_schema(authorized_evidence=[SOURCE])
    for branch in schema['anyOf']:
        assert branch['properties']['answer']['maxItems']==24
        assert branch['properties']['limitations']['items']['maxItems']==1
