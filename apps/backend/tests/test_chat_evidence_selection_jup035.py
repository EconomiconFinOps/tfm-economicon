"""Generation constraints and the independent final evidence firewall."""
import copy
import importlib.util
import sys
import json
from pathlib import Path

import pytest
from app.schemas.chat import _validate, provider_response_schema, validate_response, ResponseValidationError
from test_chat_operations_jup035 import ANSWER

SOURCE = {'id': 'corpus:authorized:0', 'kind': 'corpus', 'title': 'Synthetic policy',
          'source': 'Synthetic manual', 'content': 'A synthetic authorized rule.'}


def test_simple_decision_schema_keeps_branch_coherence_in_local_validator():
    from app.core.chat_resources import DECISION_SCHEMA, validate_search_call
    value={'action':'search','query':'a'}
    _validate(value,DECISION_SCHEMA,DECISION_SCHEMA)
    assert validate_search_call(value)[1]=='a'
    for value in ({'action':'none','query':'a'},{'action':'search','query':None},
                  {'action':'search','query':'a','tenant':'other'}):
        with pytest.raises(ValueError):validate_search_call(value)
    assert 'anyOf' not in DECISION_SCHEMA
    with pytest.raises(ResponseValidationError):
        _validate({'action':'none','query':None,'comparisons':[],'calculations':[],'tenant':'other'},DECISION_SCHEMA,DECISION_SCHEMA)


def test_contextual_decision_schema_enforces_exact_source_enum_and_disabled_plan():
    from app.core.chat_expressions import quantities,ExpressionRenderer
    catalog=quantities('73 EUR/día y 20 EUR/día.')
    schema=provider_response_schema(quantities=catalog,authorized_evidence=[])
    value=candidate();value['status']='insufficient_data';value['limitations']=[]
    expression={'operation':'difference',
        'current':{'quantity':'73 EUR/día'},'baseline':{'quantity':'20 EUR/día'}}
    value['basis']='user_scenario'
    value['answer']=[{'expression':expression}]
    _validate(value,schema,schema)
    for operand in ('100 EUR/día','73 EUR'):
        expression['current']['quantity']=operand
        with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
        with pytest.raises(ValueError):ExpressionRenderer(catalog).render(expression)
    expression['current']['quantity']='73 EUR/día'
    disabled=provider_response_schema(quantities={},authorized_evidence=[])
    with pytest.raises(ResponseValidationError):_validate(value,disabled,disabled)
    value['answer']=[{'expression':{'quantity':'73 EUR/día'}}]
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)
    with pytest.raises(ValueError,match='requires an operation'):
        ExpressionRenderer(catalog).render(value['answer'][0]['expression'])


def test_contextual_schema_hash_and_full_token_accounting_match_both_services():
    from dataclasses import replace
    from app.core.chat_resources import load_resources,decision_schema
    from app.schemas.chat import canonical
    from app.db.chat_repository import ChatError
    root=Path(__file__).parents[2]/'processor/app/agents/prompt_resources/jup035/chat/v3'
    backend=load_resources(root,root.parent/'v2/tokenizer.json')
    path=Path(__file__).parents[2]/'processor/app/core/chat_resources.py'
    spec=importlib.util.spec_from_file_location('processor_counted_decision',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    processor=module.ChatResources(backend.prompt_version,backend.system,'', '',backend.schema_sha256,
        backend.manifest_bytes,backend._tokenizer)
    messages=[{'role':'system','content':backend.system},{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({
        'question':'Importes EUR/día '+', '.join(str(i) for i in range(64))})}]
    context={'messages':messages}
    from app.core.chat_expressions import context_quantities
    catalog=context_quantities(context)
    schema=decision_schema(context);final_schema=provider_response_schema(quantities=catalog)
    assert schema==module.decision_schema(context)
    assert backend.count_messages(messages)==processor.check_messages(messages,final_schema)
    assert backend.metadata(backend.count_messages(messages),messages)['decision_schema_sha256']==module.sha(module.canonical(schema))
    required=sum(backend.count(canonical(value)) for value in (messages,final_schema))+1024+11000
    assert required<backend.context_budget['context_tokens']
    limited={**backend.context_budget,'context_tokens':required-1}
    with pytest.raises(ChatError):replace(backend,context_budget=limited).count_messages(messages)
    with pytest.raises(module.TokenBudgetExceeded):replace(processor,context_budget=limited).check_messages(messages,final_schema)
    quoted=provider_response_schema(authorized_evidence=[SOURCE],quantities=catalog)
    assert backend.count_messages(messages,authorized_evidence=[SOURCE])==processor.check_messages(messages,quoted)
    required=sum(backend.count(canonical(value)) for value in (messages,quoted))+1024+11000
    limited={**backend.context_budget,'context_tokens':required-1}
    with pytest.raises(ChatError):replace(backend,context_budget=limited).count_messages(messages,authorized_evidence=[SOURCE])
    with pytest.raises(module.TokenBudgetExceeded):replace(processor,context_budget=limited).check_messages(messages,quoted)

    source={**SOURCE,'content':'Synthetic experimental threshold: 17%.'}
    messages=messages+[{'role':'user','content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':[source]})}]
    catalog=context_quantities({'messages':messages,'authorized_evidence':[source]})
    assert 'document:corpus:authorized:0:17 %' in catalog
    final_schema=provider_response_schema(authorized_evidence=[source],quantities=catalog)
    assert backend.count_messages(messages,authorized_evidence=[source])==processor.check_messages(messages,final_schema)
    with pytest.raises(ValueError,match='not authorized'):
        backend.count_messages(messages,authorized_evidence=[])


