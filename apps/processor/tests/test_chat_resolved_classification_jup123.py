import copy
import json

import pytest

from app.core.chat_expressions import context_quantities, ExpressionRenderer, expression_definitions
from app.core.chat_rules import resolved_classification
from app.core.chat_segments import bind_segments, render_response, CLASSIFICATION_ABSTENTIONS
from test_chat_interval_stream_jup035 import fixture


def catalog_for(question):
    context, _, _ = fixture()
    context['messages'][0]['content'] = 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})
    return context_quantities(context)


QUESTION = 'Classify waste.\n\nScenario with 100 EUR eligible cost and 8 EUR waste.'


def test_explicit_total_is_bound_and_boundary_evaluated_on_server():
    catalog = catalog_for(QUESTION)
    node = resolved_classification(catalog)
    assert node['value']['denominator'] == {'quantity': '100 EUR'}
    assert node['value']['numerator'] == {'quantity': '8 EUR'}
    assert '): middle.' in ExpressionRenderer(catalog).render(node)
    assert expression_definitions(catalog)['DocumentaryClassification'] == {'const': node}
    changed = copy.deepcopy(node)
    changed['value']['denominator'] = {'quantity': '8 EUR'}
    with pytest.raises(ValueError, match='KPI value mismatch'):
        ExpressionRenderer(catalog).render(changed)


@pytest.mark.parametrize('question', [
    QUESTION.replace('eligible cost', 'cost'),
    QUESTION.replace('100 EUR', '100 USD'),
    QUESTION.replace('100 EUR', '0 EUR'),
    QUESTION.replace('100 EUR', '-100 EUR'),
    QUESTION.replace('100 EUR', '4 EUR'),
    QUESTION + ' Another period has 100 EUR eligible cost.',
    QUESTION + ' Another period has 8 EUR waste.',
    QUESTION + ' Excluded: 10 EUR.',
    QUESTION.replace('100 EUR eligible cost', '100 EUR non eligible cost'),
    QUESTION.replace('Classify waste.', 'Define waste.'),
])
def test_missing_ambiguous_or_incompatible_operands_do_not_force_classification(question):
    assert resolved_classification(catalog_for(question)) is None


def test_spanish_explicit_total_and_false_abstention_rejected():
    catalog = catalog_for('Clasifica waste.\n\nEscenario con 100 EUR elegibles y 8 EUR waste.')
    assert resolved_classification(catalog)
    value = {'answer': [{'text': CLASSIFICATION_ABSTENTIONS[1]}],
             'status': 'insufficient_data', 'evidence': [], 'metrics': [],
             'recommendations': [], 'assumptions': [], 'limitations': [], 'next_actions': []}
    with pytest.raises(ValueError, match='Resolved classification requires typed answer'):
        render_response(value, [], quantities=catalog)


def test_schema_keeps_only_classified_answer_when_operands_are_resolved():
    from app.agents.schemas import chat_provider_schema
    catalog = catalog_for(QUESTION)
    schema = chat_provider_schema(authorized_evidence=list(catalog.authorized_sources), calculations=[], quantities=catalog)
    assert all('classification' in b['properties']['answer']['properties'] for b in schema['anyOf'])
