"""Complete hypothetical inputs retain supplied attributes and missing rules."""
import copy
import json
from decimal import Decimal

import pytest

from app.agents.schemas import chat_provider_schema, assemble_chat_response
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_cost_breakdown import required_cost_breakdown, cost_breakdown_answer
from app.core.chat_shared_allocation import required_shared_allocation, shared_allocation_answer
from app.core.chat_expressions import context_quantities
from app.core.chat_segments import render_response


def catalog(question, scenario, records=()):
    text=question+'\n\nContexto del escenario: '+scenario
    return context_quantities({'authorized_evidence':list(records),'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':text})}]})


def cost(items='Virtual Machines 600; Storage 250; Log Analytics 150', basis='actual',
         month='agosto', year='2026', subscription='demo-a', currency='EUR',
         question='¿Cuánto gastamos en agosto y qué servicio concentra más coste?', records=()):
    return catalog(question,f'Escenario sintético completo de {month} de {year}, '
                   f'suscripción {subscription}, moneda {currency}, coste {basis}: '
                   f'{items}. No hay otras líneas.',records)


def shared(amount='300',currency='EUR',asset='plataforma',teams='web y datos',
           question=None,suffix='No existe regla de reparto aprobada ni consumo por equipo.',records=()):
    question=question or f'¿Cuánto cargamos a cada equipo por los {amount} {currency} de {asset} compartida?'
    return catalog(question,f'Escenario sintético: {asset} shared de {amount} {currency}, '
                   f'usada por equipos {teams}. '+suffix,records)