def candidate(evidence=(),source=None):
    value=copy.deepcopy(ANSWER)
    value['evidence']=list(evidence)
    value['scope'].pop('period');value['scope'].pop('subscription_ids')
    value['answer']=[{'inference':value['answer']}]
    if source is not None:
        from app.core.chat_claims import passages
        value['answer']=[{'documentary':{'source_id':source['id'],'passage':passages(source['content'])[0]}}]
    value['basis']='authorized_evidence'
    for field in ('assumptions','limitations','next_actions'):
        value[field]=[[{'inference':item}] for item in value[field]]
    return value


@pytest.mark.parametrize('problem',['unknown','kind','title','source','foreign_tenant','foreign_user','passage'])
def test_effective_schema_rejects_invalid_evidence_before_backend_firewall(problem):
    schema=provider_response_schema(authorized_evidence=[SOURCE])
    value=candidate(source=SOURCE)
    _validate(value,schema,schema)
    selection=value['answer'][0]['documentary']
    if problem in ('unknown','foreign_tenant','foreign_user'):selection['source_id']='corpus:'+problem
    elif problem=='passage':selection['passage']='Invented quote.'
    else:selection[problem]='Altered provenance'
    with pytest.raises(ResponseValidationError):_validate(value,schema,schema)


def test_no_sources_allows_useful_greeting_but_no_invented_evidence_or_ok():
    schema = provider_response_schema(authorized_evidence=[])
    value = candidate()
    value['status']='no_data'
    value['basis']='greeting'
    value['answer'] = [{'text':'Hola. ¿Qué consulta FinOps necesitas resolver?'}]
    value['limitations'] = []
    _validate(value, schema, schema)
    value['evidence'] = [{k: SOURCE[k] for k in ('id', 'kind', 'title', 'source')}]
    with pytest.raises(ResponseValidationError): _validate(value, schema, schema)
    value['evidence'] = []
    value['status'] = 'ok'
    with pytest.raises(ResponseValidationError): _validate(value, schema, schema)


