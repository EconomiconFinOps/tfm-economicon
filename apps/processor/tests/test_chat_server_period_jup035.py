import copy
import json

import pytest
from test_chat_gateway_jup035 import ANSWER, _provider, supported_provider, _diagnostic_run, _diagnostic_wire


def provider_answer():
    value = copy.deepcopy(ANSWER)
    value['scope'].pop('period')
    value['scope'].pop('subscription_ids')
    return value


def test_provider_omits_period_but_public_contract_preserves_it():
    from app.agents.schemas import FinOpsResponse, chat_provider_schema
    schema = chat_provider_schema()
    assert 'period' not in schema['$defs']['ResponseScope']['properties']
    assert 'period' not in schema['$defs']['ResponseScope']['required']
    assert 'Period' not in schema['$defs']
    assert schema['$defs']['ResponseScope']['additionalProperties'] is False
    assert 'period' in FinOpsResponse.model_json_schema()['$defs']['ResponseScope']['required']


def test_gateway_accepts_periodless_model_response(monkeypatch, caplog):
    records, events = _diagnostic_run(monkeypatch, _diagnostic_wire(json.dumps(supported_provider())), caplog)
    assert records[-1]['type'] == 'candidate'
    assert records[-1]['result']['scope']['period'] is None
    assert not events
    period = {'from': '2026-09-01', 'to': '2026-10-01'}
    records, events = _diagnostic_run(monkeypatch, _diagnostic_wire(json.dumps(supported_provider())), caplog, period=period)
    assert records[-1]['type'] == 'candidate'
    assert records[-1]['result']['scope']['period'] == period
    assert not events


def test_server_assembly_preserves_verified_period_and_rejects_model_injection():
    from app.agents.schemas import assemble_chat_response
    period = {'from': '2026-09-01', 'to': '2026-10-01'}
    assert assemble_chat_response(provider_answer(), period)['scope']['period'] == period
    assert assemble_chat_response(provider_answer(), None)['scope']['period'] is None
    with pytest.raises(ValueError):
        assemble_chat_response(copy.deepcopy(ANSWER), period)
    with pytest.raises(ValueError):
        assemble_chat_response(provider_answer(), {'from': '2026-10-01', 'to': '2026-10-01'})
