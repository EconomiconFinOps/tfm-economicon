"""General arithmetic/control/streaming regressions, no acceptance-bank fixtures."""
import asyncio
import json
import time
from pathlib import Path

import pytest

from app.core.chat_calculations import calculate, CalculationStream, render_text
from app.core.chat_resources import validate_decision, validate_search_call, continuation_messages
from test_chat_auto_jup035 import provider, wire
from test_chat_gateway_jup035 import ANSWER, _provider


def step(left='73',right='20',operator='subtract',left_unit='EUR',right_unit='EUR'):
    def operand(value,unit):
        return {'ref':int(value[1:])} if value.startswith('@') else {'literal':value,'unit':unit}
    return dict(left=operand(left,left_unit),right=operand(right,right_unit),operator=operator)


def context(question='Ejemplo hipotético: 73 EUR frente a 20 EUR.'):
    return {'messages':[{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})}],
            'tool_protocol':'structured-documentation-v3','financial_metrics_allowed':False,'authorized_evidence':[]}


def test_server_and_processor_arithmetic_are_identical():
    base=Path(__file__).resolve().parents[2]
    assert (base/'backend/app/core/chat_calculations.py').read_bytes()==(base/'processor/app/core/chat_calculations.py').read_bytes()


def test_decimal_operations_and_references_keep_units_and_strict_boundaries():
    plan=[step(),step('@0','20','percentage'),step('@0','73','lt'),step('20','20','gt'),step('20','20','gte')]
    result=calculate(context(),plan)
    assert [r['value'] for r in result]==['53','265','verdadero','falso','verdadero']
    assert result[0]['equation']=='73 EUR − 20 EUR = 53 EUR'
    assert result[1]['unit']=='%' and all(r['hypothetical'] for r in result)
    decimal=calculate(context('0,1 EUR y 0,2 EUR.'),[step('0.1','0.2','add')])
    assert decimal[0]['value']=='0.3'


def test_cost_per_count_ratios_preserve_dimensions_and_support_comparison():
    initial=context('Ejemplo: 84 EUR para 7 operaciones; 65 EUR para 13 operaciones.')
    plan=[step('84','7','divide','EUR','operaciones'),
          step('65','13','divide','EUR','operaciones'),
          step('@0','@1','subtract','EUR/operaciones','EUR/operaciones'),
          step('@2','@0','percentage','EUR/operaciones','EUR/operaciones')]
    result=calculate(initial,plan)
    assert [item['value'] for item in result]==['12','5','7','58.333333']
    assert result[0]['unit']==result[1]['unit']=='EUR/operaciones'
    with pytest.raises(ValueError,match='Currency conversion'):
        calculate(context('84 EUR y 7 USD.'),[step('84','7','divide','EUR','USD')])


@pytest.mark.parametrize('plan,question', [
    ([step('99')],'73 EUR y 20 EUR'),
    ([step('73','0','divide')],'73 EUR y 0 EUR'),
    ([step('73','20','add','EUR','USD')],'73 EUR y 20 USD'),
    ([step('73','20','multiply')],'73 EUR y 20 EUR'),
    ([step('@0')],'73 EUR y 20 EUR'),
    ([step('1e9')],'1000000000 EUR y 20 EUR'),
    ([step('1'*13)],'73 EUR y 20 EUR'),
    ([step()]*13,'73 EUR y 20 EUR'),
    ([step('73','20','__import__')],'73 EUR y 20 EUR'),
    ([step('73','20','subtract','USD','USD')],'73 EUR y 20 EUR'),
    ([step('999999999999','999999999999','multiply','','')],'999999999999'),
    ([step('20','20','eq'),step('@0','20')],'20 EUR'),
])
def test_invalid_or_unfunded_plans_fail_closed(plan,question):
    with pytest.raises(ValueError):calculate(context(question),plan)


def test_rounding_is_explicit_and_comparison_uses_unrounded_decimal():
    result=calculate(context('1 y 3 y 0.333333'),[
        step('1','3','divide','',''),step('@0','0.333333','gt','','')])
    assert result[0]['equation']=='1 / 3 ≈ 0.333333'
    assert result[1]['value']=='verdadero'


@pytest.mark.parametrize('text',['500 − 100 = 100','73 - 20 = 90',
    '500 EUR − 100 EUR = 100 EUR','**500 EUR** − **100 EUR** = **100 EUR**',
    '73 x 20 = 90','73 ÷ 20 = 90','20 EUR > 20 EUR = verdadero',
    '[[calc:99]]','[[calc:0','[[calc:abc]]'])
def test_free_equations_and_bad_slots_are_never_repaired(text):
    with pytest.raises(ValueError):render_text(text,calculate(context(),[step()]))