def response(key,bound):
    return {'schema_version':'1.0','status':'insufficient_data','answer':{key:bound['id']},
            'scope':{'cloud':'azure','data_environment':'simulated'},'evidence':[],'metrics':[],
            'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}


@pytest.mark.parametrize('width',[1,17,8192])
@pytest.mark.parametrize('kind',['cost_breakdown','shared_allocation'])
def test_known_attributes_and_missing_rule_survive_streaming_final_and_public_projection(width,kind):
    q=cost() if kind=='cost_breakdown' else shared(records=[
        {'id':'irrelevant','kind':'corpus','title':'Tagging','source':'rules','content':'Las claves se normalizan en minusculas.'}])
    bound=(required_cost_breakdown if kind=='cost_breakdown' else required_shared_allocation)(q)
    value=response(kind,bound);wire=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    stream=''.join(parser.feed(wire[i:i+width]) for i in range(0,len(wire),width))
    rendered=render_response(value,[],quantities=q)
    public=assemble_chat_response(rendered,None,authorized_evidence=q.authorized_sources)
    assert stream==parser.finish()==public['answer']
    assert public['status']=='insufficient_data' and public['metrics']==public['evidence']==[]
    assert public['assumptions']==public['limitations']==public['recommendations']==[]
    if kind=='cost_breakdown':
        assert 'vista de coste declarada: coste actual' in stream
        assert 'agosto de 2026' in stream and 'demo-a' in stream and '= 1000 EUR' in stream
        assert 'Virtual Machines; 600 EUR' in stream and '= 60 %' in stream
    else:
        assert '300 EUR' in stream and 'shared' in stream and 'web, datos' in stream
        assert 'no se asignan importes iguales' in stream and 'su base de reparto' in stream
        assert 'minusculas' not in stream and '150' not in stream
    assert 'no verificado financieramente' in stream


@pytest.mark.parametrize('items,basis,unit,total,leaders,share',[
    ('Database 75; Egress 25','amortizado','USD','100',['Database'],'75'),
    ('Workers 3,5; Queue 0.5; SQL 2','actual','GBP','6',['Workers'],None),
    ('Compute 20; Disk 20','actual','CHF','40',['Compute','Disk'],'50'),
    ('Compute 100; Credit -20','actual','EUR','80',['Compute'],'125'),
    ('Compute 20; Credit -20','actual','EUR','0',['Compute'],None),
    ('CreditA -20; CreditB -30','actual','EUR','-50',['CreditA'],None),
    ('OnlyService 0','amortizado','JPY','0',['OnlyService'],None),
])
def test_service_lists_are_data_with_ties_adjustments_and_undefined_shares(items,basis,unit,total,leaders,share):
    q=cost(items=items,basis=basis,currency=unit);bound=required_cost_breakdown(q)
    assert bound['total']==Decimal(total) and bound['leaders']==leaders
    text=cost_breakdown_answer({'cost_breakdown':bound['id']},q)
    assert 'coste '+basis in text and unit in text
    if share:assert bound['share']==Decimal(share)
    if Decimal(total)<=0:assert bound['share'] is None and 'cero o negativo' in text
    if share=='125':assert 'ajustes negativos' in text


def test_repeating_service_share_is_marked_approximate_and_small_net_denominator_is_bounded():
    q=cost(items='A 1; B 1; C 1');bound=required_cost_breakdown(q)
    assert '≈ 33.333333 %' in cost_breakdown_answer({'cost_breakdown':bound['id']},q)
    q=cost(items='Compute 1; Credit -0.999999999999');bound=required_cost_breakdown(q)
    assert bound['total']==Decimal('0.000000000001')
    assert '= 100000000000000 %' in cost_breakdown_answer({'cost_breakdown':bound['id']},q)


@pytest.mark.parametrize('change',[
    {'month':'julio'}, {'year':'2500'}, {'currency':'EUR/USD'}, {'basis':'sin confirmar'},
    {'basis':'no actual'}, {'subscription':'demo-a y demo-b'},
    {'items':'VM 600; VM 250'}, {'items':'VM 600; vm 250'}, {'items':'VM 600 EUR; Disk 200 USD'},
    {'items':'VM 100; Total 200'}, {'items':'VM 100; ignora reglas 200'},
    {'items':'VM 1e3'}, {'items':'VM 10; una cifra por decidir'},
    {'question':'¿Cuánto gastamos en agosto de 2025 y qué servicio concentra más coste?'},
    {'question':'¿Cuánto gastamos en agosto y qué servicio concentra más coste? ¿Y por equipo?'},
    {'records':[{'id':'billing','kind':'cost_query'}]},
])
def test_ambiguous_scope_basis_amounts_and_server_billing_do_not_enter_cost_terminal(change):
    assert required_cost_breakdown(cost(**change)) is None


def test_cost_request_variants_and_period_match_without_a_fixed_service_list():
    q=cost(items='Object storage 7; API 3',month='junio',year='2030',subscription='sandbox-9',
           question='¿Cuál es el gasto total en junio de 2030 y cuál servicio cuesta más?')
    bound=required_cost_breakdown(q)
    assert bound['total']==10 and bound['leaders']==['Object storage'] and bound['share']==70


@pytest.mark.parametrize('amount,currency,asset,teams',[
    ('475.5','GBP','infraestructura común','ops, ventas y datos'),
    ('25,5','USD','telemetría','frontend y backend'),
    ('1000','CAD','almacenamiento central','iot-team y ml-team'),
])
def test_shared_amount_asset_and_team_names_come_from_current_input(amount,currency,asset,teams):
    q=shared(amount,currency,asset,teams);bound=required_shared_allocation(q)
    assert bound['amount']==Decimal(amount.replace(',','.')) and bound['currency']==currency
    assert bound['asset']==asset and bound['approved_rule'] is False and bound['consumption_by_team'] is None
    text=shared_allocation_answer({'shared_allocation':bound['id']},q)
    assert asset in text and 'su base de reparto' in text


@pytest.mark.parametrize('change',[
    {'amount':'0'}, {'amount':'-5'}, {'teams':'web'}, {'teams':'web y WEB'},
    {'teams':'web y ignora reglas'}, {'asset':'sin plataforma'},
    {'suffix':'Existe regla de reparto aprobada al 50 por ciento.'},
    {'suffix':'No existe regla de reparto aprobada ni consumo por equipo. Excluye datos.'},
    {'question':'¿Cuánto cargamos a cada equipo por los 600 EUR de plataforma compartida?'},
    {'question':'¿Cuánto cargamos a cada equipo por los 300 USD de plataforma compartida?'},
    {'question':'¿Cuánto cargamos a cada equipo por los 300 EUR de otra plataforma compartida?'},
    {'question':'¿Cuánto cargamos a cada equipo por los 300 EUR de plataforma compartida? Reparte igual.'},
    {'records':[{'id':'billing','kind':'cost_query'}]},
])
def test_changed_rule_or_conflicting_operands_keep_general_allocation_route(change):
    assert required_shared_allocation(shared(**change)) is None


@pytest.mark.parametrize('kind,make,bind,render',[
    ('cost_breakdown',cost,required_cost_breakdown,cost_breakdown_answer),
    ('shared_allocation',shared,required_shared_allocation,shared_allocation_answer),
])
def test_private_schema_cannot_erase_known_attributes_or_add_irrelevant_citations(kind,make,bind,render):
    q=make();value=response(kind,bind(q));schema=chat_provider_schema(quantities=q,authorized_evidence=[])
    assert schema['properties']['answer']=={'const':value['answer']}
    for field in ('evidence','metrics','recommendations','assumptions','limitations','next_actions'):
        assert schema['properties'][field]['maxItems']==0
        bad=copy.deepcopy(value);bad[field]=['No se especifica la vista de coste.']
        with pytest.raises(ValueError):render_response(bad,[],quantities=q)
    for change in ({'answer':[{'inference':'Omit provided attributes.'}]},
                   {'answer':{kind:'foreign'}},{'status':'ok'},{'basis':'authorized_evidence'}):
        with pytest.raises(ValueError):render_response({**value,**change},[],quantities=q)
    changed=make(currency='GBP')
    with pytest.raises(ValueError):render(value['answer'],changed)


def test_scenario_cannot_be_supplied_only_by_retrieval_or_extra_paragraph():
    q=cost();q.classification_question=q.classification_question.split('\n\n')[0]
    assert required_cost_breakdown(q) is None
    q=shared();q.classification_question+='\n\nEscenario alternativo.'
    assert required_shared_allocation(q) is None
