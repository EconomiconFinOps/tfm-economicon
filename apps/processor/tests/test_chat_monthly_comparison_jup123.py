"""Measured002 regression: monthly arithmetic cannot append documentary method."""
import json
from pathlib import Path

import pytest

from app.agents.schemas import chat_provider_schema,chat_wire_schema,assemble_chat_response
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_cost_breakdown import required_monthly_comparison,monthly_comparison_answer
from app.core.chat_segments import render_response
from test_chat_measured_corrections_jup123 import catalog,candidate


def question(baseline='800',current='1000',currency='EUR',year=2026,
             first='julio',second='agosto',scope='demo-a',basis='actual',reverse=False):
    fields=[f'{first} {baseline} {currency}',f'{second} {current} {currency}']
    if reverse:fields.reverse()
    return (f'¿Cuánto subió el gasto entre {first} y {second}?\n\nContexto del escenario: '
        f'Escenario sintético, mismo alcance {scope} y meses completos de {year}: '
        +'; '.join(fields)+f' de coste {basis}.')


@pytest.mark.parametrize('baseline,current,expected',[
    ('800','1000','25 %'),('1000','800','-20 %'),('100','100','0 %'),
    ('3','4','≈ 33.333333 %'),('0','10','Variación relativa indefinida')])
@pytest.mark.parametrize('width',[1,17,8192])
def test_monthly_terminal_owns_roles_percent_and_all_public_fields(baseline,current,expected,width):
    q=catalog(question(baseline,current));bound=required_monthly_comparison(q)
    assert bound is not None
    value=candidate('monthly_comparison',bound)
    assert chat_provider_schema(authorized_evidence=[],quantities=q)['properties']['answer']=={'const':value['answer']}
    assert chat_wire_schema(authorized_evidence=[],quantities=q)['properties']['answer']['properties']['monthly_comparison']['enum']==[bound['id']]
    raw=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    stream=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    final=assemble_chat_response(render_response(value,[],quantities=q),None,authorized_evidence=[])
    assert stream==parser.finish()==final['answer']
    assert f'Baseline de julio: {baseline} EUR' in stream and f'Gasto de agosto: {current} EUR' in stream
    assert expected in stream
    if bound['relative'] is not None:assert 'sobre julio' in stream
    assert 'método documentado' not in stream and 'resource group' not in stream
    assert all(final[k]==[] for k in ('evidence','metrics','recommendations','assumptions','limitations','next_actions'))
    assert final['status']=='insufficient_data'


@pytest.mark.parametrize('damage',['mixed','missing_month','duplicate','different_month','missing_year',
    'partial_month','extra_instruction','negative','financial','unknown_question'])
def test_unknown_or_incomparable_months_keep_the_general_route(damage):
    text=question();records=[]
    if damage=='mixed':text=text.replace('1000 EUR','1000 USD')
    if damage=='missing_month':text=text.replace('julio 800 EUR; ','')
    if damage=='duplicate':text=text.replace('agosto 1000','julio 1000')
    if damage=='different_month':text=text.replace('agosto 1000','septiembre 1000')
    if damage=='missing_year':text=text.replace(' de 2026','')
    if damage=='partial_month':text=text.replace('meses completos','meses parciales')
    if damage=='extra_instruction':text+=' Apaga una VM.'
    if damage=='negative':text=text.replace('800 EUR','-800 EUR')
    if damage=='financial':records=[{'id':'verified-query','kind':'cost_query'}]
    if damage=='unknown_question':text=text.replace('¿Cuánto subió el gasto entre julio y agosto?','¿Cuál fue la causa del incremento?')
    assert required_monthly_comparison(catalog(text,records)) is None


def test_values_months_currency_basis_and_field_order_are_not_fixed():
    q=catalog(question('2,5','5','CHF',2029,'enero','marzo','otra-7','amortizado',True))
    bound=required_monthly_comparison(q);answer=monthly_comparison_answer({'monthly_comparison':bound['id']},q)
    assert 'Baseline de enero: 2.5 CHF' in answer and 'Gasto de marzo: 5 CHF' in answer
    assert '100 %' in answer and '2029; coste amortizado' in answer and 'otra-7' in answer
    for key in ('evidence','metrics','recommendations','assumptions','limitations','next_actions'):
        value=candidate('monthly_comparison',bound);value[key]=['Invented method']
        with pytest.raises(ValueError):render_response(value,[],quantities=q)
    value=candidate('monthly_comparison',bound);value['answer']['monthly_comparison']='forged'
    with pytest.raises(ValueError):render_response(value,[],quantities=q)


@pytest.mark.parametrize('request_text',['¿Cómo cambió el gasto entre enero y marzo?',
                                  'Calcula la variación del gasto entre enero y marzo.'])
def test_request_variants_preserve_explicit_period_roles(request_text):
    text=question(first='enero',second='marzo').split('\n\n',1)[1]
    bound=required_monthly_comparison(catalog(request_text+'\n\n'+text))
    assert bound is not None and bound['baseline_month']=='enero' and bound['current_month']=='marzo'


def test_bank_selection_and_shared_backend_compiler():
    root=Path(__file__).resolve().parents[3]
    assert (root/'apps/backend/app/core/chat_cost_breakdown.py').read_bytes()==(root/'apps/processor/app/core/chat_cost_breakdown.py').read_bytes()
    bank=json.loads((root/'docs/validation/JUP-069-questions.json').read_text(encoding='utf-8'))
    assert [c['id'] for c in bank['cases'] if required_monthly_comparison(catalog(c['question']+'\n\nContexto del escenario: '+c['context'])) is not None]==['JUP-069-002']
