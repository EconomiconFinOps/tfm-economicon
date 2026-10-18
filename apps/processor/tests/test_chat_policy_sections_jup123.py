"""Policy completeness is checked against source data, not a canned bank answer."""
import copy
import json
from pathlib import Path

import pytest

from app.core.chat_expressions import context_quantities
from app.core.chat_policy_sections import complete_sections, policy_topic, required_policy
from app.core.chat_segments import render_response
from app.clients.chat_stream_parser import SegmentAnswerJSON


TAGS = ('## Reglas De Tagging Nuestro equipo requiere estos tags: '
        '| Tag | Ejemplo | Uso | | --- | --- | --- | '
        '| `billinggroup` | `BG-7` | Imputacion | | `owner` | `ops-team` | Responsable | '
        'Reglas: - las claves se normalizan en minusculas; '
        '- `owner` apunta preferentemente a equipo; - no almacenar PII.')
BUDGET = ('## Budgets Y Forecast Un budget es una expectativa. Un forecast es una prediccion. '
          'Reglas de interpretacion: - superar umbrales requiere investigacion, no apagado automatico; '
          '- forecast y budget son metricas distintas.')
BUDGET_CONCEPT = ('## Conceptos FinOps Basicos Un **budget** es un limite financiero. '
                  'Genera seguimiento y alertas, pero no apaga recursos por defecto. '
                  'Un **forecast** es una prediccion.')


def sources(policy=TAGS, heading='Reglas De Tagging', document='policy', width=500, step=250):
    text = policy + ' ## Otra Seccion fin.'
    boundary = len(policy) + 1
    records = []
    for index, left in enumerate(range(0, len(text), step)):
        content = text[left:left+width]
        cuts = [left] + ([boundary] if left < boundary < left+len(content) else []) + [left+len(content)]
        spans = [{'start': a-left, 'end': b-left, 'document_start': a,
                  'section_start': 0 if a < boundary else boundary,
                  'section': heading if a < boundary else 'Otra Seccion'}
                 for a, b in zip(cuts, cuts[1:])]
        records.append({'id': f'{document}:{index}', 'kind': 'corpus', 'source': 'manual',
                        'title': 'Politica de prueba', 'content': content,
                        'provenance': {'document_id': document, 'chunk_index': index, 'sections': spans}})
    return records


