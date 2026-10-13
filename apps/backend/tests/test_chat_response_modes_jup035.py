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
    value=candidate({'request':{'reason':reason}})
    schema=provider_response_schema(authorized_evidence=[],quantities={})
    _validate(value,schema,schema)
    result=render_response(value,[],quantities={})
    assert result['status']==REQUESTS[reason][0]
    assert result['answer']==REQUESTS[reason][1]
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
