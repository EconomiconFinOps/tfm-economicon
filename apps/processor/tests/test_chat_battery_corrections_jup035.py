import copy
import os
from pathlib import Path

import pytest


def test_scope_is_server_owned_and_model_cannot_inject_subscription():
    from app.agents.schemas import assemble_chat_response, chat_provider_schema
    from test_chat_gateway_jup035 import ANSWER
    candidate = copy.deepcopy(ANSWER)
    candidate['scope'].pop('period')
    candidate['scope'].pop('subscription_ids')
    assert 'subscription_ids' not in chat_provider_schema()['$defs']['ResponseScope']['properties']
    assert all(b['properties']['metrics']['maxItems']==0 for b in chat_provider_schema()['anyOf'])
    assert all(b['properties']['metrics']['maxItems']==(20 if b['properties']['basis']['const']=='authorized_evidence' else 0)
        for b in chat_provider_schema(financial_metrics_allowed=True)['anyOf'])
    from app.agents.schemas import FinOpsResponse
    assert FinOpsResponse.model_json_schema()['properties']['metrics']['maxItems'] == 20
    assert assemble_chat_response(candidate, None, ['subscription-a'])['scope']['subscription_ids'] == ['subscription-a']
    assert assemble_chat_response(candidate, None, [])['scope']['subscription_ids'] == []
    candidate['scope']['subscription_ids'] = ['tenant-core']
    with pytest.raises(ValueError):
        assemble_chat_response(candidate, None, [])


@pytest.mark.parametrize('financial_allowed', [False, True])
def test_private_schema_branches_preserve_scope_and_financial_authority(financial_allowed):
    from app.agents.schemas import chat_provider_schema, FinOpsResponse
    schema = chat_provider_schema(financial_metrics_allowed=financial_allowed)
    assert 'anyOf' in schema
    actionable, abstention = [branch for branch in schema['anyOf']
        if branch['properties']['basis']['const']=='authorized_evidence']
    neutral=[branch for branch in schema['anyOf'] if branch not in (actionable,abstention)]
    assert len(neutral)==5
    for branch in neutral:
        assert 'basis' in branch['required'] and 'status' in branch['required']
        assert branch['properties']['metrics']['maxItems']==0
        assert branch['properties']['evidence']['maxItems'] == 0
    assert actionable['properties']['status']['enum'] == ['ok', 'partial']
    assert actionable['properties']['evidence']['minItems'] == 0
    assert actionable['properties']['evidence']['maxItems'] == 0
    assert abstention['properties']['status']['enum'] == [
        'no_data', 'insufficient_data', 'unsupported', 'refused', 'error']
    assert abstention['properties']['evidence']['minItems'] == 0
    assert abstention['properties']['evidence']['maxItems'] == 0
    public=FinOpsResponse.model_json_schema()
    assert 'properties' not in schema and 'required' not in schema
    for branch in (actionable, abstention):
        assert set(branch['required']) == set(public['required']) | {'basis'}
        assert branch['additionalProperties'] is False
        assert branch['properties']['metrics']['maxItems'] == (20 if financial_allowed else 0)
        assert branch['properties']['scope'] == public['properties']['scope']
        assert branch['properties']['evidence']['items']['additionalProperties'] is False
        assert 'Evidence' not in schema['$defs']
        assert 'period' not in schema['$defs']['ResponseScope']['properties']
        assert 'subscription_ids' not in schema['$defs']['ResponseScope']['properties']


def test_chat_output_budget_reserves_configured_output(monkeypatch):
    from app.core.context_budget import budget
    assert budget('chat')['output_tokens'] == 3200
    monkeypatch.setenv('CHAT_MAX_OUTPUT_TOKENS', '1600')
    assert budget('chat')['output_tokens'] == 1600
    monkeypatch.setenv('CHAT_MAX_OUTPUT_TOKENS', '3201')
    with pytest.raises(ValueError):
        budget('chat')


def test_v4_prompt_has_general_hypothetical_and_documentary_rules():
    # This is a packaging guard, not semantic acceptance of a model response.
    from app.core.chat_resources import load_resources
    resource=load_resources()
    assert resource.prompt_version.startswith('jup-035.chat.v4:')
    text=' '.join(resource.system.split())
    for rule in [
        'hipotéticos/no verificados', 'shared identificado no es unallocated',
        'owner como equipo responsable', 'ausencia de datos personales',
        'convención de mayúsculas/minúsculas', 'ok/partial requieren evidencia autorizada realmente usada',
        'muestra diferencia absoluta y variación relativa', 'puntos porcentuales',
        'Un cociente con base cero', 'Si hay recuentos y costes, explica ambas ponderaciones',
        'investigar y confirmar causa y esperabilidad', 'no para apagar recursos',
        'CPU, memoria, IO, picos, rendimiento, SLA, crecimiento y restricciones de negocio',
        'posible deterioro de rendimiento/servicio/SLA',
        'ahorro identificado, implementado estimado y verificado',
        'conservando importes/categorías relevantes y sus comparaciones',
        'moneda de destino, tipo/dirección del cambio y fecha',
        'Ausencia de datos no es cero', 'período elegible',
        'Una captura no resuelve hoy ni un período financiero', 'pide período/zona horaria si hacen falta',
        'No listes todos los resultados ni añadas afirmaciones para justificar citas',
        'el mismo título, tema o fragmento vecino no bastan',
        'La aritmética del usuario no es evidencia documental ni financiera',
        'no inventes plazo, precio ni ahorro', 'falta de datos para cuantificarlo',
        'bloque completo con unidades',
    ]:
        assert rule in text
    assert 'JUP-069-' not in text
    assert 'DocumentationDecision' not in text and 'calculation_id' not in text
    assert 'No rechaces una definición documental por faltar costes reales' in text
