import copy
import json

import pytest

from app.core.chat_expressions import quantities
from app.core.chat_response_modes import REQUESTS
from app.core.chat_segments import render_response
from app.schemas.chat import provider_response_schema,_validate,ResponseValidationError


def candidate(answer,*,status=None):
    value={'schema_version':'1.0','scope':{'cloud':'azure','data_environment':'simulated'},
        'answer':answer,'evidence':[],'metrics':[],'recommendations':[],
        'assumptions':[],'limitations':[],'next_actions':[]}
    if status is not None:value['status']=status
    return value


@pytest.mark.parametrize('reason',list(REQUESTS))
def test_neutral_request_derives_status_and_useful_action_without_documentary_authority(reason):
    request={'reason':reason}
    if reason=='missing_documentation':request['missing_requirement']='La política de asignación aplicable.'
    value=candidate({'request':request})
    schema=provider_response_schema(authorized_evidence=[],quantities={})
    _validate(value,schema,schema)
    result=render_response(value,[],quantities={})
    assert result['status']==REQUESTS[reason][0]
    assert result['answer']==(REQUESTS[reason][1] if reason!='missing_documentation' else
        'Necesito contrastar este requisito específico para completar la consulta: La política de asignación aplicable.')
    assert result['next_actions']==[REQUESTS[reason][2]]
    assert result['evidence']==result['metrics']==result['recommendations']==[]
    assert 'status' not in value


@pytest.mark.parametrize('reason,terms',[
    ('authorized_cost_data',['fuente','autorizada','período']),
    ('ingestion_coverage',['Confirma la cobertura','ingesta']),
    ('execution_not_enabled',['análisis','propuesta revisable']),
])
def test_requests_have_concrete_next_step(reason,terms):
    result=render_response(candidate({'request':{'reason':reason}}),[],quantities={})
    assert all(term in result['next_actions'][0] for term in terms)


def test_complete_user_scenario_keeps_two_currencies_without_fabricating_operations():
    catalog=quantities('37 EUR y 42 USD')
    value=candidate({'scenario':{'calculations':[],'quantities':['37 EUR','42 USD']}},status='insufficient_data')
    schema=provider_response_schema(authorized_evidence=[],quantities=catalog)
    _validate(value,schema,schema)
    result=render_response(value,[],quantities=catalog)
    assert '37 EUR' in result['answer'] and '42 USD' in result['answer']
    assert 'moneda de destino' in result['answer'] and 'fecha' in result['answer']
    assert '+' not in result['answer'] and 'faltan' not in result['answer']
    assert result['next_actions']==[]


def test_narrative_requires_selected_source_even_for_insufficient_status():
    source={'id':'guide','kind':'corpus','title':'Guide','source':'guide','content':'Actual cost reflects billing.'}
    value=candidate([{'text':'El método documentado dice...'}],status='insufficient_data')
    schema=provider_response_schema(authorized_evidence=[source],quantities={})
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    with pytest.raises(ValueError,match='selected evidence'):render_response(value,[],quantities={})
    value['evidence']=[{key:source[key] for key in ('id','kind','title','source')}|{'support_quote':source['content']}]
    _validate(value,schema,schema)
    assert render_response(value,[],quantities={})['answer']=='El método documentado dice...'


@pytest.mark.parametrize('change',[
    {'status':'ok'}, {'answer':{'request':{'reason':'invented'}}},
    {'next_actions':[[{'text':'Unverified assertion'}]]}, {'metrics':[{'name':'cost'}]},
])
def test_request_cannot_override_authority_status_or_add_free_claims(change):
    value=candidate({'request':{'reason':'clarification'}})|copy.deepcopy(change)
    schema=provider_response_schema(authorized_evidence=[],quantities={})
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    with pytest.raises(ValueError):render_response(value,[],quantities={})


def test_scenario_schema_and_local_guard_exclude_documentary_operands():
    catalog=quantities('37 EUR y 5 EUR')
    catalog['5 EUR']['provenance']=[{'kind':'corpus','id':'guide'}]
    value=candidate({'scenario':{'calculations':[{'operation':'difference',
        'current':{'quantity':'37 EUR'},'baseline':{'quantity':'5 EUR'}}],'quantities':[]}},status='insufficient_data')
    schema=provider_response_schema(authorized_evidence=[],quantities=catalog)
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    with pytest.raises(ValueError,match='documentary operands'):render_response(value,[],quantities=catalog)


