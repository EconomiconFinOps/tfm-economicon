"""Savings-stage binding also passes the independent backend public firewall."""
import json

import pytest

from app.core.chat_expressions import context_quantities
from app.core.chat_savings_realization import required_savings_realization
from app.core.chat_segments import render_response
from app.schemas.chat import provider_response_schema, validate_response


@pytest.mark.parametrize('identified,estimated,verified,expected',[
    ('200','150','80','80 / 200 × 100 = 40 %'),
    ('0','20','10','Realization indefinida'),
    ('3','2','1','1 / 3 × 100 ≈ 33.333333 %'),
])
def test_savings_roles_formula_and_public_authority(identified,estimated,verified,expected):
    question=('Calcula el savings realization.\n\nEscenario sintético: '
              f'ahorro identificado {identified} EUR/mes; ahorro implementado estimado {estimated} EUR/mes; '
              f'ahorro verificado {verified} EUR/mes. Para este ejercicio, '
              'realization = verificado / identificado * 100.')
    q=context_quantities({'authorized_evidence':[],'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})}]})
    answer={'savings_realization':required_savings_realization(q)['id']}
    schema=provider_response_schema(authorized_evidence=[],quantities=q)
    assert schema['properties']['answer']=={'const':answer}
    value={'schema_version':'1.0','status':'insufficient_data','answer':answer,
           'scope':{'cloud':'azure','data_environment':'simulated','period':None,'subscription_ids':[]},
           'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}
    public=render_response(value,[],quantities=q)
    assert validate_response(public,[],expected_period=None,expected_subscriptions=[])==public
    assert expected in public['answer']
    assert f'realizado corresponde sólo al verificado: {verified} EUR/mes' in public['answer']
    assert public['metrics']==public['evidence']==[] and public['status']=='insufficient_data'
