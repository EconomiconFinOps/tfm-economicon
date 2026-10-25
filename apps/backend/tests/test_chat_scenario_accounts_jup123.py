"""Independent backend grammar, scoped arithmetic and public response contract."""
import json

import pytest

from app.core.chat_expressions import context_quantities
from app.core.chat_cost_breakdown import required_cost_breakdown
from app.core.chat_shared_allocation import required_shared_allocation
from app.core.chat_segments import render_response
from app.schemas.chat import provider_response_schema, validate_response


@pytest.mark.parametrize('key,question,scenario,binder,expected',[
    ('cost_breakdown','¿Cuánto gastamos en agosto y qué servicio concentra más coste?',
     'Escenario sintético completo de agosto de 2026, suscripción demo-a, moneda EUR, coste actual: '
     'Virtual Machines 600; Storage 250; Log Analytics 150. No hay otras líneas.',
     required_cost_breakdown,('coste actual','= 1000 EUR','= 60 %','demo-a')),
    ('cost_breakdown','¿Cuál es el gasto total y cuál servicio cuesta más?',
     'Escenario sintético completo de marzo de 2027, suscripción demo-b, moneda USD, coste amortizado: '
     'Compute 20; Disk 20. No hay otras líneas.',
     required_cost_breakdown,('coste amortizado','= 40 USD','empatados','50 %')),
    ('shared_allocation','¿Cuánto cargamos a cada equipo por los 450 GBP de plataforma compartida?',
     'Escenario sintético: plataforma shared de 450 GBP, usada por equipos web y datos. '
     'No existe regla de reparto aprobada ni consumo por equipo.',
     required_shared_allocation,('shared','450 GBP','su base de reparto','no se asignan importes iguales')),
])
def test_server_scenarios_retain_supplied_facts_and_cannot_authorize_financial_metrics(key,question,scenario,binder,expected):
    q=context_quantities({'authorized_evidence':[],'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question+'\n\n'+scenario})}]})
    answer={key:binder(q)['id']}
    schema=provider_response_schema(authorized_evidence=[],quantities=q)
    assert schema['properties']['answer']=={'const':answer}
    value={'schema_version':'1.0','status':'insufficient_data','answer':answer,
           'scope':{'cloud':'azure','data_environment':'simulated','period':None,'subscription_ids':[]},
           'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}
    public=render_response(value,[],quantities=q)
    assert validate_response(public,[],expected_period=None,expected_subscriptions=[])==public
    assert all(part in public['answer'] for part in expected)
    assert public['metrics']==public['evidence']==public['limitations']==[]