def test_explanatory_scenario_keeps_user_labels_scope_and_calculation():
    catalog=quantities('Workspace sandbox-z, marzo. Compute 72 EUR; Network 28 EUR.')
    value=candidate({'scenario':{'segments':[
        {'text':'En marzo, para sandbox-z, Compute es la categoría de mayor coste aportado. Total: '},
        {'expression':{'operation':'sum','left':{'quantity':'72 EUR'},'right':{'quantity':'28 EUR'}}},
    ]}},status='insufficient_data')
    schema=provider_response_schema(authorized_evidence=[],quantities=catalog)
    _validate(value,schema,schema)
    result=render_response(value,[],quantities=catalog)
    assert all(text in result['answer'] for text in ('hipotético','marzo','sandbox-z','Compute','100 EUR'))
    assert result['evidence']==result['metrics']==result['recommendations']==[]
    for field in ('metrics','recommendations','evidence'):
        bad=copy.deepcopy(value);bad[field]=[{'id':'invented'}]
        with pytest.raises(ResponseValidationError):_validate(bad,schema,schema)
        with pytest.raises(ValueError):render_response(bad,[],quantities=catalog)


@pytest.mark.parametrize('segments',[
    [{'text':'7 + '},{'text':'2 = 100'}],
    [{'text':'[[ca'},{'text':'lc:0]]'}],
    [{'quantity':'document:guide:5 EUR'}],
])
def test_explanatory_scenario_preserves_equation_protocol_and_source_guards(segments):
    catalog=quantities('7 EUR y 2 EUR')
    catalog['document:guide:5 EUR']={'value':'5','unit':'EUR','source':'5 EUR',
        'provenance':[{'kind':'corpus','id':'guide'}]}
    value=candidate({'scenario':{'segments':segments}},status='insufficient_data')
    with pytest.raises(ValueError):render_response(value,[],quantities=catalog)


@pytest.mark.parametrize('requirement',['','   ','x'*301,'7 + 2 = 100','[[calc:0]]'])
def test_missing_documentation_rejects_empty_long_or_unverified_requirement(requirement):
    value=candidate({'request':{'reason':'missing_documentation','missing_requirement':requirement}})
    with pytest.raises(ValueError):render_response(value,[],quantities={})


def test_specific_documentary_request_remains_available_with_irrelevant_retrieval():
    source={'id':'unrelated','kind':'corpus','title':'Manual','source':'manual','content':'The interface has a dark theme.'}
    value=candidate({'request':{'reason':'missing_documentation','missing_requirement':'El criterio de reparto de costes compartidos.'}})
    schema=provider_response_schema(authorized_evidence=[source],quantities={})
    _validate(value,schema,schema)
    result=render_response(value,[],quantities={})
    assert 'criterio de reparto' in result['answer']
    assert result['evidence']==result['metrics']==[]
    for request in ({'reason':'missing_documentation'},
        {'reason':'clarification','missing_requirement':'unneeded'},
        {'reason':'missing_documentation','missing_requirement':'criterion','extra':True}):
        bad=candidate({'request':request})
        with pytest.raises(ResponseValidationError):_validate(bad,schema,schema)
        with pytest.raises(ValueError):render_response(bad,[],quantities={})


@pytest.mark.parametrize('current,unit,expected',[('73','EUR','73 EUR'),('-12','EUR','-12 EUR'),('7','%','7 puntos porcentuales')])
def test_zero_baseline_relative_change_also_explains_absolute_difference(current,unit,expected):
    from app.core.chat_expressions import ExpressionRenderer
    catalog=quantities(f'{current} {unit} y 0 {unit}')
    result=ExpressionRenderer(catalog).render({'operation':'relative_change',
        'current':{'quantity':f'{current} {unit}'},'baseline':{'quantity':f'0 {unit}'}})
    assert 'indefinida' in result and 'Diferencia absoluta = '+expected in result