@pytest.mark.parametrize('width',[1,2,7,8192])
def test_stream_fragmentation_unicode_escape_and_persistable_final_match(monkeypatch,width):
    computations=calculate(context(),[step()])
    value=_provider(ANSWER)
    value['answer']='Hipotético 😀: [[calc:0]]. La diferencia está calculada.'
    value['assumptions']=['Datos del usuario: [[calc:0]].']
    event={'choices':[{'index':0,'delta':{'content':json.dumps(value,ensure_ascii=False)},'finish_reason':'stop'}]}
    data=('data: '+json.dumps(event,ensure_ascii=False)+'\n\ndata: [DONE]\n\n').encode()
    gateway,_=provider(monkeypatch,[data],read_size=width)
    async def exercise():
        return [r async for r in gateway({**context(),'tool_protocol':None,'calculations':computations},time.time()+60)]
    records=asyncio.run(exercise())
    result=records[-1]['result']
    assert records[-1]['type']=='candidate'
    assert ''.join(r['text'] for r in records if r['type']=='delta')==result['answer']
    assert result['answer']=='Hipotético 😀: 73 EUR − 20 EUR = 53 EUR. La diferencia está calculada.'
    assert '[[calc:' not in json.dumps(records) and result['metrics']==[]


def test_none_with_calculation_uses_authenticated_extension_without_search(monkeypatch):
    decision={'action':'none','query':None,'calculations':[step()]}
    assert validate_decision(decision)==decision
    candidate=_provider(ANSWER);candidate['answer']='Hipotético: [[calc:0]].'
    gateway,requests=provider(monkeypatch,[wire({'content':json.dumps(decision)}),wire({'content':json.dumps(candidate)})])
    initial=context();calls=[]
    async def result(value):
        calls.append(value)
        content=json.dumps({'evidence':[],'omissions':[],'calculations':calculate(initial,value['calculations'])})
        return {'tool_call_id':validate_search_call(value)[0],'content':content,'variable_tokens':0}
    async def exercise():
        return [r async for r in gateway(initial,time.time()+60,tool_result=result)]
    records=asyncio.run(exercise())
    assert calls==[decision] and len(requests)==2
    assert records[-1]['type']=='candidate' and records[-1]['result']['evidence']==[]
    assert requests[1]['messages'][-1]['content'].startswith('UNTRUSTED_RETRIEVAL_CONTEXT\n')


def test_authenticated_result_arithmetic_cannot_be_tampered():
    initial=context();decision={'action':'none','query':None,'calculations':[step()]}
    computed=calculate(initial,decision['calculations']);computed[0]['value']='90'
    result={'tool_call_id':validate_search_call(decision)[0],'variable_tokens':0,
            'content':json.dumps({'evidence':[],'omissions':[],'calculations':computed})}
    with pytest.raises(ValueError,match='Calculation result mismatch'):continuation_messages(initial,decision,result)


def test_decimal_point_at_fragment_boundary_does_not_bypass_equation_rejection():
    stream=CalculationStream([])
    assert stream.feed('Hipotético: 0.')==''
    with pytest.raises(ValueError):stream.feed('1 + 0.2 = 0.9. ',final=True)


def test_small_operands_remain_exact_when_result_is_rounded():
    result=calculate(context('0.0000004 EUR'),[step('0.0000004','0.0000004','add')])
    assert result[0]['equation']=='0.0000004 EUR + 0.0000004 EUR ≈ 0.000001 EUR'


def test_long_tail_without_sentence_boundary_respects_wire_limit(monkeypatch):
    value=_provider(ANSWER);value['answer']='😀'*2400
    gateway,_=provider(monkeypatch,[wire({'content':json.dumps(value)})],read_size=100000)
    import threading
    records=list(gateway._records({'messages':[],'financial_metrics_allowed':False},
        time.time()+60,{},threading.Event(),'none'))
    assert records[-1]['type']=='candidate'
    deltas=[record['text'] for record in records if record['type']=='delta']
    assert len(deltas)>1 and all(len(text.encode())<=8192 for text in deltas)
    assert ''.join(deltas)==records[-1]['result']['answer']==value['answer']


def test_sentence_punctuation_is_not_a_grouped_numeric_literal():
    assert calculate(context('Calcula 73 menos 20.'),[step('73','20','subtract','','')])[0]['value']=='53'
    with pytest.raises(ValueError,match='literal absent'):
        calculate(context('Agrupado ambiguo 1.234.567 y 20.'),[step('1.234','20','subtract','','')])


def test_hyphenated_identifier_is_not_a_numeric_operand():
    assert calculate(context('73, luego 20.'),[step('73','20','subtract','','')])[0]['value']=='53'
    with pytest.raises(ValueError,match='literal absent'):
        calculate(context('cost-73-item y 20.'),[step('73','20','subtract','','')])


def test_gateway_calculation_diagnostic_exposes_closed_rule_only(caplog):
    from app.clients.chat_gateway import _record_diagnostic
    from app.core.chat_calculations import CalculationError
    _record_diagnostic('finish', CalculationError('sensitive rejected operand'), 'a'*64, 'stop')
    value=json.loads(caplog.records[-1].message)
    assert value['rule_code']=='calculation_invalid'
    assert value['exception_class']=='CalculationError'
    assert 'sensitive' not in caplog.text


@pytest.mark.parametrize('operand',[{'ref':True},{'ref':-1},{'ref':0,'unit':'EUR'},
    {'literal':'73','unit':'EUR','ref':0},{'literal':'73'},{'ref':'0'}])
def test_typed_reference_rejects_extra_units_mixed_branches_and_invalid_indices(operand):
    plan=[step(),{'left':operand,'right':{'literal':'20','unit':'EUR'},'operator':'subtract'}]
    with pytest.raises(ValueError):calculate(context(),plan)
