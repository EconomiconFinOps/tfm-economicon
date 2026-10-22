import json

import pytest
from jsonschema import Draft202012Validator


def test_nova_wrapper_preserves_branch_and_reference_constraints():
    from app.core.bedrock import native_tool_schema
    original = {'type': 'object', '$defs': {'Amount': {'type': 'integer', 'minimum': 1}}, 'anyOf': [
        {'type': 'object', 'properties': {'kind': {'const': 'cost'}, 'amount': {'$ref': '#/$defs/Amount'}},
         'required': ['kind', 'amount'], 'additionalProperties': False},
        {'type': 'object', 'properties': {'kind': {'const': 'empty'}}, 'required': ['kind'], 'additionalProperties': False}]}
    wrapped = native_tool_schema(original)
    assert set(wrapped) == {'type', 'properties', 'required'} and wrapped['type'] == 'object'
    for candidate in [{'kind': 'cost', 'amount': 1}, {'kind': 'empty'}, {'kind': 'cost'},
                      {'kind': 'empty', 'amount': 1}, {'kind': 'cost', 'amount': 0}]:
        assert Draft202012Validator(original).is_valid(candidate) == Draft202012Validator(wrapped).is_valid({'response': candidate})
    assert original['anyOf'][0]['properties']['amount']['$ref'] == '#/$defs/Amount'


def test_native_wrapper_is_removed_incrementally_without_losing_json_escapes():
    from app.core.bedrock import NativeToolJSON
    schema = {'type': 'object', 'properties': {'answer': {'type': 'string'}}, 'required': ['answer'], 'additionalProperties': False}
    value = {'answer': 'Medir "CPU", memoria y latencia. 😀'}
    raw = json.dumps({'response': value}, ensure_ascii=True)
    decoder = NativeToolJSON(schema)
    fragments = [decoder.feed(char) for char in raw]
    assert any(fragments[:len(raw) - 3]), 'Must preserve streaming before the complete wrapper arrives'
    assert json.loads(''.join(fragments)) == value
    assert decoder.finish() == value


@pytest.mark.parametrize('raw', ['{"response":{"answer":"ok"},"extra":true}',
    '{"response":{"answer":"first"},"response":{"answer":"second"}}',
    '{"response":{"answer":true}}', '{"response":{"answer":"truncated"}'])
def test_invalid_native_wrapper_never_completes(raw):
    from app.core.bedrock import NativeToolJSON
    decoder = NativeToolJSON({'type': 'object', 'properties': {'answer': {'type': 'string'}}, 'required': ['answer']})
    with pytest.raises(ValueError):
        decoder.feed(raw)
        decoder.finish()


def test_remote_schema_references_are_rejected_without_network():
    from app.core.bedrock import native_tool_schema
    with pytest.raises(ValueError):
        native_tool_schema({'type': 'object', 'properties': {'value': {'$ref': 'https://foreign.invalid/schema'}}})


def test_native_review_reports_complete_token_counters_without_inventing_price():
    from app.core.bedrock import native_review_usage
    leg = {'prompt_tokens': 12, 'completion_tokens': 4, 'total_tokens': 16, 'cost_usd': None}
    assert native_review_usage([leg, leg], 2) == {'prompt_tokens': 24, 'completion_tokens': 8, 'total_tokens': 32}
    assert native_review_usage([leg], 2) is None
    assert native_review_usage([leg, {'prompt_tokens': 12}], 2) is None
    assert native_review_usage([leg, dict(leg, total_tokens=99)], 2) is None
