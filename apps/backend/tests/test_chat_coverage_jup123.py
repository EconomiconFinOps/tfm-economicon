import json

from app.core.chat_expressions import context_quantities
from app.core.chat_segments import render_response
from app.schemas.chat import validate_response


def test_hypothetical_budget_coverage_preserves_the_public_authority_boundary():
    question='¿Hay riesgo para el presupuesto?\n\nDatos aportados: forecast 840 EUR; budget 800 EUR.'
    q=context_quantities({'messages':[{'role':'user','content':
        'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})}]})
    value={'schema_version':'1.0','scope':{'cloud':'azure','data_environment':'simulated',
            'period':None,'subscription_ids':[]},'basis':'user_scenario',
           'status':'insufficient_data','answer':[{'inference':'Es una proyección hipotética.'}],
           'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],
           'limitations':[],'next_actions':[]}
    result=render_response(value,[],quantities=q)
    assert '40 EUR' in result['answer'] and 'presupuesto: 5 %' in result['answer']
    checked=validate_response(result,[],expected_period=None,expected_subscriptions=[])
    assert checked['status']=='insufficient_data' and checked['metrics']==[]
    assert checked['evidence']==[] and checked['recommendations']==[]
