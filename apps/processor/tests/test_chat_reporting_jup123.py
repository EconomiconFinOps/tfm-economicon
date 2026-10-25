import copy
import json
import pytest
from app.core.chat_expressions import context_quantities
from app.core.chat_reporting import required_reporting
from app.core.chat_segments import render_response
from app.clients.chat_stream_parser import SegmentAnswerJSON

POLICY = ('## Showback Y Chargeback **Showback** muestra costes asignados a equipos o unidades sin repercusion contable formal. '
          'Es apropiado para el MVP porque mejora visibilidad y accountability sin requerir procesos financieros estrictos. '
          '**Chargeback** repercute el coste formalmente a una unidad responsable. '
          'Debe esperar a que la calidad de allocation sea suficiente.')
QUESTION = ('¿Podemos presentar este reparto como chargeback?\n\nContexto del escenario: '
            'Escenario sintético con costes mostrados por equipo para dar visibilidad, sin repercusión contable formal.')

def catalog(question=QUESTION, policy=POLICY):
    source = {'id': 'policy:1', 'kind': 'corpus', 'source': 'manual', 'title': 'Reporting policy',
              'content': policy, 'provenance': {'document_id': 'policy', 'chunk_index': 0,
              'sections': [{'start': 0, 'end': len(policy), 'section': 'Showback Y Chargeback',
                            'document_start': 0, 'section_start': 0}]}}
    return context_quantities({'authorized_evidence': [source], 'messages': [
        {'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})},
        {'content': 'UNTRUSTED_RETRIEVAL_CONTEXT\n' + json.dumps({'evidence': [source]})}]})

def response(q):
    return {'answer': {'reporting_basis': required_reporting(q)['id']}, 'status': 'ok',
            'evidence': [], 'metrics': [], 'recommendations': [], 'assumptions': [],
            'limitations': [], 'next_actions': []}

@pytest.mark.parametrize('formal,label', [('sin', 'showback'), ('con', 'chargeback')])
@pytest.mark.parametrize('width', [1, 13, 8192])
def test_grounded_reporting_stream_and_final_never_assert_unmeasured_quality(formal, label, width):
    q = catalog(QUESTION.replace('sin repercusión', formal + ' repercusión'))
    value = response(q)
    raw = json.dumps(value)
    parser = SegmentAnswerJSON([], quantities=q)
    streamed = ''.join(parser.feed(raw[i:i+width]) for i in range(0, len(raw), width))
    result = render_response(value, [], quantities=q)
    assert streamed == parser.finish() == result['answer']
    assert 'corresponde a ' + label in streamed
    assert 'no se concluye que sea suficiente ni insuficiente' in streamed
    assert 'no autoriza una repercusión contable' in streamed
    assert result['recommendations'] == []
    assert [item['id'] for item in result['evidence']] == ['policy:1']

@pytest.mark.parametrize('question', [
    QUESTION.replace('sin repercusión', 'no sin repercusión'),
    QUESTION.replace('sin repercusión', 'quizá sin repercusión'),
    QUESTION + ' La calidad es suficiente.',
    QUESTION + ' Otro escenario con repercusión contable formal.',
    QUESTION.replace('costes mostrados', 'no costes mostrados'),
    QUESTION.replace('¿Podemos presentar este reparto como chargeback?', 'Define chargeback y calcula el gasto.'),
])
def test_ambiguous_additional_or_negated_scenarios_retain_general_route(question):
    assert required_reporting(catalog(question)) is None

@pytest.mark.parametrize('policy', [POLICY.replace('repercute el coste', 'no repercute el coste'),
    POLICY.replace('sin repercusion', 'con repercusion'), POLICY[:-30],
    POLICY + ' Esta regla no aplica al MVP.'])
def test_modified_or_partial_policy_cannot_authorize_decision(policy):
    assert required_reporting(catalog(policy=policy)) is None

@pytest.mark.parametrize('field,value', [('answer', {'reporting_basis': 'forged'}),
    ('recommendations', [{'rationale': 'La calidad es insuficiente.'}]),
    ('limitations', [[{'inference': 'La calidad es insuficiente.'}]]), ('status', 'partial')])
def test_provider_cannot_replace_conclusion_or_add_unmeasured_premises(field, value):
    q = catalog(); supplied = response(q); supplied[field] = value
    with pytest.raises(ValueError): render_response(supplied, [], quantities=q)

def test_schema_exposes_only_bound_answer_and_empty_auxiliaries():
    from app.agents.schemas import chat_provider_schema
    q = catalog()
    schema = chat_provider_schema(authorized_evidence=q.authorized_sources, quantities=q)
    assert schema['properties']['answer']['const'] == response(q)['answer']
    assert schema['properties']['recommendations']['maxItems'] == 0
