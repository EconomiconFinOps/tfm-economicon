"""Separate unit economics from spend, and expose conditional sizing risk."""
import copy
import json
from pathlib import Path

import pytest

from app.agents.schemas import assemble_chat_response, chat_provider_schema
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_documentary_decisions import required_documentary_answer
from app.core.chat_segments import render_response
from app.core.chat_unit_cost import required_unit_cost
from test_chat_measured_corrections_jup123 import catalog, candidate
from test_chat_policy_sections_jup123 import sources


def comparison(first='1000 EUR y 100 pedidos', second='1200 EUR y 200 pedidos', unit='pedidos'):
    return ('¿El incremento de gasto significa que somos menos eficientes?\n\n'
            'Escenario sintético con periodos completos y comparables: '
            f'julio {first}; agosto {second}. Definir coste unitario = gasto / {unit}.')


POLICY = ('## Azure Advisor, Rightsizing Y Commitments '
          'Azure Advisor puede ser una fuente de seniales, pero no una orden automatica. '
          'Antes de aplicar rightsizing hay que validar CPU, memoria, I/O, picos, SLA, crecimiento esperado y restricciones de negocio. '
          'Un commitment es un compromiso financiero a cambio de descuento, como Reservations o Savings Plans. '
          'Antes de comprar commitments conviene aplicar rightsizing y confirmar una base de uso estable.')
SIZING = ('¿Reducimos ya el tamaño de esta VM para ahorrar?\n\n'
          'Escenario sintético: CPU media 5%, sin datos de memoria, I/O, picos ni SLA; coste 300 EUR/mes. '
          'No existe recomendación validada ni medición de ahorro.')


def rendered(question, records=(), width=17):
    records = list(records)
    q = catalog(question, records)
    bound = required_unit_cost(q) or required_documentary_answer(q)
    assert bound is not None
    key = 'unit_cost' if required_unit_cost(q) else 'documentary_answer'
    value = candidate(key, bound)
    schema = chat_provider_schema(authorized_evidence=records, quantities=q)
    assert schema['properties']['answer'] == {'const': value['answer']}
    wire = json.dumps(value)
    parser = SegmentAnswerJSON([], quantities=q)
    streamed = ''.join(parser.feed(wire[i:i+width]) for i in range(0, len(wire), width))
    final = assemble_chat_response(render_response(value, [], quantities=q), None, authorized_evidence=records)
    assert streamed == parser.finish() == final['answer']
    assert final['metrics'] == final['recommendations'] == []
    assert final['status'] == 'insufficient_data'
    return final


@pytest.mark.parametrize('width', [1, 17, 8192])
def test_measured_mislabel_cannot_reappear_in_stream_or_final(width):
    answer = rendered(comparison(), width=width)['answer']
    assert 'julio: gasto 1000 EUR; volumen 100 pedidos. Coste unitario = 10 EUR/pedidos' in answer
    assert 'agosto: gasto 1200 EUR; volumen 200 pedidos. Coste unitario = 6 EUR/pedidos' in answer
    assert 'gasto total (segundo menos primero) = 200 EUR' in answer
    assert 'gasto total sobre el primer período = 20 %' in answer
    assert 'coste unitario (segundo menos primero) = -4 EUR/pedidos' in answer
    assert 'coste unitario sobre el primer período = -40 %' in answer
    assert 'coste por unidad disminuye' in answer


@pytest.mark.parametrize('a,b,unit,expected', [
    ('900 USD y 90 operaciones', '1200 USD y 60 operaciones', 'operaciones', 'coste unitario sobre el primer período = 100 %'),
    ('10 GBP y 5 usuarios', '20 GBP y 10 usuarios', 'usuarios', 'coste unitario sobre el primer período = 0 %'),
    ('1 CHF y 3 unidades', '1 CHF y 4 unidades', 'unidades', 'coste unitario sobre el primer período = -25 %'),
    ('0 CAD y 10 transacciones', '50 CAD y 20 transacciones', 'transacciones', 'coste unitario inicial es cero'),
    ('100 AUD y 0 pedidos', '200 AUD y 10 pedidos', 'pedidos', 'No se calcula la variación del coste unitario'),
    ('100 JPY y 10 pedidos', '200 JPY y 0 pedidos', 'pedidos', 'Coste unitario indefinido'),
    ('1 EUR y 3 pedidos', '2 EUR y 3 pedidos', 'pedidos', 'Coste unitario ≈ 0.333333'),
    ('0.000000000001 EUR y 1 pedidos', '1 EUR y 1 pedidos', 'pedidos', 'gasto 0.000000000001 EUR'),
])
def test_values_units_ratios_rounding_and_undefined_domains(a, b, unit, expected):
    assert expected in rendered(comparison(a, b, unit))['answer']


