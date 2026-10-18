import copy
import json

import pytest

from app.core.chat_expressions import context_quantities
from app.core.chat_boolean_rules import required_zero_change
from app.core.chat_segments import render_response
from app.agents.schemas import chat_provider_schema
from app.clients.chat_stream_parser import SegmentAnswerJSON

QUESTION = '¿Qué porcentaje aumentó el gasto?\n\nEscenario: baseline diario 0 EUR; observado 87 EUR; sin historial previo.'


def catalog(question=QUESTION):
    return context_quantities({'messages': [{'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})}]})


def response(q):
    return {'answer': {'zero_change': required_zero_change(q)}, 'status': 'insufficient_data',
            **{key: [] for key in ('evidence', 'metrics', 'recommendations', 'assumptions', 'limitations', 'next_actions')}}


def test_zero_change_returns_absolute_delta_and_requests_comparable_baseline():
    q = catalog(); result = render_response(response(q), [], quantities=q)
    assert 'Diferencia absoluta = 87 EUR/día.' in result['answer']
    assert 'variación relativa indefinida' in result['answer']
    assert 'Necesito una base comparable' in result['answer']
    assert result['evidence'] == [] and result['status'] == 'insufficient_data'
    schema = chat_provider_schema(quantities=q, authorized_evidence=[], calculations=[])
    assert schema['properties']['answer']['properties']['zero_change']['const'] == required_zero_change(q)
    assert schema['properties']['limitations']['maxItems'] == 0


@pytest.mark.parametrize('width', [1, 13, 8192])
def test_zero_change_stream_is_exactly_final_answer(width):
    q = catalog(); value = response(q); raw = json.dumps(value)
    parser = SegmentAnswerJSON([], quantities=q)
    streamed = ''.join(parser.feed(raw[i:i+width]) for i in range(0, len(raw), width))
    assert streamed == parser.finish() == render_response(value, [], quantities=q)['answer']


@pytest.mark.parametrize('question', [
    QUESTION.replace('baseline diario 0', 'baseline diario 2'),
    QUESTION.replace('87 EUR', '87 USD'),
    QUESTION + ' Otro baseline diario 0 EUR.',
    QUESTION + ' Presupuesto: 42 EUR.',
    QUESTION.replace('observado', 'estimado'),
    QUESTION.replace('el gasto?', 'el gasto y que recomendaciones tienes?'),
    QUESTION.replace('el gasto?', 'el gasto? Explica tambien el showback.'),
    QUESTION.replace('¿Qué porcentaje aumentó el gasto?', 'Define variación relativa.'),
    QUESTION.replace('¿Qué porcentaje aumentó el gasto?', 'No calcules el porcentaje de aumento.'),
])
def test_ambiguous_or_unrequested_zero_change_keeps_existing_modes(question):
    assert required_zero_change(catalog(question)) is None


@pytest.mark.parametrize('mutation', ['operand', 'authority', 'auxiliary', 'omission'])
def test_model_cannot_replace_operands_omit_terminal_or_add_claims(mutation):
    q = catalog(); value = response(q)
    if mutation == 'operand': value['answer']['zero_change']['current'] = {'quantity': '0 EUR/día'}
    if mutation == 'authority': value['status'] = 'ok'
    if mutation == 'auxiliary': value['limitations'] = [[{'inference': 'Both amounts must be positive.'}]]
    if mutation == 'omission': value['answer'] = [{'inference': 'No percentage is available.'}]
    with pytest.raises(ValueError): render_response(value, [], quantities=q)


def test_zero_observed_value_remains_valid_and_does_not_require_positive_numerator():
    q = catalog(QUESTION.replace('87 EUR', '0 EUR'))
    assert 'Diferencia absoluta = 0 EUR/día.' in render_response(response(q), [], quantities=q)['answer']
