"""Independent backend grammar and public validation of count/cost coverage."""
import json

import pytest

from app.core.chat_expressions import context_quantities
from app.core.chat_segments import render_response
from app.core.chat_weighted_coverage import required_weighted_coverage
from app.schemas.chat import provider_response_schema, validate_response


@pytest.mark.parametrize('currency,yes,no,expected', [('EUR', '100', '900', '10 %'),
                                                   ('GBP', '250', '250', '50 %'),
                                                   ('USD', '0', '0', 'denominador es cero')])
def test_complete_scenario_grammar_and_public_firewall(currency,yes,no,expected):
    question = ('Calcula la cobertura de etiquetado ponderada por coste.\n\n'
                'Escenario sintético: 10 recursos etiquetables. Nueve cumplen todos los tags mínimos '
                f'y suman {yes} {currency}; el décimo incumple y cuesta {no} {currency}. '
                'Todo el coste es etiquetable.')
    q=context_quantities({'authorized_evidence': [], 'messages': [
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})}]})
    answer={'weighted_coverage':required_weighted_coverage(q)['id']}
    schema=provider_response_schema(authorized_evidence=[],quantities=q)
    assert schema['properties']['answer']=={'const':answer}
    value={'schema_version':'1.0','status':'insufficient_data','answer':answer,
           'scope':{'cloud':'azure','data_environment':'simulated','period':None,'subscription_ids':[]},
           'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}
    public=render_response(value,[],quantities=q)
    assert validate_response(public,[],expected_period=None,expected_subscriptions=[])==public
    assert expected in public['answer'] and '9 / 10 × 100 = 90 %' in public['answer']
    assert public['metrics']==public['evidence']==[]