def test_exact_authorized_source_is_allowed_and_contract_matches_processor():
    schema = provider_response_schema(authorized_evidence=[SOURCE])
    _validate(candidate(source=SOURCE),schema,schema)
    path = Path(__file__).parents[2] / 'processor/app/agents/schemas.py'
    spec = importlib.util.spec_from_file_location('processor_evidence_schema', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for sources in ([], [SOURCE]):
        for financial in (False, True):
            for records in ([],[{'id':'0','equation':'3 + 4 = 7','value':'7','unit':'','hypothetical':True}]):
                assert provider_response_schema(financial_metrics_allowed=financial, authorized_evidence=sources,calculations=records) == module.chat_provider_schema(financial_metrics_allowed=financial, authorized_evidence=sources,calculations=records)


@pytest.mark.parametrize('problem,rule', [('unknown','evidence_unknown_id'), ('duplicate','evidence_duplicate_id'), ('source','evidence_provenance')])
def test_independent_backend_firewall_keeps_rejecting_and_distinguishes_causes(problem, rule):
    value = copy.deepcopy(ANSWER)
    record = {k: SOURCE[k] for k in ('id', 'kind', 'title', 'source')}
    value['evidence'] = [record]
    if problem == 'unknown': record['id'] = 'foreign'
    elif problem == 'duplicate': value['evidence'].append(copy.deepcopy(record))
    else: record['source'] = 'Altered source'
    with pytest.raises(ResponseValidationError) as failure: validate_response(value, [SOURCE])
    assert failure.value.rule_code == rule


def test_provider_projection_omits_unsupported_uniqueness_but_processor_rejects_duplicates():
    import json
    from pydantic import ValidationError
    path = Path(__file__).parents[2] / 'processor/app/agents/schemas.py'
    spec = importlib.util.spec_from_file_location('processor_duplicate_schema', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for sources in ([], [SOURCE]):
        for financial in (False, True):
            schema = provider_response_schema(financial_metrics_allowed=financial, authorized_evidence=sources)
            assert 'uniqueItems' not in json.dumps(schema)
    record = {key: SOURCE[key] for key in ('id', 'kind', 'title', 'source')}
    value = copy.deepcopy(ANSWER)
    value['evidence'] = [record, copy.deepcopy(record)]
    with pytest.raises(ValidationError, match='evidence ids must be unique'):
        module.FinOpsResponse.model_validate(value)


@pytest.mark.parametrize('financial',[False,True])
def test_narrative_union_preserves_root_constraints_and_neutral_branch_is_distinct(financial):
    source={**SOURCE,'content':('A literal rule > 20 AND amount > 100; '*20)[:500]}
    schema=provider_response_schema(financial_metrics_allowed=financial,authorized_evidence=[source])
    assert set(schema)=={'type','anyOf','$defs'}
    assert all(branch['additionalProperties'] is False for branch in schema['anyOf'])
    narratives=[branch for branch in schema['anyOf'] if branch['properties']['basis']['const']=='authorized_evidence']
    assert len(narratives)==2
    root=copy.deepcopy(narratives[1]);root['$defs']=schema['$defs']
    root['properties']['status']={'type':'string','enum':['ok','partial','no_data','insufficient_data','unsupported','refused','error']}
    for branch in narratives:
        reconstructed=copy.deepcopy(root);reconstructed.pop('$defs')
        reconstructed['properties']['status']=branch['properties']['status']
        assert reconstructed==branch
    def accepts(value,rule):
        try:_validate(value,rule,schema);return True
        except ValueError:return False
    for status in root['properties']['status']['enum']:
        value=candidate(source=source);value['status']=status
        variants=[value]
        for key in ('answer','scope','evidence'):
            bad=copy.deepcopy(value);bad.pop(key);variants.append(bad)
        bad=copy.deepcopy(value);bad['extra']='rejected';variants.append(bad)
        for field,replacement in [('source_id','foreign'),('passage','Invented or paraphrased quote'),('title','Forged title')]:
            bad=copy.deepcopy(value);bad['answer'][0]['documentary'][field]=replacement;variants.append(bad)
        bad=copy.deepcopy(value);bad['evidence']=[{key:source[key] for key in ('id','kind','title','source')}];variants.append(bad)
        bad=copy.deepcopy(value);bad['scope']['period']=None;variants.append(bad)
        bad=copy.deepcopy(value);bad['metrics']=[{'name':'cost','value':'1','unit':'EUR','evidence_ids':[source['id']]}];variants.append(bad)
        for item in variants:
            assert accepts(item,schema)==(accepts(item,root) and any(accepts(item,b) for b in narratives))
        assert accepts(value,schema)
        assert all(not accepts(item,schema) for item in variants[1:-1])
        assert accepts(variants[-1],schema)==financial
    neutral=candidate();neutral.update(status='insufficient_data',basis='clarification',answer=[{'inference':'Necesito concretar la consulta.'}],limitations=[])
    neutral['next_actions']=[[{'inference':'Indica el período y el ámbito.'}]]
    assert accepts(neutral,schema) and not accepts(neutral,root)
    for change in ({'status':'ok'},{'answer':{'request':{'reason':'clarification'}}},{'basis':'unknown'}):
        assert not accepts({**neutral,**change},schema)
    for basis,status in [('missing_data','insufficient_data'),('clarification','insufficient_data'),('refusal','refused')]:
        documented={**neutral,'basis':basis,'status':status,'answer':candidate(source=source)['answer']}
        assert accepts(documented,schema)
        assert accepts({**documented,'answer':neutral['answer']},schema)
        for field,replacement in [('source_id','foreign'),('title','Altered title'),('source','Altered source'),('passage','Invented quote')]:
            bad=copy.deepcopy(documented);bad['answer'][0]['documentary'][field]=replacement
            assert not accepts(bad,schema)
        assert not accepts({**documented,'metrics':[{'name':'cost','value':'1','unit':'EUR','evidence_ids':[source['id']]}]},schema)
        assert not accepts({**documented,'recommendations':[{}]},schema)
