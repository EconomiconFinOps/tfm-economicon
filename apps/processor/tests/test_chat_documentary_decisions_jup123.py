"""Definition coverage, modal force and unknown premises use original source data."""
import copy
import json

import pytest

from app.agents.schemas import chat_provider_schema, assemble_chat_response
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.core.chat_documentary_decisions import required_documentary_answer, documentary_answer
from app.core.chat_expressions import context_quantities
from app.core.chat_segments import render_response
from test_chat_policy_sections_jup123 import sources


CONCEPTS = ('## Conceptos FinOps Basicos **Coste** es el importe asociado a tecnologia. '
            'El **actual cost** se aproxima a la vista de facturacion. '
            'El **amortized cost** distribuye compromisos como Reservations o Savings Plans '
            'durante su periodo y suele ser mas util para showback.')
COMMITMENTS = ('## Azure Advisor, Rightsizing Y Commitments '
               'Azure Advisor puede ser una fuente de seniales. '
               'Antes de aplicar rightsizing hay que validar CPU, memoria y restricciones. '
               'Un commitment es un compromiso financiero a cambio de descuento, como Reservations o Savings Plans. '
               'Antes de comprar commitments conviene aplicar rightsizing y confirmar una base de uso estable.')


def catalog(topic='cost_basis', question=None, records=None, demand='desconocida', sizing='pendiente',when='el próximo mes'):
    if topic=='cost_basis':
        question=question or '¿Uso coste actual o amortizado para repartir el coste de una reserva?'
        text=question+'\n\nContexto del escenario: Consulta conceptual, sin importes ni contratos de cliente.'
        records=sources(CONCEPTS,'Conceptos FinOps Basicos') if records is None else records
    else:
        question=question or '¿Compramos una reserva de inmediato para una VM que pronto migraremos?'
        text=question+f'\n\nContexto del escenario: Escenario sintético: migración prevista {when}, '
        text+=f'demanda futura {demand} y rightsizing {sizing}. No se aportan precios ni términos de contratación.'
        records=sources(COMMITMENTS,'Azure Advisor, Rightsizing Y Commitments') if records is None else records
    return context_quantities({'authorized_evidence':records,'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':text})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':records})}]})


