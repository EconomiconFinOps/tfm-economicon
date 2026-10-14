import itertools

import pytest

from app.core.chat_premises import Premise, evaluate


def fact(value, ref='captured-request:fact'):
    return Premise(value, () if value is None else (ref,))


@pytest.mark.parametrize('left,right', tuple(itertools.product((True, False, None), repeat=2)))
def test_all_any_truth_tables_preserve_unknown(left, right):
    premises = {'left': fact(left), 'right': fact(right)}
    children = [{'premise': 'left'}, {'premise': 'right'}]
    expected_all = False if False in (left, right) else None if None in (left, right) else True
    expected_any = True if True in (left, right) else None if None in (left, right) else False
    assert evaluate({'all': children}, premises).value is expected_all
    assert evaluate({'any': children}, premises).value is expected_any


@pytest.mark.parametrize('value,expected', [(True, False), (False, True), (None, None)])
def test_negation_does_not_turn_missing_evaluation_into_a_failure(value, expected):
    assert evaluate({'not': {'premise': 'quality'}}, {'quality': fact(value)}).value is expected


def test_false_formal_transfer_does_not_imply_insufficient_allocation_quality():
    # Models the distinction exposed by028; it does not parse its free prose.
    facts = {'formal_transfer': fact(False, 'user:formal-transfer'), 'quality': fact(None),
             'unrelated': fact(True, 'corpus:inform')}
    result = evaluate({'all': [{'premise': 'formal_transfer'}, {'premise': 'quality'}]}, facts)
    assert result.value is False
    assert result.unknown == ('quality',)
    assert result.premises['quality'].value is None
    assert result.support == ('user:formal-transfer',)
    assert 'corpus:inform' not in result.support
    facts['quality'] = fact(False)
    assert result.premises['quality'].value is None
    with pytest.raises(TypeError):
        result.premises['quality'] = fact(False)


def test_empty_records_do_not_bind_zero_spend():
    #026 has an ingestion observation, not an authenticated spend observation.
    result = evaluate({'premise': 'spend_is_zero'}, {'spend_is_zero': fact(None),
                      'records_empty': fact(True, 'user:query-empty')})
    assert result.value is None
    assert result.support == ()
    assert result.unknown == ('spend_is_zero',)


@pytest.mark.parametrize('value,support', [(0, ('x',)), (1, ('x',)), ('false', ('x',)),
    (False, ()), (None, ('x',)), (True, ['x']), (True, ('x', 'x'))])
def test_invalid_or_unsupported_premises_rejected(value, support):
    with pytest.raises(ValueError):
        Premise(value, support)


@pytest.mark.parametrize('tree', [
    {'all': [{'premise': 'false'}, {'premise': 'missing'}]},
    {'any': [{'premise': 'true'}, {'value': True}]},
    {'all': []}, {'all': [{'premise': 'true'}]}, {'premise': []},
    {'premise': 'true', 'value': True}, {'not': None},
])
def test_invalid_branch_is_rejected_even_if_another_branch_decides(tree):
    with pytest.raises(ValueError):
        evaluate(tree, {'false': fact(False), 'true': fact(True)})


def test_provider_dictionary_is_not_a_bound_premise():
    with pytest.raises(ValueError):
        evaluate({'premise': 'quality'}, {'quality': {'value': True, 'support': ['forged']}})


def test_cyclic_or_excessive_trees_are_bounded():
    cycle = {}
    cycle['not'] = cycle
    with pytest.raises(ValueError):
        evaluate(cycle, {})
    many = {'all': [{'all': [{'premise': 'p'}] * 16}] * 16}
    with pytest.raises(ValueError):
        evaluate(many, {'p': fact(True)})