@pytest.mark.parametrize('old,new', [
    ('completos y comparables', 'parciales'), ('1200 EUR', '1200 USD'),
    ('200 pedidos', '200 usuarios'), ('gasto / pedidos', 'pedidos / gasto'),
    ('agosto', 'julio'), ('1000 EUR', '-1000 EUR'), ('100 pedidos', '100'),
    ('1000 EUR', '1000000000001 EUR'), ('significa que somos menos eficientes?', 'no implica ineficiencia?'),
    ('Definir coste unitario', 'No definir coste unitario'),
    ('agosto 1200', 'agosto parcial 1200'),
])
def test_incomplete_or_ambiguous_inputs_do_not_compile(old, new):
    assert required_unit_cost(catalog(comparison().replace(old, new))) is None


@pytest.mark.parametrize('question', [comparison()+' Además apaga la VM.', comparison()+'\n\nOtra petición.'])
def test_extra_instructions_are_not_discarded(question):
    assert required_unit_cost(catalog(question)) is None


@pytest.mark.parametrize('damage', ['id', 'status', 'basis', 'answer', 'metrics', 'evidence', 'recommendations', 'next_actions'])
def test_metric_terminal_cannot_be_replaced_by_correct_numbers_with_wrong_captions(damage):
    q = catalog(comparison()); value = candidate('unit_cost', required_unit_cost(q))
    if damage == 'id': value['answer']['unit_cost'] = 'forged'
    elif damage == 'status': value['status'] = 'ok'
    elif damage == 'basis': value['basis'] = 'user_scenario'
    elif damage == 'answer': value['answer'] = [{'inference': 'El coste unitario aumenta 20 %.'}]
    else: value[damage] = ['Ahorro garantizado.']
    with pytest.raises(ValueError): render_response(value, [], quantities=q)


@pytest.mark.parametrize('width', [1, 17, 8192])
def test_rightsizing_risk_is_conditional_and_supported_by_complete_policy(width):
    records = sources(POLICY, 'Azure Advisor, Rightsizing Y Commitments')
    result = rendered(SIZING, records, width)
    assert result['evidence'] and result['next_actions']
    assert 'podría degradar el rendimiento o el servicio y comprometer el SLA' in result['answer']
    assert 'no una degradación observada' in result['answer'] and 'no equivale siempre a reducir' in result['answer']
    assert 'no se garantiza ni se cuantifica ahorro' in result['answer']
    assert 'crecimiento esperado y restricciones de negocio' in result['answer']
    assert 'No se ejecuta ningún cambio' in result['answer']


@pytest.mark.parametrize('change', ['exception', 'missing', 'changed', 'unauthorized', 'absent'])
def test_sizing_does_not_cherry_pick_incomplete_or_changed_policies(change):
    body = POLICY
    if change == 'exception': body += ' Excepción: reducir sin validar en demo.'
    if change == 'changed': body = body.replace('hay que validar', 'no es necesario validar')
    records = sources(body, 'Azure Advisor, Rightsizing Y Commitments')
    if change == 'missing': records = records[1:]
    if change == 'absent': records = []
    q = catalog(SIZING, records)
    if change == 'unauthorized':
        q.authorized_sources = []
        with pytest.raises(ValueError): required_documentary_answer(q)
    else: assert required_documentary_answer(q) is None


@pytest.mark.parametrize('question', [
    SIZING.replace('5%', '101%'), SIZING.replace('sin datos', 'con datos'),
    SIZING.replace('No existe recomendación', 'Existe recomendación'),
    SIZING.replace('Reducimos ya', 'No reducimos'), SIZING+' Apaga la VM.',
    SIZING.replace('para ahorrar?', 'para ahorrar? Después compra una reserva.'),
])
def test_changed_or_negated_sizing_requests_are_not_reinterpreted(question):
    assert required_documentary_answer(catalog(question, sources(POLICY, 'Azure Advisor, Rightsizing Y Commitments'))) is None


def test_full_question_binding_and_financial_authority():
    original = catalog(comparison()); other = catalog(comparison().replace('1000 EUR', '900 EUR'))
    with pytest.raises(ValueError): render_response(candidate('unit_cost', required_unit_cost(original)), [], quantities=other)
    assert required_unit_cost(catalog(comparison(), [{'id': 'real', 'kind': 'cost_query'}])) is None
    assert required_documentary_answer(catalog(SIZING, [{'id': 'real', 'kind': 'cost_query'}])) is None
