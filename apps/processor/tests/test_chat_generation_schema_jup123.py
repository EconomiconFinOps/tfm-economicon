"""Compare original and provider spellings with an independent schema engine."""
import copy

import pytest
from jsonschema import Draft202012Validator

from app.core.chat_generation_schema import expand_constants, generation_schema


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
    {'const': None, 'type': 'string'}, {'const': None, 'type': ['string', 'null']},
    {'const': 1, 'enum': [1.0, 2]}, {'const': 1.0, 'enum': [1, 2]},
    {'const': True, 'type': 'integer'}, {'const': 0, 'type': 'string'},
])
def test_scalar_intersections_preserve_null_and_json_number_semantics(schema):
    wire = generation_schema(schema)
    for value in (None, '', 'x', 0, 1, 1.0, 2, True, False):
        assert Draft202012Validator(schema).is_valid(value) == Draft202012Validator(wire).is_valid(value)


@pytest.mark.parametrize('schema', [
    {'const': {'id': 'real'}, 'properties': {'other': {'type': 'string'}}},
    {'const': ['a'], 'maxItems': 0}, {'const': {'a': 1}, 'type': 'array'},
    {'const': True, 'enum': [1]}, {'const': 'a', 'enum': ['b']},
])
def test_unsupported_intersections_fail_before_dispatch(schema):
    with pytest.raises(ValueError):
        expand_constants(schema)


def test_empty_collections_remove_only_unreachable_grammars():
    original = {'type': 'object', 'properties': {
        'answer': {'$ref': '#/$defs/Live'},
        'evidence': {'type': 'array', 'maxItems': 0, 'items': {'$ref': '#/$defs/Dead'}}},
        'required': ['answer', 'evidence'], 'additionalProperties': False,
        '$defs': {'Live': {'type': 'object', 'properties': {'id': {'$ref': '#/$defs/Id'}},
                          'required': ['id'], 'additionalProperties': False},
                  'Id': {'const': 'real'}, 'Dead': {'type': 'string', 'pattern': '^dead$'}}}
    wire = generation_schema(original)
    assert set(wire['$defs']) == {'Live', 'Id'}
    for value in ({'answer': {'id': 'real'}, 'evidence': []},
                  {'answer': {'id': 'forged'}, 'evidence': []},
                  {'answer': {'id': 'real'}, 'evidence': ['dead']},
                  {'answer': {'id': 'real', 'extra': 1}, 'evidence': []}):
        assert Draft202012Validator(original).is_valid(value) == Draft202012Validator(wire).is_valid(value)


def test_recursive_live_reference_and_literal_ref_are_preserved():
    original = {'$defs': {'Node': {'anyOf': [{'type': 'null'}, {'type': 'array', 'items': {'$ref': '#/$defs/Node'}}]},
                         'Dead': {'type': 'string'}}, '$ref': '#/$defs/Node'}
    wire = generation_schema(original)
    assert set(wire['$defs']) == {'Node'}
    for value in (None, [], [None, []], 'wrong'):
        assert Draft202012Validator(original).is_valid(value) == Draft202012Validator(wire).is_valid(value)
    assert generation_schema({'enum': [{'$ref': 'data-not-a-reference'}]}) == {'enum': [{'$ref': 'data-not-a-reference'}]}


@pytest.mark.parametrize('original', [
    {'$ref': 'https://invalid.example/schema'},
    {'$defs': {}, '$ref': 'https://invalid.example/schema'},
    {'$defs': {}, '$ref': '#/$defs/Missing'},
    {'$defs': {'A': {}}, '$ref': '#/$defs/A/properties/x'},
    {'$id': 'scope', '$defs': {}},
])
def test_unknown_reference_scopes_fail_closed(original):
    with pytest.raises(ValueError):
        generation_schema(original)
