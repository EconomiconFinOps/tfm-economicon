import json
import pytest
from app.core.chat_expressions import context_quantities
from app.core.chat_missing_spend import required_missing_spend
from app.core.chat_segments import render_response
from app.clients.chat_stream_parser import SegmentAnswerJSON

QUESTION = ('¿El gasto de septiembre es cero?\n\nContexto del escenario: Escenario sintético: '
            'la consulta de septiembre de 2026 devuelve cero registros, pero la ingesta del mes todavía no se ha completado.')

def catalog(question=QUESTION, sources=None):
    return context_quantities({'messages': [{'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})}],
                               'authorized_evidence': sources or []})

def response(q):
    return {'answer': {'missing_spend': required_missing_spend(q)['id']}, 'status': 'insufficient_data',
            'evidence': [], 'metrics': [], 'recommendations': [], 'assumptions': [], 'limitations': [], 'next_actions': []}

@pytest.mark.parametrize('width', [1, 13, 8192])
@pytest.mark.parametrize('month', ['septiembre', 'enero', 'diciembre'])
def test_incomplete_period_remains_unknown_without_decorative_citations(width, month):
    q = catalog(QUESTION.replace('septiembre', month))
    raw = json.dumps(response(q)); parser = SegmentAnswerJSON([], quantities=q)
    streamed = ''.join(parser.feed(raw[i:i+width]) for i in range(0, len(raw), width))
    rendered = render_response(response(q), [], quantities=q)
    assert streamed == parser.finish() == rendered['answer']
    assert f'No se puede concluir que el gasto de {month} de 2026 sea cero' in streamed
    assert 'tampoco demuestran que exista un gasto positivo' in streamed
    assert 'cobertura de la ingesta' in streamed and 'consulta de costes autorizada' in streamed
    assert rendered['evidence'] == [] and rendered['metrics'] == []

@pytest.mark.parametrize('question', [
    QUESTION.replace('gasto de septiembre', 'gasto de agosto'),
    QUESTION.replace('gasto de septiembre', 'gasto de septiembre de 2025'),
    QUESTION.replace('cero registros', 'dos registros'),
    QUESTION.replace('devuelve cero', 'no devuelve cero'),
    QUESTION.replace('todavía no se ha completado', 'ya se ha completado'),
    QUESTION.replace('todavía no se ha completado', 'quizá no se ha completado'),
    QUESTION + ' Otro periodo tiene datos completos.',
    QUESTION.replace('¿El gasto de septiembre es cero?', 'Define gasto cero y calcula el forecast.'),
])
def test_mismatch_ambiguity_or_additional_claims_do_not_force_route(question):
    assert required_missing_spend(catalog(question)) is None

def test_server_financial_evidence_is_not_silently_discarded():
    q = catalog(sources=[{'kind': 'cost_query', 'id': 'query:1'}])
    assert required_missing_spend(q) is None

@pytest.mark.parametrize('field,value', [('status', 'ok'), ('answer', {'missing_spend': 'forged'}),
    ('evidence', [{'id': 'irrelevant'}]), ('recommendations', [{'rationale': 'El gasto es cero.'}]),
    ('limitations', [[{'inference': 'El gasto es positivo.'}]])])
def test_provider_cannot_add_amount_or_unsupported_support(field, value):
    q = catalog(); supplied = response(q); supplied[field] = value
    with pytest.raises(ValueError): render_response(supplied, [], quantities=q)

def test_schema_requires_bound_terminal_and_insufficient_data():
    from app.agents.schemas import chat_provider_schema
    q = catalog(); schema = chat_provider_schema(quantities=q)
    assert schema['properties']['answer']['const'] == response(q)['answer']
    assert schema['properties']['status']['enum'] == ['insufficient_data']
    assert schema['properties']['evidence']['maxItems'] == 0
