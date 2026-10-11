"""Offline checks for the project packaging and explicitly selected mock path."""
import asyncio
import json
from pathlib import Path
import time

import pytest
import yaml

from app.clients.chat_gateway import configured_gateway as chat_gateway
from app.clients.summary_gateway import configured_gateway as summary_gateway, SummaryGatewayError
from app.core.summary_resources import load_resources, validate_sources

ROOT = Path(__file__).resolve().parents[3]


def test_compose_migrates_before_verify_and_keeps_listener_private():
    compose = yaml.safe_load((ROOT / 'docker-compose.yml').read_text())
    services = compose['services']
    migrator = services['backend-migrate']
    assert migrator['command'] == ['python', '-m', 'app.migrate']
    backend, processor = services['backend'], services['processor']
    assert backend['depends_on']['backend-migrate']['condition'] == 'service_completed_successfully'
    assert backend['environment']['BACKEND_SCHEMA_MODE'] == 'verify'
    assert processor['depends_on']['backend']['condition'] == 'service_healthy'
    assert 'processor' not in backend['depends_on']
    assert compose['networks']['chat-private']['internal'] is True
    assert processor['networks']['chat-private']['ipv4_address'] == processor['environment']['PROCESSOR_CHAT_BIND_HOST']
    assert 'processor-chat' in processor['networks']['chat-private']['aliases']
    assert backend['environment']['PROCESSOR_CHAT_BASE_URL'] == 'http://processor-chat:8003'
    assert not any('8003' in str(port) for port in processor.get('ports', []))
    assert backend['secrets'] == processor['secrets'] == ['chat-hmac']
    assert backend['environment']['CHAT_SERVICE_HMAC_KEY_FILE'] == processor['environment']['CHAT_SIGNING_KEY_FILE']
    for name in ('CHAT_ENABLED', 'SUMMARY_ENABLED', 'CHAT_CONTEXT_TOKENS', 'SUMMARY_CONTEXT_TOKENS', 'CHAT_MAX_ACTIVE'):
        assert backend['environment'][name] == processor['environment'][name]
    assert backend['environment']['SUMMARY_TIMEOUT_SECONDS'] == processor['environment']['SUMMARY_TIMEOUT_SECONDS'] == '${SUMMARY_TIMEOUT_SECONDS:-180}'
    ai = yaml.safe_load((ROOT / 'infra/litellm/compose.ai.yml').read_text())
    assert 'summary-api-key' in ai['services']['processor']['secrets']
    assert 'summary-api-key' not in ai['services']['backend'].get('secrets', [])


@pytest.mark.parametrize('service', ['backend', 'processor'])
def test_dockerfiles_resolve_locks_together_and_validate_bundled_assets(service):
    dockerfile = (ROOT / 'apps' / service / 'Dockerfile').read_text()
    assert '--require-hashes -r requirements.lock -r requirements-chat.lock' in dockerfile
    assert 'pip check' in dockerfile
    assert '-c requirements.txt' not in dockerfile
    assert 'pip install --dry-run --no-index -r requirements.txt' in dockerfile
    assert 'app.core.chat_resources' in dockerfile and 'app.core.summary_resources' in dockerfile
    assert 'USER economicon' in dockerfile
    if service == 'backend':
        assert 'COPY apps/processor/app/agents/prompt_resources/jup035/chat/v2 /opt/economicon/chat/v2' in dockerfile
        assert 'COPY apps/processor/app/agents/prompt_resources/jup035/summary /opt/economicon/summary' in dockerfile