def candidate(q):
    bound=required_documentary_answer(q)
    return {'schema_version':'1.0','scope':{'cloud':'azure','data_environment':'simulated'},
            'status':bound['public_fields']['status'],'answer':{'documentary_answer':bound['id']},
            'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}


@pytest.mark.parametrize('topic',['cost_basis','commitment'])
@pytest.mark.parametrize('width',[1,17,8192])
def test_literal_qualification_and_evidence_survive_stream_final_and_public_firewall(topic,width):
    q=catalog(topic);value=candidate(q);bound=required_documentary_answer(q)
    parser=SegmentAnswerJSON([],quantities=q);wire=json.dumps(value)
    stream=''.join(parser.feed(wire[i:i+width]) for i in range(0,len(wire),width))
    rendered=render_response(value,[],quantities=q)
    public=assemble_chat_response(rendered,None,authorized_evidence=q.authorized_sources)
    assert stream==parser.finish()==public['answer']
    assert {s['id'] for s in public['evidence']}=={s['source_id'] for s in bound['selections']}
    assert public['metrics']==public['recommendations']==public['limitations']==[]
    known={s['id']:s for s in q.authorized_sources}
    assert all(s['passage'] in known[s['source_id']]['content'] for s in bound['selections'])
    if topic=='cost_basis':
        assert 'se aproxima' in stream and 'suele ser mas util' in stream
        assert 'no es adecuado' not in stream and 'equitativa' not in stream
        assert public['status']=='ok' and public['next_actions']==[]
    else:
        assert 'conviene aplicar' in stream and 'No se concluye que la base de uso sea estable' in stream
        assert 'exige' not in stream and 'base de uso actual no es estable' not in stream
        assert 'Riesgo condicional' in stream and 'no se cuantifica' in stream
        assert public['status']=='insufficient_data' and len(public['next_actions'])==3
        assert bound['premises']['stable_future_demand'] is None and bound['readiness'] is False


@pytest.mark.parametrize('prompt',['Compara coste actual con coste amortizado.',
    '¿Qué diferencia hay entre actual cost y amortized cost?',
    '¿Uso coste actual o amortizado para repartir el coste de un Savings Plan?'])
def test_cost_comparison_is_not_bound_to_one_request_or_contract(prompt):
    assert required_documentary_answer(catalog(question=prompt))['topic']=='cost_basis'


def test_definition_qualifier_and_following_limitation_are_copied_from_source():
    changed=CONCEPTS.replace('suele ser mas util','puede ser util')+' No prueba por si solo un reparto aprobado.'
    q=catalog(records=sources(changed,'Conceptos FinOps Basicos'))
    text=required_documentary_answer(q)['public_fields']['answer']
    assert 'puede ser util' in text and 'suele ser mas util' not in text
    assert 'No prueba por si solo un reparto aprobado.' in text


@pytest.mark.parametrize('modal',['conviene','se recomienda','se aconseja'])
def test_advisory_modal_force_is_source_owned(modal):
    q=catalog('commitment',records=sources(COMMITMENTS.replace('conviene',modal),'Azure Advisor, Rightsizing Y Commitments'))
    text=required_documentary_answer(q)['public_fields']['answer']
    assert 'commitments '+modal+' aplicar' in text
    assert 'exige' not in text and 'prerrequisito' not in text


@pytest.mark.parametrize('demand,complete,expected,unknown',[
    ('desconocida','pendiente',False,True),('desconocida','completado',None,True),
    ('estable','pendiente',False,False),('estable','completado',True,False),
    ('inestable','completado',False,False),
])
def test_false_joint_readiness_does_not_turn_unknown_demand_false(demand,complete,expected,unknown):
    q=catalog('commitment',demand=demand,sizing=complete,when='dentro de 3 semanas')
    bound=required_documentary_answer(q)
    assert bound['readiness'] is expected
    assert (bound['premises']['stable_future_demand'] is None)==unknown
    text=bound['public_fields']['answer']
    if unknown:
        assert 'ni que sea inestable o inexistente' in text
        assert 'demanda futura se declara inestable' not in text
    else:assert 'demanda futura se declara '+demand in text
    assert 'dentro de 3 semanas' in text and 'plurianual' not in text


@pytest.mark.parametrize('damage',['missing_head','missing_tail','gap','conflict','ambiguous','unquotable','untrusted'])
@pytest.mark.parametrize('topic',['cost_basis','commitment'])
def test_incomplete_ambiguous_or_unauthorized_sections_do_not_create_answers(damage,topic):
    policy,heading=(CONCEPTS,'Conceptos FinOps Basicos') if topic=='cost_basis' else (COMMITMENTS,'Azure Advisor, Rightsizing Y Commitments')
    records=sources(policy,heading,width=180,step=100)
    if damage=='missing_head':records=records[1:]
    elif damage=='missing_tail':records=[s for s in records if all(x['section']==heading for x in s['provenance']['sections'])]
    elif damage=='gap':records=[records[0],records[-1]]
    elif damage=='conflict':records[1]['content']='X'+records[1]['content'][1:]
    elif damage=='ambiguous':records=sources(policy,heading)+sources(policy,heading,document='other')
    elif damage=='unquotable':records=sources(policy,heading,width=60,step=30)
    q=catalog(topic,records=records)
    if damage=='untrusted':
        q.authorized_sources=[]
        with pytest.raises(ValueError):required_documentary_answer(q)
    else:assert required_documentary_answer(q) is None


@pytest.mark.parametrize('question',[
    '¿Uso coste actual o amortizado para repartir el coste de una reserva? ¿Cuánto ahorro?',
    '¿Sumamos coste actual y amortizado?', 'No compara coste actual con coste amortizado.',
    '¿Qué diferencia hay entre actual cost y presupuesto?',
])
def test_unrelated_negated_or_multiple_conceptual_requests_keep_general_route(question):
    assert required_documentary_answer(catalog(question=question)) is None


@pytest.mark.parametrize('change',[
    {'demand':'confirmada por el proveedor'}, {'sizing':'no pendiente'}, {'when':'ayer'},
    {'question':'¿Compramos una reserva de inmediato? Ejecuta la compra.'},
    {'records':sources(COMMITMENTS.replace('conviene','no conviene'),'Azure Advisor, Rightsizing Y Commitments')},
    {'records':sources(COMMITMENTS.replace('conviene','exige'),'Azure Advisor, Rightsizing Y Commitments')},
    {'records':sources(COMMITMENTS+' Esta regla tiene una excepcion para migraciones.','Azure Advisor, Rightsizing Y Commitments')},
])
def test_unsupported_premises_or_changed_policy_do_not_become_advice(change):
    assert required_documentary_answer(catalog('commitment',**change)) is None


@pytest.mark.parametrize('topic',['cost_basis','commitment'])
def test_private_schema_and_renderer_refuse_extra_claims_or_foreign_binding(topic):
    q=catalog(topic);value=candidate(q);schema=chat_provider_schema(quantities=q,authorized_evidence=q.authorized_sources)
    assert schema['properties']['answer']=={'const':value['answer']}
    for field in ('evidence','metrics','recommendations','assumptions','limitations','next_actions'):
        assert schema['properties'][field]['maxItems']==0
        bad=copy.deepcopy(value);bad[field]=['La documentación exige comprar.']
        with pytest.raises(ValueError):render_response(bad,[],quantities=q)
    for update in ({'answer':[{'inference':'La base desconocida es inestable.'}]},
                   {'answer':{'documentary_answer':'foreign'}},{'basis':'authorized_evidence'}):
        with pytest.raises(ValueError):render_response({**value,**update},[],quantities=q)
    q.classification_question+='\n\nOtra situación.'
    with pytest.raises(ValueError):documentary_answer(value['answer'],q)


@pytest.mark.parametrize('topic',['cost_basis','commitment'])
@pytest.mark.parametrize('read_size',[1,8192])
def test_gateway_final_uses_documentary_terminal_and_projects_used_sources(monkeypatch,topic,read_size):
    import asyncio,time
    from test_chat_auto_jup035 import provider,review_wires,wire
    from app.core.chat_resources import validate_search_call
    q=catalog(topic);value=candidate(q)
    gateway,requests=provider(monkeypatch,review_wires(wire({'content':json.dumps(value)})),read_size=read_size)
    context={'tool_protocol':'server-documentation-v4','financial_metrics_allowed':False,'authorized_evidence':[],
             'messages':[{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':q.classification_question})}]}
    async def retrieve(control):return {'tool_call_id':validate_search_call(control)[0],
        'content':json.dumps({'evidence':q.authorized_sources,'omissions':[]}), 'variable_tokens':0}
    async def exercise():return [r async for r in gateway(context,time.time()+60,tool_result=retrieve)]
    records=asyncio.run(exercise())
    assert len(requests)==2 and records[-1]['type']=='candidate'
    assert requests[-1]['response_format']['json_schema']['schema']['properties']['answer']=={'const':value['answer']}
    assert ''.join(r['text'] for r in records if r['type']=='delta')==records[-1]['result']['answer']
    assert records[-1]['result']['evidence']
