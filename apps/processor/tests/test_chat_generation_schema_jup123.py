"""Compare original and provider spellings with an independent schema engine."""
import copy

import pytest
from jsonschema import Draft202012Validator

from app.core.chat_generation_schema import expand_constants


@pytest.mark.parametrize('value', [None, True, False, 0, 1, -3, 2.5, '😀', '',
    {}, [], {'unit_cost': 'bound-123'}, {'left': {'quantity': 'q'}, 'right': {'value': '100'}},
    ['a', 2, {'x': False}], {'const': {'enum': ['not a schema']}}])
def test_constant_lowering_has_identical_acceptance(value):
    original = {'const': value}
    lowered = expand_constants(original)
    Draft202012Validator.check_schema(lowered)
    candidates = [value, None, True, False, 0, 1, 1.0, '1', {}, [], ['x'],
                  {'unit_cost': 'bound-123'}, {'unit_cost': 'forged'},
                  {'unit_cost': 'bound-123', 'extra': True}]
    if isinstance(value, dict):
        candidates += [{**value, 'extra': 'x'}, {key: item for i, (key, item) in enumerate(value.items()) if i}]
    if isinstance(value, list):
        candidates += [value[::-1], value + [None], value[:-1]]
    for candidate in candidates:
        assert Draft202012Validator(original).is_valid(candidate) == Draft202012Validator(lowered).is_valid(candidate)
    assert original == {'const': value}


def test_only_schema_positions_are_transformed_and_references_are_preserved():
    original = {'type': 'object', '$defs': {'Terminal': {'const': {'id': 'real'}}},
                'properties': {'answer': {'$ref': '#/$defs/Terminal'},
                               'data': {'enum': [{'const': {'data': True}}]}},
                'required': ['answer', 'data'], 'additionalProperties': False}
    before = copy.deepcopy(original)
    wire = expand_constants(original)
    assert wire['properties'] == original['properties']
    assert wire['$defs']['Terminal']['required'] == ['id']
    assert original == before
    assert not Draft202012Validator(wire).is_valid({'answer': {'id': 'forged'}, 'data': {'const': {'data': True}}})


def test_constraints_and_modes_are_never_dropped():
    original = {'anyOf': [{'type': 'object', 'properties': {'mode': {'const': 'a'}},
                          'required': ['mode'], 'additionalProperties': False},
                         {'type': 'object', 'properties': {'mode': {'const': 'b'}},
                          'required': ['mode'], 'additionalProperties': False}]}
    wire = expand_constants(original)
    for value in ({'mode': 'a'}, {'mode': 'b'}, {'mode': 'c'}, {'mode': 'a', 'extra': 1}, {}):
        assert Draft202012Validator(original).is_valid(value) == Draft202012Validator(wire).is_valid(value)


@pytest.mark.parametrize('schema', [
    {'const': {'id': 'real'}, 'properties': {'other': {'type': 'string'}}},
    {'const': ['a'], 'maxItems': 0}, {'const': {'a': 1}, 'type': 'array'},
    {'const': True, 'enum': [1]}, {'const': 'a', 'enum': ['b']},
])
def test_unsupported_intersections_fail_before_dispatch(schema):
    with pytest.raises(ValueError):
        expand_constants(schema)
