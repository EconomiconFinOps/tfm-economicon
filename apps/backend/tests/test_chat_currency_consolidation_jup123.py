"""Independent backend firewall preserves FX abstention and public contract."""
import json

import pytest

from app.core.chat_expressions import context_quantities
from app.core.chat_currency_consolidation import required_currency_consolidation
from app.core.chat_segments import render_response
from app.schemas.chat import provider_response_schema, validate_response


@pytest.mark.parametrize('units', [('EUR', 'USD'), ('CHF', 'GBP'), ('JPY', 'CAD')])
def test_missing_conversion_is_server_bound_and_passes_public_firewall(units):
    question = ('¿Puedes consolidar los costes de las dos suscripciones?\n\n'
                f'Escenario sintético enero 2027: one-9 12.5 {units[0]}; two_4 7.25 {units[1]}. '
                'No se suministra tipo de cambio ni fecha de conversión.')
    q = context_quantities({'authorized_evidence': [], 'messages': [
        {'content': 'UNTRUSTED_CURRENT_CONTEXT\n' + json.dumps({'question': question})}]})
    answer = {'currency_consolidation': required_currency_consolidation(q)['id']}
    schema = provider_response_schema(authorized_evidence=[], quantities=q)
    assert schema['properties']['answer'] == {'const': answer}
    value = {'schema_version': '1.0', 'status': 'insufficient_data', 'answer': answer,
             'scope': {'cloud': 'azure', 'data_environment': 'simulated', 'period': None, 'subscription_ids': []},
             'evidence': [], 'metrics': [], 'recommendations': [], 'assumptions': [], 'limitations': [], 'next_actions': []}
    public = render_response(value, [], quantities=q)
    assert validate_response(public, [], expected_period=None, expected_subscriptions=[]) == public
    assert all(s in public['answer'] for s in ('moneda destino', 'tipo de cambio autorizado', 'fecha de cambio'))
    assert f'12.5 {units[0]}' in public['answer'] and f'7.25 {units[1]}' in public['answer']
    value['status'] = 'ok'
    with pytest.raises(ValueError):
        render_response(value, [], quantities=q)
