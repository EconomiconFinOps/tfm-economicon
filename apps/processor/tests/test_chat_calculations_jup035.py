"""General arithmetic/control/streaming regressions, no acceptance-bank fixtures."""
import asyncio
import json
import time
from pathlib import Path

import pytest

from app.core.chat_calculations import calculate, CalculationStream, render_text
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
    plan=[step(),step('@0','20','percentage')]
    comparisons=[step('@0','73','lt'),step('20','20','gt'),step('20','20','gte')]
    result=calculate(context(),plan,comparisons)
    assert [r['value'] for r in result]==['53','265','verdadero','falso','verdadero']
    assert [r['id'] for r in result]==['n:0','n:1','c:0','c:1','c:2']
    assert result[0]['equation']=='73 EUR − 20 EUR = 53 EUR'
    assert result[1]['unit']=='%' and all(r['hypothetical'] for r in result)
    decimal=calculate(context('0,1 EUR y 0,2 EUR.'),[step('0.1','0.2','add')])
    assert decimal[0]['value']=='0.3'


@pytest.mark.parametrize('numeric,comparisons',[
    ([step('20','20','eq')],[]),
    ([],[step()]),
    ([],[step('@0','20','eq')]),
    ([step()],[step('@1','20','eq')]),
    ([step()],[step('20','20','eq'),step('@1','20','eq')]),
    ([step()]*6,[step('20','20','eq')]*7),
    ([step()], [{'left':{'ref':True},'right':{'literal':'20','unit':'EUR'},'operator':'eq'}]),
])
def test_terminal_comparisons_cannot_enter_numeric_reference_graph(numeric,comparisons):
    with pytest.raises(ValueError):calculate(context(),numeric,comparisons)






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
        step('1','3','divide','','')],[step('@0','0.333333','gt','','')])
    assert result[0]['equation']=='1 / 3 ≈ 0.333333'
    assert result[1]['value']=='verdadero'


@pytest.mark.parametrize('text',['500 − 100 = 100','73 - 20 = 90',
    '500 EUR − 100 EUR = 100 EUR','**500 EUR** − **100 EUR** = **100 EUR**',
    '73 x 20 = 90','73 ÷ 20 = 90','20 EUR > 20 EUR = verdadero',
    '[[calc:99]]','[[calc:0','[[calc:abc]]'])
def test_free_equations_and_bad_slots_are_never_repaired(text):
    with pytest.raises(ValueError):render_text(text,calculate(context(),[step()]))








def test_decimal_point_at_fragment_boundary_does_not_bypass_equation_rejection():
    stream=CalculationStream([])
    assert stream.feed('Hipotético: 0.')==''
    with pytest.raises(ValueError):stream.feed('1 + 0.2 = 0.9. ',final=True)


def test_small_operands_remain_exact_when_result_is_rounded():
    result=calculate(context('0.0000004 EUR'),[step('0.0000004','0.0000004','add')])
    assert result[0]['equation']=='0.0000004 EUR + 0.0000004 EUR ≈ 0.000001 EUR'


def test_long_tail_without_sentence_boundary_respects_wire_limit(monkeypatch):
    from test_chat_gateway_jup035 import supported_provider, SOURCE
    value=supported_provider();value['answer']=[{'text':'😀'*2400}]
    gateway,_=provider(monkeypatch,[wire({'content':json.dumps(value)})],read_size=100000)
    import threading
    records=list(gateway._records({'messages':[],'financial_metrics_allowed':False,'authorized_evidence':[SOURCE]},
        time.time()+60,{},threading.Event(),'none'))
    assert records[-1]['type']=='candidate'
    deltas=[record['text'] for record in records if record['type']=='delta']
    assert len(deltas)>1 and all(len(text.encode())<=8192 for text in deltas)
    assert ''.join(deltas)==records[-1]['result']['answer']==value['answer'][0]['text']


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


def test_gateway_assembly_diagnostic_uses_only_closed_messages(caplog):
    from app.clients.chat_gateway import _record_diagnostic
    _record_diagnostic('model_validation',ValueError('Citation passage is not grounded.'),'a'*64,'stop')
    assert json.loads(caplog.records[-1].message)['rule_code']=='citation_passage_not_grounded'
    _record_diagnostic('model_validation',ValueError('sensitive unknown input'),'a'*64,'stop')
    assert 'rule_code' not in json.loads(caplog.records[-1].message)
    assert 'sensitive' not in caplog.text


@pytest.mark.parametrize('operand',[{'ref':True},{'ref':-1},{'ref':0,'unit':'EUR'},
    {'literal':'73','unit':'EUR','ref':0},{'literal':'73'},{'ref':'0'}])
def test_typed_reference_rejects_extra_units_mixed_branches_and_invalid_indices(operand):
    plan=[step(),{'left':operand,'right':{'literal':'20','unit':'EUR'},'operator':'subtract'}]
    with pytest.raises(ValueError):calculate(context(),plan)
