import copy
import pytest
from app.core.chat_expressions import quantities,ExpressionRenderer
from app.core.chat_response_modes import BASIS_STATUSES,USER_PREFIX
from app.core.chat_segments import render_response
from app.schemas.chat import provider_response_schema,_validate,ResponseValidationError


def candidate(answer,*,basis='user_scenario',status='insufficient_data',next_actions=None):
    return {'schema_version':'1.0','scope':{'cloud':'azure','data_environment':'simulated'},
        'basis':basis,'status':status,'answer':answer,'evidence':[],'metrics':[],
        'recommendations':[],'assumptions':[],'limitations':[],'next_actions':next_actions or []}


@pytest.mark.parametrize('basis',list(BASIS_STATUSES))
def test_unified_basis_derives_no_authority_and_is_removed_from_public_response(basis):
    value=candidate([{'text':'Una respuesta concreta.'}],basis=basis,status=BASIS_STATUSES[basis][0],
        next_actions=[[{'text':'Aporta el ámbito y la fuente aplicable.'}]] if basis in ('missing_data','clarification','refusal') else [])
    schema=provider_response_schema(authorized_evidence=[],quantities={})
    _validate(value,schema,schema)
    result=render_response(value,[],quantities={})
    assert 'basis' not in result and result['status']==value['status']
    assert result['answer']==(USER_PREFIX if basis=='user_scenario' else '')+'Una respuesta concreta.'
    assert result['evidence']==result['metrics']==result['recommendations']==[]


def test_explanatory_scenario_keeps_user_labels_scope_and_calculation():
    catalog=quantities('Workspace sandbox-z, marzo. Compute 72 EUR; Network 28 EUR.')
    value=candidate([{'text':'En marzo, para sandbox-z, Compute es la categoría de mayor coste aportado. Total: '},
        {'expression':{'operation':'sum','left':{'quantity':'72 EUR'},'right':{'quantity':'28 EUR'}}}])
    schema=provider_response_schema(authorized_evidence=[],quantities=catalog)
    _validate(value,schema,schema)
    result=render_response(value,[],quantities=catalog)
    assert all(text in result['answer'] for text in ('hipotético','marzo','sandbox-z','Compute','100 EUR'))
    for field in ('metrics','recommendations','evidence'):
        bad=copy.deepcopy(value);bad[field]=[{'id':'invented'}]
        with pytest.raises(ResponseValidationError):_validate(bad,schema,schema)
        with pytest.raises(ValueError):render_response(bad,[],quantities=catalog)


@pytest.mark.parametrize('segments',[
    [{'text':'7 + '},{'text':'2 = 100'}],
    [{'text':'[[ca'},{'text':'lc:0]]'}],
    [{'quantity':'document:guide:5 EUR'}],
])
def test_unified_unverified_basis_preserves_equation_protocol_and_source_guards(segments):
    catalog=quantities('7 EUR y 2 EUR')
    catalog['document:guide:5 EUR']={'value':'5','unit':'EUR','source':'5 EUR','provenance':[{'kind':'corpus','id':'guide'}]}
    with pytest.raises(ValueError):render_response(candidate(segments),[],quantities=catalog)


@pytest.mark.parametrize('basis',('missing_data','clarification','refusal'))
def test_missing_or_refused_response_requires_useful_next_action(basis):
    value=candidate([{'text':'Falta una fuente aplicable.'}],basis=basis,status=BASIS_STATUSES[basis][0],
        next_actions=[[{'text':'Aporta la fuente y el ámbito.'}]])
    source={'id':'unrelated','kind':'corpus','title':'Manual','source':'manual','content':'The interface has a dark theme.'}
    schema=provider_response_schema(authorized_evidence=[source],quantities={})
    _validate(value,schema,schema)
    assert 'fuente' in render_response(value,[],quantities={})['next_actions'][0]
    value['next_actions']=[]
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    with pytest.raises(ValueError):render_response(value,[],quantities={})


@pytest.mark.parametrize('answer',[
    {'request':{'reason':'clarification'}},
    {'request':{'reason':'missing_documentation','missing_requirement':'policy'}},
    {'scenario':{'quantities':['7 EUR'],'calculations':[]}},
    {'scenario':{'segments':[{'text':'legacy'}]}},
])
def test_old_private_modes_are_not_generative_routes(answer):
    value=candidate(answer);value.pop('basis')
    catalog=quantities('7 EUR')
    schema=provider_response_schema(authorized_evidence=[],quantities=catalog)
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    with pytest.raises(ValueError):render_response(value,[],quantities=catalog)


@pytest.mark.parametrize('change',[{'basis':'unknown'},{'status':'ok'},{'basis':None},{'extra':True}])
def test_invalid_basis_or_authority_is_rejected(change):
    value=candidate([{'text':'Escenario.'}]);schema=provider_response_schema(authorized_evidence=[],quantities={})
    _validate(value,schema,schema)
    value.update(change)
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    if 'extra' not in change:
        with pytest.raises(ValueError):render_response(value,[],quantities={})


def test_authorized_narrative_requires_selected_evidence_even_when_insufficient():
    source={'id':'guide','kind':'corpus','title':'Guide','source':'guide','content':'Actual cost reflects billing.'}
    value=candidate([{'text':'El coste actual refleja facturación.'}],basis='authorized_evidence')
    schema=provider_response_schema(authorized_evidence=[source],quantities={})
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    with pytest.raises(ValueError):render_response(value,[],quantities={})
    value['evidence']=[{key:source[key] for key in ('id','kind','title','source')}|{'support_quote':source['content']}]
    _validate(value,schema,schema)
    assert render_response(value,[],quantities={})['answer']=='El coste actual refleja facturación.'


@pytest.mark.parametrize('current,unit,expected',[('73','EUR','73 EUR'),('-12','EUR','-12 EUR'),('7','%','7 puntos porcentuales')])
def test_zero_baseline_relative_change_also_explains_absolute_difference(current,unit,expected):
    catalog=quantities(f'{current} {unit} y 0 {unit}')
    result=ExpressionRenderer(catalog).render({'operation':'relative_change',
        'current':{'quantity':f'{current} {unit}'},'baseline':{'quantity':f'0 {unit}'}})
    assert 'indefinida' in result and 'Diferencia absoluta = '+expected in result


def test_user_scenario_preserves_two_currencies_without_fabricating_a_conversion():
    catalog=quantities('Servicio A: 37 EUR. Servicio B: 42 USD.')
    value=candidate([{'text':'Importes aportados por separado: '},{'quantity':'37 EUR'},
        {'text':' y '},{'quantity':'42 USD'},{'text':'. Para convertirlos faltan destino, tipo y fecha.'}])
    schema=provider_response_schema(authorized_evidence=[],quantities=catalog)
    _validate(value,schema,schema)
    rendered=render_response(value,[],quantities=catalog)
    assert '37 EUR' in rendered['answer'] and '42 USD' in rendered['answer']
    assert '79' not in rendered['answer'] and rendered['evidence']==[]
    # Guidance is model prose, not a server guarantee; arithmetic remains guarded.
    bad=copy.deepcopy(value)
    bad['answer']=[{'expression':{'operation':'sum','left':{'quantity':'37 EUR'},'right':{'quantity':'42 USD'}}}]
    result=render_response(bad,[],quantities=catalog)
    assert 'no agregable sin una conversión de divisa autorizada' in result['answer']
    assert '79' not in result['answer']
    bad['answer']=[{'quantity':'37 USD'}]
    with pytest.raises(ResponseValidationError):_validate(bad,schema,schema)
    with pytest.raises(ValueError):render_response(bad,[],quantities=catalog)
