import copy
import json

import pytest
from app.core.chat_expressions import context_quantities
from app.core.chat_rules import required_zero_percentage
from app.core.chat_segments import render_response
from app.agents.schemas import chat_provider_schema
from app.clients.chat_stream_parser import SegmentAnswerJSON

QUESTION = '¿Qué porcentaje del coste elegible queda sin asignar?\n\nEscenario: total elegible 0 EUR y unallocated 0 EUR.'
FORMULA = 'KPI: Unallocated Cost % = Unallocated Cost / Total Eligible Cost * 100'


def catalog(question=QUESTION, formula=FORMULA):
    source = {'id': 'synthetic:formula', 'kind': 'corpus', 'source': 'synthetic', 'title': 'Synthetic ratio',
        'content': formula, 'provenance': {'document_id': 'synthetic', 'chunk_index': 0, 'sections': [
            {'start': 0, 'end': len(formula), 'document_start': 0, 'section_start': 0, 'section': 'Ratio'}]}}
    return context_quantities({'authorized_evidence': [source], 'messages': [
        {'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})},
        {'content': 'UNTRUSTED_RETRIEVAL_CONTEXT\n' + json.dumps({'evidence': [source]})}]})


def response(q):
    terminal = required_zero_percentage(q)
    return {'answer': {'zero_percentage': terminal['expression']}, 'status': 'insufficient_data',
        **{key: [] for key in ('evidence', 'metrics', 'recommendations', 'assumptions', 'limitations', 'next_actions')}}


def test_zero_ratio_uses_verified_formula_without_needing_threshold_partition():
    q = catalog(); value = response(q); result = render_response(value, [], quantities=q)
    assert 'cociente indefinido porque el denominador es cero' in result['answer']
    assert 'un período con un denominador aplicable' in result['answer']
    assert result['status'] == 'insufficient_data'
    assert [e['id'] for e in result['evidence']] == ['synthetic:formula']
    schema = chat_provider_schema(quantities=q, authorized_evidence=q.authorized_sources, calculations=[])
    assert schema['properties']['answer']['properties']['zero_percentage']['const'] == value['answer']['zero_percentage']
    assert schema['properties']['next_actions']['maxItems'] == 0


@pytest.mark.parametrize('width', [1, 9, 8192])
def test_zero_ratio_stream_matches_final(width):
    q = catalog(); value = response(q); raw = json.dumps(value)
    parser = SegmentAnswerJSON([], quantities=q)
    streamed = ''.join(parser.feed(raw[i:i+width]) for i in range(0, len(raw), width))
    assert streamed == parser.finish() == render_response(value, [], quantities=q)['answer']


@pytest.mark.parametrize('question', [
    QUESTION.replace('total elegible 0', 'total elegible 10'),
    QUESTION.replace('unallocated 0 EUR', 'unallocated 0 USD'),
    QUESTION.replace('unallocated 0 EUR', 'unallocated -2 EUR'),
    QUESTION + ' Otro periodo: total elegible 0 EUR.',
    QUESTION + ' Presupuesto 80 EUR.',
    QUESTION.replace('total elegible', 'non eligible cost'),
    QUESTION.replace('total elegible', 'not total eligible cost'),
    QUESTION.replace('sin asignar?', 'sin asignar y que recomendaciones tienes?'),
    QUESTION.replace('¿Qué porcentaje del coste elegible queda sin asignar?', 'Define porcentaje unallocated.'),
])
def test_zero_ratio_ambiguity_or_other_intent_does_not_force_terminal(question):
    assert required_zero_percentage(catalog(question)) is None


@pytest.mark.parametrize('formula', ['No percentage formula is available.', 'KPI: Unallocated Cost % = Unallocated Cost / All Cost * 100',
    'KPI: Unallocated Cost % = Unallocated Cost / Total Eligible Cost'])
def test_formula_must_be_complete_and_applicable(formula):
    assert required_zero_percentage(catalog(formula=formula)) is None


@pytest.mark.parametrize('field', ['answer', 'limitations', 'status'])
def test_provider_cannot_replace_terminal_or_require_positive_numerator(field):
    q = catalog(); value = response(q)
    if field == 'answer': value[field] = [{'inference': 'The percentage is zero.'}]
    if field == 'limitations': value[field] = [[{'inference': 'Unallocated must be positive.'}]]
    if field == 'status': value[field] = 'ok'
    with pytest.raises(ValueError): render_response(value, [], quantities=q)
