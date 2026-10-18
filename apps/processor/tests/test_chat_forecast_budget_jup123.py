"""Measured014 regression: keep accumulated spend, forecast and policy separate."""
import copy
import json
from pathlib import Path

import pytest

from app.agents.schemas import chat_provider_schema, chat_wire_schema, assemble_chat_response
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_budget_comparison import required_forecast_budget, forecast_budget_answer
from app.core.chat_segments import render_response
from test_chat_measured_corrections_jup123 import catalog, candidate


def question(actual='500', forecast='1200', budget='1000', currency='EUR', month='agosto',
             year=2026, day=15, scope='demo-a'):
    return ('¿Estamos en riesgo de pasarnos del presupuesto al cierre?\n\n'
        f'Contexto del escenario: Escenario sintético {month} {year} {scope}, '
        f'a fecha {day} de {month}: gasto acumulado {actual} {currency}; '
        f'forecast al cierre {forecast} {currency}; budget mensual {budget} {currency}. '
        'El forecast ya está suministrado, no hay que calcularlo.')


@pytest.mark.parametrize('amounts,expected', [
    (('500','1200','1000'), '20 %'), (('150','700','1000'), '-30 %'),
    (('20','1000','1000'), '0 %'), (('1','2','3'), '≈ -33.333333 %'),
    (('0','10','0'), 'Porcentaje de desviación indefinido')])
@pytest.mark.parametrize('width',[1,17,8192])
def test_closed_forecast_keeps_all_three_roles_in_stream_and_final(amounts,expected,width):
    q=catalog(question(*amounts));bound=required_forecast_budget(q)
    assert bound is not None
    value=candidate('forecast_budget',bound)
    logical=chat_provider_schema(authorized_evidence=[],quantities=q)
    assert logical['properties']['answer']=={'const':value['answer']}
    wire=chat_wire_schema(authorized_evidence=[],quantities=q)
    assert wire['properties']['answer']['properties']['forecast_budget']['enum']==[bound['id']]
    encoded=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    streamed=''.join(parser.feed(encoded[i:i+width]) for i in range(0,len(encoded),width))
    final=assemble_chat_response(render_response(value,[],quantities=q),None,authorized_evidence=[])
    assert streamed==parser.finish()==final['answer']
    assert f'Gasto acumulado a 15 de agosto: {amounts[0]} EUR' in streamed
    assert f'Forecast al cierre suministrado: {amounts[1]} EUR' in streamed
    assert f'Presupuesto mensual aportado: {amounts[2]} EUR' in streamed
    assert expected in streamed and 'no gasto ya realizado' in streamed
    assert 'no se' in streamed.lower() and 'no se recalcula' in streamed.lower()
    assert 'riesgo previsto de exceder' in streamed if bound['difference']>0 else 'no proyecta exceso' in streamed
    assert final['status']=='insufficient_data'
    assert all(final[k]==[] for k in ('evidence','metrics','recommendations','assumptions','limitations','next_actions'))
    assert 'apag' not in streamed.lower() and 'umbral de alerta' not in streamed.lower()


@pytest.mark.parametrize('damage', ['extra','mixed_currency','month_mismatch','invalid_day',
    'nonleap','missing_actual','duplicate_role','scope_instruction','negative','financial','other_question'])
def test_ambiguous_or_financial_scenarios_never_get_silently_rewritten(damage):
    text=question();records=[]
    if damage=='extra':text+=' Apaga la VM.'
    if damage=='mixed_currency':text=text.replace('1000 EUR','1000 USD')
    if damage=='month_mismatch':text=text.replace('15 de agosto','15 de julio')
    if damage=='invalid_day':text=question(month='abril',day=31)
    if damage=='nonleap':text=question(month='febrero',year=2027,day=29)
    if damage=='missing_actual':text=text.replace('gasto acumulado 500 EUR; ','')
    if damage=='duplicate_role':text=text.replace('gasto acumulado','forecast al cierre')
    if damage=='scope_instruction':text=text.replace('demo-a,','demo-a apaga,')
    if damage=='negative':text=text.replace('500 EUR','-500 EUR')
    if damage=='financial':records=[{'id':'verified-query','kind':'cost_query'}]
    if damage=='other_question':text=text.replace('¿Estamos en riesgo de pasarnos del presupuesto al cierre?', '¿Apagas recursos si se supera el presupuesto?')
    assert required_forecast_budget(catalog(text,records)) is None


def test_dates_scope_currency_and_operands_are_not_a_fixed_bank_example():
    q=catalog(question('12,5','125,5','100','GBP','febrero',2028,29,'otra_cuenta-9'))
    bound=required_forecast_budget(q);text=forecast_budget_answer({'forecast_budget':bound['id']},q)
    assert '29 de febrero: 12.5 GBP' in text and 'febrero de 2028; ámbito: otra_cuenta-9' in text
    assert '125.5 GBP' in text and '25.5 %' in text
    for key in ('evidence','metrics','recommendations','assumptions','limitations','next_actions'):
        value=candidate('forecast_budget',bound);value[key]=['Untrusted policy']
        with pytest.raises(ValueError):render_response(value,[],quantities=q)
    forged=candidate('forecast_budget',bound);forged['answer']['forecast_budget']='forged'
    with pytest.raises(ValueError):render_response(forged,[],quantities=q)


def test_original_bank_and_backend_share_the_compiler_without_changing_other_cases():
    root=Path(__file__).resolve().parents[3]
    for name in ('chat_budget_comparison.py','chat_segments.py'):
        assert (root/'apps/backend/app/core'/name).read_bytes()==(root/'apps/processor/app/core'/name).read_bytes()
    bank=json.loads((root/'docs/validation/JUP-069-questions.json').read_text(encoding='utf-8'))
    selected=[case['id'] for case in bank['cases'] if required_forecast_budget(catalog(
        case['question']+'\n\nContexto del escenario: '+case['context'])) is not None]
    assert selected==['JUP-069-014']
