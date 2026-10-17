"""Guards that no test exercised: each case fails if the corresponding check is removed or loosened."""
import json

import pytest

from app.core import chat_calculations as calc
from app.core.chat_expressions import ExpressionRenderer, context_quantities, quantities


def ctx(question, evidence=()):
    messages = [{'role': 'user', 'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})}]
    if evidence:
        messages.append({'role': 'user', 'content': 'UNTRUSTED_RETRIEVAL_CONTEXT\n' + json.dumps({'evidence': list(evidence)})})
    return {'messages': messages, 'authorized_evidence': list(evidence)}


def step(left, right, operator, unit_left='EUR', unit_right='EUR'):
    return [{'left': {'literal': left, 'unit': unit_left}, 'right': {'literal': right, 'unit': unit_right}, 'operator': operator}]


def test_subtraction_of_incompatible_units_is_rejected():
    with pytest.raises(calc.CalculationError) as failure:
        calc.calculate(ctx('Coste 10 EUR y 5 GB.'), step('10', '5', 'subtract', 'EUR', 'GB'))
    assert failure.value.rule_code == 'calculation_incompatible_calculation_units'


def test_division_by_zero_keeps_its_own_closed_code():
    with pytest.raises(calc.CalculationError) as failure:
        calc.calculate(ctx('Coste 10 EUR entre 0 EUR.'), step('10', '0', 'divide'))
    assert failure.value.rule_code == 'calculation_denominator_zero'


def test_pending_stream_text_is_bounded_at_16384_characters():
    stream = calc.CalculationStream([])
    assert stream.feed('a' * 16384) == ''
    with pytest.raises(calc.CalculationError) as failure:
        stream.feed('a')
    assert failure.value.rule_code == 'calculation_stream_limit'


@pytest.mark.parametrize('node', [
    {'operation': 'relative_change', 'current': {'quantity': '10 EUR'}, 'baseline': {'quantity': '5 GB'}},
    {'operation': 'compare', 'left': {'quantity': '10 EUR'}, 'right': {'quantity': '5 GB'}, 'relation': 'gt'},
])
def test_expressions_over_different_dimensions_are_rejected(node):
    catalog = context_quantities(ctx('Coste 10 EUR frente a 5 GB.'))
    assert set(catalog) == {'10 EUR', '5 GB'}
    with pytest.raises(ValueError, match='Incompatible expression units'):
        ExpressionRenderer(catalog).render(node)


def test_source_magnitude_and_decimal_places_are_bounded():
    assert list(quantities('Gasto 1000000000000 EUR.')) == ['1000000000000 EUR']
    assert quantities('Gasto 1000000000001 EUR.') == {}
    assert list(quantities('Gasto 0.123456789012 EUR.')) == ['0.123456789012 EUR']
    assert quantities('Gasto 0.1234567890123 EUR.') == {}


def test_daily_baseline_rate_does_not_leak_into_a_total():
    units = {key: entry['unit'] for key, entry in quantities('Baseline diario 100 EUR; observado total 130 EUR.').items()}
    assert units == {'100 EUR/día': 'EUR/día', '130 EUR': 'EUR'}


def classify(waste, rest):
    content = ('KPI: Waste Cost % = Waste Cost / Eligible Cost * 100 '
               '- low: < 3 %; - middle: >= 3 % and <= 8 %; - high: > 8 %.')
    source = {'id': 'synthetic:rule', 'kind': 'corpus', 'title': 'Synthetic', 'source': 'manual', 'content': content,
              'provenance': {'document_id': 'synthetic', 'chunk_index': 0, 'sections': [
                  {'start': 0, 'end': len(content), 'section': 'Waste', 'document_start': 12, 'section_start': 0}]}}
    catalog = context_quantities(ctx(f'waste: {waste} EUR; remaining: {rest} EUR.', [source]))
    leaf = lambda key: {'quantity': key + ' EUR'}
    node = {'operation': 'classify', 'rule_id': catalog.rules[0]['id'], 'value': {
        'operation': 'percentage', 'numerator': leaf(str(waste)),
        'denominator': {'operation': 'sum', 'left': leaf(str(waste)), 'right': leaf(str(rest))}}}
    return ExpressionRenderer(catalog).render(node)


@pytest.mark.parametrize('waste,rest,label', [(2, 98, 'low'), (3, 97, 'middle'), (8, 92, 'middle'), (9, 91, 'high')])
def test_inclusive_and_exclusive_interval_bounds_are_matched_exactly(waste, rest, label):
    assert f'): {label}.' in classify(waste, rest)