def test_explicit_mock_chat_is_valid_and_does_not_open_network(monkeypatch):
    import socket
    from app.agents.schemas import FinOpsResponse
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: pytest.fail('Unexpected inference'))
    gateway = chat_gateway()
    assert gateway is not None, 'Explicit mock chat must be available'
    period = {'from': '2026-09-01', 'to': '2026-10-01'}
    async def collect():
        return [item async for item in gateway({'messages': [], 'response_period': period}, time.time() + 30)]
    records = asyncio.run(collect())
    assert [item['type'] for item in records] == ['delta', 'candidate']
    result = FinOpsResponse.model_validate(records[-1]['result'])
    assert result.status == 'insufficient_data'
    assert result.evidence == []
    assert 'mock' in ' '.join(result.assumptions)
    assert records[-1]['usage'] is None
    assert records[-1]['result']['scope']['period'] == period


def test_mock_summary_cancellation_settles_without_output(monkeypatch):
    monkeypatch.setenv('SUMMARY_ENABLED', 'true')
    gateway = summary_gateway()
    async def exercise():
        task = asyncio.create_task(gateway.dispatch('cancelled', [], None, time.time() + 30))
        await asyncio.sleep(0)
        gateway.cancel('cancelled')
        with pytest.raises(SummaryGatewayError, match='summary_cancelled'):
            await task
        assert gateway.jobs == {}
        await gateway.close()
    asyncio.run(exercise())


def test_mock_summary_validates_literal_sources_and_declares_omissions(monkeypatch):
    monkeypatch.setenv('SUMMARY_ENABLED', 'true')
    resources = load_resources()
    payload = {'previous_summary': None, 'pairs': [
        {'question_ref': 'q-' + '1' * 64, 'question': 'No autorizar cambios.',
         'answer_ref': 'a-' + '2' * 64, 'answer': 'No se permite borrar datos.'},
        {'question_ref': 'q-' + '3' * 64, 'question': 'texto largo ' * 100,
         'answer_ref': 'a-' + '4' * 64, 'answer': 'Sin confirmacion no reactivar.'}]}
    messages, _ = resources.prepare_input(payload)
    gateway = summary_gateway()
    assert gateway is not None, 'Explicit mock summary must be available'
    async def exercise():
        result = await gateway.dispatch('synthetic-job', messages, resources, time.time() + 30)
        await gateway.close()
        return result
    result = asyncio.run(exercise())
    output = resources.validate_payload(result['output'])
    sources = {p[role + '_ref']: p[role] for p in payload['pairs'] for role in ('question', 'answer')}
    validate_sources(output, sources)
    assert any(f['quote'] == 'No se permite borrar datos.' for f in output['facts'])
    assert all(f['quote'] != 'texto largo ' * 100 for f in output['facts'])
    assert any('mock' in text and 'omit' in text for text in output['limitations'])
    assert result['observed_model'] == 'mock' and result['usage'] is None and result['cost'] is None


def test_mock_summary_deadline_and_disabled_mode(monkeypatch):
    monkeypatch.setenv('SUMMARY_ENABLED', 'false')
    assert summary_gateway() is None
    monkeypatch.setenv('SUMMARY_ENABLED', 'true')
    gateway = summary_gateway()
    assert gateway is not None
    with pytest.raises(SummaryGatewayError, match='summary_deadline'):
        asyncio.run(gateway.dispatch('expired', [], load_resources(), time.time() - 1))


def test_real_configuration_never_selects_mock(monkeypatch):
    from app.clients.chat_gateway import ChatGateway
    monkeypatch.setenv('LLM_PROVIDER', 'litellm')
    monkeypatch.setenv('LITELLM_API_KEY', 'synthetic-main-virtual-key')
    monkeypatch.setenv('SUMMARY_ENABLED', 'true')
    monkeypatch.delenv('SUMMARY_API_KEY_FILE', raising=False)
    assert isinstance(chat_gateway(), ChatGateway)
    assert summary_gateway() is None


@pytest.mark.parametrize('key,value', [('AI_EXECUTION_MODE', 'evaluation'), ('RUNTIME_ENVIRONMENT', 'production')])
def test_mock_not_available_outside_development_or_test(monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    monkeypatch.setenv('SUMMARY_ENABLED', 'true')
    assert summary_gateway() is None
    with pytest.raises(Exception):
        chat_gateway()
