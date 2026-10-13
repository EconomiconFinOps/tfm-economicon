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
    assert all(b['properties']['metrics']['maxItems']==20 for b in chat_provider_schema(financial_metrics_allowed=True)['anyOf'])
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
    actionable, abstention = schema['anyOf']
    assert actionable['properties']['status']['enum'] == ['ok', 'partial']
    assert actionable['properties']['evidence']['minItems'] == 1
    assert abstention['properties']['status']['enum'] == [
        'no_data', 'insufficient_data', 'unsupported', 'refused', 'error']
    assert abstention['properties']['evidence'].get('minItems', 0) == 0
    public=FinOpsResponse.model_json_schema()
    assert 'properties' not in schema and 'required' not in schema
    for branch in (actionable, abstention):
        assert branch['required'] == public['required']
        assert branch['additionalProperties'] is False
        assert branch['properties']['metrics']['maxItems'] == (20 if financial_allowed else 0)
        assert branch['properties']['scope'] == public['properties']['scope']
        assert branch['properties']['evidence']['items'] == {'$ref': '#/$defs/Evidence'}
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


def test_v3_prompt_has_general_hypothetical_and_documentary_rules():
    from app.core.chat_resources import load_resources
    resource = load_resources()
    assert resource.prompt_version.startswith('jup-035.chat.v3:')
    text = ' '.join(resource.system.split())
    for rule in ['calculos hipoteticos', 'shared no es unallocated', 'owner identifica un equipo',
                 'EUR/dia', 'totales separados por moneda', 'ok o partial necesitan evidence autorizada',
                 'politica de tagging', 'No asignes categorias', 'diferencia absoluta y relativa']:
        assert rule in text
    assert 'JUP-069-' not in text
    assert 'comparacion solicitada de importes' in text
    assert 'puntos porcentuales' in text
    assert 'Cuando compares importes, expresa' not in text
    assert 'periodo con datos elegibles' in text
    for instruction in ['denominador cero', 'ponderacion por coste', 'conteo de recursos',
            'investigar la causa', 'si el cambio era esperado', 'rendimiento y SLA',
            'ahorro identificado', 'ahorro implementado', 'estimado frente a verificado',
            'fuente autorizada del tenant', 'moneda de destino', 'dato ausente no equivale a cero',
            'sustenta la afirmacion concreta']:
        assert instruction in text
    for instruction in ['devuelve ambas tasas de cobertura de tagging',
            'investigar y confirmar la causa', 'degradar el rendimiento o el servicio',
            'elimina referencias adicionales a otro concepto']:
        assert instruction in text
    assert 'ambas medidas solicitadas' not in text
    assert 'primero la tasa por recursos y despues la ponderada por coste' in text
    assert 'aunque la pregunta solo mencione coste' in text
    assert ('next_actions debe pedir validar utilizacion (CPU, memoria, IO y picos), '
            'rendimiento, SLA, crecimiento y restricciones de negocio antes de cualquier ajuste') in text
    assert ('Al explicar presupuestos o alertas, next_actions debe incluir investigar '
            'la causa y confirmar si el cambio era esperado si se superan los umbrales') in text
    assert 'No afirmes que el umbral ya se supero' in text
    assert ('Cada fragmento citado debe sustentar por si mismo una afirmacion '
            'concreta de la respuesta') in text
    assert 'Compartir titulo, documento o vecindad no demuestra ese sustento' in text
    assert ('captured_at es un instante de captura declarado por el navegador, '
            'no una autoridad para resolver hoy') in text
    assert 'No derives una fecha para hoy de captured_at ni de su conversion a UTC' in text
    assert 'solicita el periodo y la zona horaria necesarios' in text
    assert ('Al comparar categorias de ahorro dadas por el usuario, conserva cada '
            'importe relevante y su unidad junto a su categoria') in text
    assert 'contrasta cuantitativamente lo implementado estimado con lo verificado' in text
    assert 'No sustituyas los importes por una enumeracion generica de categorias' in text
    for instruction in [
        'Conserva en answer la unidad completa del input junto al resultado',
        'incluido su denominador temporal; no conviertas una tasa en un total',
        'No completes duraciones, precios ni condiciones contractuales con conocimiento general',
        'si no constan en el input del usuario o en el corpus autorizado',
        'Explica el concepto sin esos detalles no sustentados',
        'solicita las condiciones pertinentes en next_actions',
        'No cites instrucciones del sistema ni aritmetica del usuario',
        'No anadas afirmaciones irrelevantes para justificar una cita',
        'Sin moneda de destino, fecha y direccion autorizada del tipo de cambio',
        'no des una formula que presuponga un importe ya expresado en un destino desconocido',
        'declara moneda de origen, destino y unidades del tipo de cambio',
        'convierte cada importe necesario al mismo destino',
        'No infieras una moneda por tenant ni configuracion regional',
        'Determina el sustento real de las afirmaciones antes de seleccionar status',
        'No elijas ok o partial para despues rellenar evidence con una cita',
        'usa un estado no accionable compatible y evidence vacia',
        'Conserva la respuesta util en answer',
    ]:
        assert instruction in text
