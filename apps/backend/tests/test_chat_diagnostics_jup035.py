"""Closed diagnostics expose rules, never response values or exception text."""
import json
import logging

import pytest

from test_chat_operations_jup035 import ANSWER, api, body, headers, path, run


@pytest.mark.parametrize('change,rule', [
    ({'status': 'ok'}, 'actionable_requires_evidence'),
    ({'status': 'SECRET-INVALID-STATUS'}, 'schema_enum'),
    ({'answer': ''}, 'schema_text'),
    ({'metrics': [{'name': 'SECRET', 'value': '1', 'unit': 'EUR', 'evidence_ids': ['SECRET']}]}, 'non_actionable_payload'),
])
def test_validation_has_closed_rule_without_values(change, rule):
    from app.schemas.chat import validate_response
    with pytest.raises(ValueError) as caught:
        validate_response({**ANSWER, **change}, [])
    assert getattr(caught.value, 'rule_code', None) == rule
    assert 'SECRET' not in str(caught.value)


def test_producer_logs_only_identity_stage_and_closed_rule(api, caplog):
    api[2].candidate = {**ANSWER, 'status': 'ok', 'answer': 'SECRET-PROMPT-KEY-RESPONSE'}
    caplog.set_level(logging.WARNING, logger='app.services.chat_operations')

    async def scenario(client):
        response = await client.post(path(), json=body(content='SECRET-QUESTION'), headers=headers())
        assert 'event: terminal' in response.text

    run(scenario, api)
    records = [record for record in caplog.records if record.message.startswith('chat_backend_diagnostic ')]
    assert len(records) == 1
    value = json.loads(records[0].message.split(' ', 1)[1])
    assert set(value) == {'operation_id', 'attempt_id', 'stage', 'rule_code'}
    assert value['stage'] == 'response_validation'
    assert value['rule_code'] == 'actionable_requires_evidence'
    assert value['operation_id'] and value['attempt_id']
    assert 'SECRET' not in records[0].message