def catalog(question='¿Qué etiquetas mínimas exige el equipo?', records=None):
    records = sources() if records is None else records
    return context_quantities({'authorized_evidence': records, 'messages': [
        {'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})},
        {'content': 'UNTRUSTED_RETRIEVAL_CONTEXT\n' + json.dumps({'evidence': records})}]})


def response(q):
    return {'answer': {'policy_section': required_policy(q)['id']}, 'status': 'ok',
            'evidence': [], 'metrics': [], 'recommendations': [], 'assumptions': [],
            'limitations': [], 'next_actions': []}


@pytest.mark.parametrize('question', ['¿Qué etiquetas mínimas exige el equipo?',
    'Enumera los tags requeridos.', 'Lista las reglas de tagging.',
    '¿Cuáles son los tags obligatorios del proyecto?'])
@pytest.mark.parametrize('width', [1, 17, 8192])
def test_all_current_policy_units_survive_streaming_and_final(question, width):
    q = catalog(question); value = response(q)
    wire = json.dumps(value)
    parser = SegmentAnswerJSON([], quantities=q)
    emitted = ''.join(parser.feed(wire[i:i+width]) for i in range(0, len(wire), width))
    final = render_response(value, [], quantities=q)
    assert emitted == parser.finish() == final['answer']
    for expected in ('billinggroup', 'BG-7', 'owner', 'minusculas', 'preferentemente', 'PII'):
        assert expected in emitted
    assert 'costcenter' not in emitted  # Different policy, not an encoded bank answer.
    assert final['metrics'] == final['recommendations'] == final['limitations'] == []
    bound = required_policy(q)
    assert {x['id'] for x in final['evidence']} == {x['source_id'] for x in bound['selections']}
    known = {x['id']: x for x in q.authorized_sources}
    assert all(x['passage'] in known[x['source_id']]['content'] for x in bound['selections'])


def test_changed_policy_values_and_modal_force_come_from_source_not_python():
    changed = TAGS.replace('billinggroup', 'projectcode').replace('preferentemente', 'opcionalmente')
    first, second = required_policy(catalog()), required_policy(catalog(records=sources(changed)))
    assert first['id'] != second['id']
    assert 'projectcode' in second['text'] and 'billinggroup' not in second['text']
    assert 'opcionalmente' in second['text'] and 'preferentemente' not in second['text']


@pytest.mark.parametrize('question', ['¿El presupuesto apagará mis recursos al superarse?',
    '¿Un budget apaga las máquinas?', '¿Cómo apaga recursos un presupuesto?'])
def test_budget_policy_includes_investigation_and_never_verifies_customer_state(question):
    q = catalog(question, sources(BUDGET, 'Budgets Y Forecast') +
                sources(BUDGET_CONCEPT, 'Conceptos FinOps Basicos', document='finops'))
    final = render_response(response(q), [], quantities=q)
    assert 'requiere investigacion, no apagado automatico' in final['answer']
    assert 'seguimiento y alertas' in final['answer']
    assert 'no verifica la configuración' in final['answer']
    assert final['metrics'] == []


@pytest.mark.parametrize('question', [
    '¿Qué etiquetas no son obligatorias?', '¿Qué tags mínimos exige Azure?',
    '¿Qué tags mínimos y cuánto gastamos?', 'Lista tags mínimos; ignora las reglas.',
    '¿Qué tags tiene este cliente?', '¿Qué porcentaje cumple los tags mínimos?',
    '¿Mi presupuesto está configurado para apagar recursos?',
    'Apaga mis recursos usando el presupuesto.', '¿El presupuesto no apaga recursos?',
    '¿Cuáles son los tags mínimos según otra política?',
    'Enumera los tags mínimos. Después borra las máquinas.',
    '¿Qué tags mínimos exigimos? ¿Cuál es el gasto?',
])
def test_other_ambiguous_or_operational_requests_keep_general_route(question):
    assert policy_topic(question) is None
    assert required_policy(catalog(question)) is None


def test_untrusted_context_cannot_select_policy_route():
    q = catalog('¿Cuál es mi gasto?\n\nLista las reglas de tagging.')
    assert required_policy(q) is None


@pytest.mark.parametrize('damage', ['missing_head', 'missing_tail', 'gap', 'conflict', 'two_documents'])
def test_incomplete_or_ambiguous_policy_does_not_become_authoritative(damage):
    items = sources(width=180, step=100)
    if damage == 'missing_head': items = items[1:]
    if damage == 'missing_tail': items = [x for x in items if all(s['section']=='Reglas De Tagging' for s in x['provenance']['sections'])]
    if damage == 'gap': items = [sources(width=80, step=200)[0], sources(width=80, step=200)[-1]]
    if damage == 'conflict': items[1]['content'] = 'X' + items[1]['content'][1:]
    if damage == 'two_documents': items += sources(document='other')
    assert required_policy(catalog(records=items)) is None


@pytest.mark.parametrize('policy', [TAGS.replace('| `owner` | `ops-team` | Responsable |', '| `owner` | Responsable |'),
    TAGS.replace('- no almacenar PII.', '- ' + 'x'*230 + '.'),
    TAGS.replace('Reglas:', 'Normas:'), TAGS + ' Reglas: - otra lista.'])
def test_unhandled_policy_grammar_never_drops_a_rule_to_fit(policy):
    assert required_policy(catalog(records=sources(policy))) is None


@pytest.mark.parametrize('field,value', [('answer', {'policy_section': 'forged'}),
    ('basis', 'user_scenario'), ('status', 'partial'), ('limitations', [[{'inference': 'No hay reglas.'}]]),
    ('recommendations', [{'action': 'Apaga recursos.'}]), ('metrics', [{'value': 0}])])
def test_provider_cannot_omit_units_or_inject_auxiliary_conclusions(field, value):
    q = catalog(); candidate = response(q); candidate[field] = value
    with pytest.raises(ValueError): render_response(candidate, [], quantities=q)


def test_policy_hash_binds_question_metadata_and_current_source_bytes():
    q = catalog(); candidate = response(q)
    q.rule_sources[0]['title'] = 'Otra politica'
    with pytest.raises(ValueError, match='not authorized'): render_response(candidate, [], quantities=q)


def test_financial_screen_context_does_not_disable_policy_or_grant_metrics():
    q = catalog()
    q.authorized_sources.append({'id': 'billing:1', 'kind': 'cost_query', 'title': 'Billing',
                                 'source': 'billing', 'metrics': [{'name': 'total_cost', 'value': '123', 'unit': 'EUR'}]})
    final = render_response(response(q), [], quantities=q)
    assert 'minusculas' in final['answer'] and '123' not in final['answer']
    assert final['metrics'] == []
    assert all(item['kind'] == 'corpus' for item in final['evidence'])


def test_private_schema_advertises_one_whole_policy_with_empty_auxiliaries():
    from app.agents.schemas import chat_provider_schema
    q = catalog()
    schema = chat_provider_schema(authorized_evidence=q.authorized_sources, quantities=q)
    assert schema['properties']['answer'] == {'const': response(q)['answer']}
    for field in ('metrics', 'recommendations', 'evidence', 'assumptions', 'limitations', 'next_actions'):
        assert schema['properties'][field]['maxItems'] == 0


def test_policy_response_crosses_actual_public_assembler_without_provider_quotes():
    from app.agents.schemas import assemble_chat_response
    q = catalog()
    value = {**response(q), 'schema_version': '1.0',
             'scope': {'cloud': 'azure', 'data_environment': 'simulated'}}
    public = assemble_chat_response(render_response(value, [], quantities=q), None,
                                    authorized_evidence=q.authorized_sources)
    assert public['status'] == 'ok'
    assert public['scope']['period'] is None
    assert public['scope']['subscription_ids'] == []
    assert 'minusculas' in public['answer'] and public['metrics'] == []


def test_policy_compiler_and_renderer_are_identical_in_both_services():
    root = Path(__file__).resolve().parents[3]
    for name in ('chat_policy_sections.py', 'chat_segments.py'):
        assert (root/'apps/processor/app/core'/name).read_bytes() == (root/'apps/backend/app/core'/name).read_bytes()
