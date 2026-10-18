"""Measured defects: complete budget coverage, investigation scope and typed variance."""
import copy
import json
from pathlib import Path

import pytest

from app.core.chat_expressions import context_quantities, ExpressionRenderer
from app.core.chat_budget_comparison import required_budget_variance
from app.core.chat_documentary_decisions import required_documentary_answer
from app.core.chat_policy_sections import required_policy
from app.core.chat_segments import render_response
from app.clients.chat_stream_parser import SegmentAnswerJSON
from app.agents.schemas import chat_provider_schema, assemble_chat_response
from test_chat_policy_sections_jup123 import sources, BUDGET, BUDGET_CONCEPT


def catalog(question, records=()):
    return context_quantities({'authorized_evidence':list(records),'messages':[
        {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':question})},
        {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':[r for r in records if r.get('kind')=='corpus']})}]})


def candidate(key, bound, status='insufficient_data'):
    return {'schema_version':'1.0','scope':{'cloud':'azure','data_environment':'simulated'},
            'status':status,'answer':{key:bound['id']},'evidence':[],'metrics':[],
            'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}


@pytest.mark.parametrize('actual,budget,expected', [('1200','1000','20 %'),('700','1000','-30 %'),
    ('1000','1000','0 %'),('2','3','≈ -33.333333 %'),('10','0','Porcentaje indefinido'),
    ('999999999999','0.000000000001','99999999999899999999999900 %')])
@pytest.mark.parametrize('width',[1,17,8192])
def test_variance_stream_final_schema_and_authority(actual,budget,expected,width):
    question=('Calcula la desviación del presupuesto.\n\nEscenario sintético: '
              f'coste actual final {actual} EUR y budget {budget} EUR. '
              'Variación definida como coste menos presupuesto; porcentaje sobre presupuesto.')
    q=catalog(question);bound=required_budget_variance(q);value=candidate('budget_variance',bound)
    schema=chat_provider_schema(authorized_evidence=[],quantities=q)
    assert schema['properties']['answer']=={'const':value['answer']}
    wire=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    stream=''.join(parser.feed(wire[i:i+width]) for i in range(0,len(wire),width))
    final=assemble_chat_response(render_response(value,[],quantities=q),None,authorized_evidence=[])
    assert stream==parser.finish()==final['answer']
    assert expected in stream and 'no un forecast' in stream
    assert f'Presupuesto: {budget} EUR' in stream
    assert final['metrics']==final['evidence']==[] and final['status']=='insufficient_data'
    wrong=copy.deepcopy(value);wrong['answer']['budget_variance']='forged'
    with pytest.raises(ValueError):render_response(wrong,[],quantities=q)


@pytest.mark.parametrize('damage',['mixed','duplicate','negative','extra','forecast','different_formula','financial'])
def test_variance_ambiguous_inputs_keep_general_path(damage):
    scenario='Escenario sintético: coste actual final 1200 EUR y budget 1000 EUR. Variación definida como coste menos presupuesto; porcentaje sobre presupuesto.'
    records=[]
    if damage=='mixed':scenario=scenario.replace('1000 EUR','1000 USD')
    if damage=='duplicate':scenario=scenario.replace('budget','coste actual')
    if damage=='negative':scenario=scenario.replace('1200','-1200')
    if damage=='extra':scenario+=' Además apaga la VM.'
    if damage=='forecast':scenario=scenario.replace('coste actual final','forecast')
    if damage=='different_formula':scenario=scenario.replace('coste menos presupuesto','presupuesto menos coste')
    if damage=='financial':records=[{'id':'real','kind':'cost_query'}]
    assert required_budget_variance(catalog('Calcula la desviación del presupuesto.\n\n'+scenario,records)) is None


@pytest.mark.parametrize('month',['julio',None])
def test_variance_does_not_answer_august_with_another_or_unspecified_period(month):
    prefix='Escenario sintético'+(' '+month+' 2026 demo-a' if month else '')
    q=catalog('¿En cuánto superamos el presupuesto de agosto?\n\n'+prefix+': coste actual final 1200 EUR y budget 1000 EUR. Variación definida como coste menos presupuesto; porcentaje sobre presupuesto.')
    assert required_budget_variance(q) is None


@pytest.mark.parametrize('change',['missing','gap','conflicting','changed_definition'])
def test_budget_companion_is_required_complete_and_current(change):
    policy=sources(BUDGET,'Budgets Y Forecast')
    concept=sources(BUDGET_CONCEPT,'Conceptos FinOps Basicos',document='finops',width=180,step=100)
    if change=='missing':concept=[]
    if change=='gap':concept=[concept[-1]]
    if change=='conflicting':concept[1]['content']='X'+concept[1]['content'][1:]
    if change=='changed_definition':concept=sources(BUDGET_CONCEPT.replace('seguimiento y alertas','avisos supervisados'),'Conceptos FinOps Basicos',document='finops')
    bound=required_policy(catalog('¿Un presupuesto apaga recursos?',policy+concept))
    if change=='changed_definition':
        assert 'avisos supervisados' in bound['text'] and 'seguimiento y alertas' not in bound['text']
    else:assert bound is None


def investigation_sources(method='1. Confirmar scope y periodo. 2. Agrupar por servicio. 3. Bajar a resource group y resource.'):
    return sources('## Cost Management Y Cost Analysis Cost Analysis ayuda a analizar. Metodo basico para investigar un aumento de costes: '+method,
                   'Cost Management Y Cost Analysis',document='finops')


@pytest.mark.parametrize('question',['¿Por qué ha subido tanto el gasto?','¿Por qué aumentó el coste?','¿Cómo investigar un aumento de costes?'])
def test_investigation_does_not_promote_schema_fields_to_prerequisites(question):
    records=investigation_sources()+sources('## Modelo Conceptual Anomaly tiene root_cause y severity.','Modelo Conceptual',document='schema')
    q=catalog(question,records);bound=required_documentary_answer(q)
    value=candidate('documentary_answer',bound);wire=json.dumps(value);parser=SegmentAnswerJSON([],quantities=q)
    stream=''.join(parser.feed(wire[i:i+17]) for i in range(0,len(wire),17))
    public=assemble_chat_response(render_response(value,[],quantities=q),None,authorized_evidence=records)
    assert stream==parser.finish()==public['answer']
    assert all(word in stream for word in ('moneda','baseline','servicio','resource group'))
    assert 'root_cause' not in stream and 'severity' not in stream and 'requisitos previos' in stream
    assert public['next_actions'] and all(e['id'].startswith('finops:') for e in public['evidence'])


@pytest.mark.parametrize('damage',['gap','ambiguous','numeric','multiple_tasks','changed_steps'])
def test_investigation_requires_whole_method_and_conservative_scope(damage):
    question='¿Por qué ha subido tanto el gasto?';records=investigation_sources()
    if damage=='gap':records=[]
    if damage=='ambiguous':records+=sources(records[0]['content'].split(' ## Otra')[0],'Cost Management Y Cost Analysis',document='other')
    if damage=='numeric':question+='\n\nCoste 1200 EUR.'
    if damage=='multiple_tasks':question+=' Apaga máquinas.'
    if damage=='changed_steps':records=investigation_sources('1. Confirmar scope. 3. Investigar causa.')
    assert required_documentary_answer(catalog(question,records)) is None


def test_classification_rejection_logs_only_bounded_location(caplog):
    from app.core.chat_rules import ClassificationProseError
    from app.clients.chat_gateway import _record_diagnostic
    failure=ClassificationProseError('limitations',2)
    with caplog.at_level('WARNING'):
        _record_diagnostic('model_validation',failure,'a'*64,'stop',category='invalid_response')
    event=json.loads(caplog.records[-1].message)
    assert event['prose_location']=={'field':'limitations','item_index':2}
    assert event['rule_code']=='classification_unverified_prose' and event['exception_class']=='ValueError'
    assert 'input' not in event and 'candidate' not in event


def test_classification_guard_retains_location_without_retaining_prose():
    from app.core.chat_rules import ClassificationProseError
    q=catalog('Consulta conceptual.');q.rules=[{'intervals':[{'label':'rojo'}]}]
    renderer=ExpressionRenderer(q);renderer.prose_location=('next_actions',1)
    with pytest.raises(ClassificationProseError) as caught:
        renderer.check_prose('Clasificación roja: contenido privado que no se registra.')
    assert caught.value.field=='next_actions' and caught.value.index==1
    assert caught.value.args==('Unverified documentary classification prose.',)
    closed=ClassificationProseError('private-field-name',True)
    assert closed.field is None and closed.index is None


def test_services_keep_shared_compilers_identical():
    root=Path(__file__).resolve().parents[3]
    for name in ('chat_policy_sections','chat_documentary_decisions','chat_budget_comparison','chat_segments','chat_expressions','chat_rules'):
        assert (root/'apps/processor/app/core'/f'{name}.py').read_bytes()==(root/'apps/backend/app/core'/f'{name}.py').read_bytes()
