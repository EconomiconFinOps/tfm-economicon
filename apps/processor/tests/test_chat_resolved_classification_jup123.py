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


PARTITION = ('Clasifica unallocated.\n\nEscenario EUR: allocated 70; shared 20; '
             'unallocated 10; excluded 5. La regla del escenario excluye esos 5 '
             'del coste elegible; el resto es elegible.')


def partition_catalog(question):
    context, _, _ = fixture()
    source = context['authorized_evidence'][0]
    source['content'] = source['content'].replace('Waste Cost', 'Unallocated Cost')
    source['provenance']['sections'][0]['end'] = len(source['content'])
    context['messages'][0]['content'] = 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})
    context['messages'][1]['content'] = 'UNTRUSTED_RETRIEVAL_CONTEXT\n' + json.dumps({'evidence': [source]})
    return context_quantities(context)


def test_explicit_allocation_partition_excludes_only_excluded_and_keeps_shared():
    catalog = partition_catalog(PARTITION)
    node = resolved_classification(catalog)
    assert node is not None
    rendered = ExpressionRenderer(catalog).render(node)
    assert '10 %' in rendered and '): high.' in rendered
    assert '= 100 EUR.' in rendered
    assert '5 EUR' not in rendered
    assert node['value']['denominator'] == {'operation': 'sum', 'left': {'quantity': '70 EUR'},
        'right': {'operation': 'sum', 'left': {'quantity': '20 EUR'}, 'right': {'quantity': '10 EUR'}}}
    changed = copy.deepcopy(node)
    changed['value']['denominator']['right']['right'] = {'quantity': '5 EUR'}
    with pytest.raises(ValueError, match='KPI value mismatch'):
        ExpressionRenderer(catalog).render(changed)


@pytest.mark.parametrize('question', [
    PARTITION.split('. La regla')[0] + '.',
    PARTITION.replace('el resto es elegible', 'el resto puede ser elegible'),
    PARTITION.replace('excluye esos 5', 'excluye esos 6'),
    PARTITION.replace('excluye esos 5', 'no excluye esos 5'),
    PARTITION.replace('shared 20', 'shared 20 USD'),
    PARTITION.replace('shared 20', 'shared -20'),
    PARTITION.replace('shared 20', 'shared 70'),
    PARTITION.replace('shared 20;', 'shared 20; other 30;'),
    PARTITION + ' Otro periodo: allocated 70; shared 20; unallocated 10; excluded 5.',
    PARTITION.replace('Clasifica', 'Define'),
])
def test_allocation_partition_without_closed_unambiguous_policy_is_not_resolved(question):
    assert resolved_classification(partition_catalog(question)) is None


def test_partition_supports_another_currency_and_does_not_embed_business_thresholds():
    catalog = partition_catalog(PARTITION.replace('EUR', 'USD').replace('allocated 70;', 'allocated 170;'))
    node = resolved_classification(catalog)
    rendered = ExpressionRenderer(catalog).render(node)
    assert '5 %' in rendered and '): middle.' in rendered
    assert 'USD' in rendered


@pytest.mark.parametrize('width', [1, 11, 8192])
def test_partition_stream_matches_final_with_visible_eligible_total(width):
    from app.clients.chat_stream_parser import SegmentAnswerJSON
    catalog = partition_catalog(PARTITION)
    response = {'answer': {'calculations': [], 'classification': resolved_classification(catalog)},
        'assumptions': [], 'limitations': [], 'next_actions': [], 'recommendations': [], 'metrics': [], 'evidence': []}
    raw = json.dumps(response)
    parser = SegmentAnswerJSON([], quantities=catalog)
    streamed = ''.join(parser.feed(raw[i:i+width]) for i in range(0, len(raw), width))
    assert streamed == parser.finish() == render_response(response, [], quantities=catalog)['answer']
    assert '= 100 EUR.' in streamed and '): high.' in streamed


def test_partition_visible_total_does_not_claim_exact_equality_after_rounding():
    catalog = partition_catalog(PARTITION.replace('allocated 70;', 'allocated 70.0000001;'))
    node = resolved_classification(catalog)
    assert '≈ 100 EUR.' in ExpressionRenderer(catalog).render(node)
