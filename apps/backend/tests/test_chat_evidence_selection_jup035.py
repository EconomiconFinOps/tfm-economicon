"""Generation constraints and the independent final evidence firewall."""
import copy
import importlib.util
import sys
from pathlib import Path

import pytest
from app.schemas.chat import _validate, provider_response_schema, validate_response, ResponseValidationError
from test_chat_operations_jup035 import ANSWER

SOURCE = {'id': 'corpus:authorized:0', 'kind': 'corpus', 'title': 'Synthetic policy',
          'source': 'Synthetic manual', 'content': 'A synthetic authorized rule.'}


def test_decision_schema_and_backend_validator_reject_invalid_branches():
    from app.core.chat_resources import DECISION_SCHEMA, validate_decision
    for value in ({'action':'none','query':None,'calculations':[]},{'action':'search','query':'a','calculations':[]}):
        _validate(value,DECISION_SCHEMA,DECISION_SCHEMA)
        assert validate_decision(value)==value
    for value in ({'action':'none','query':'a','calculations':[]},{'action':'search','query':None,'calculations':[]},
                  {'action':'search','query':'a','tenant':'other','calculations':[]}):
        with pytest.raises(ResponseValidationError): _validate(value,DECISION_SCHEMA,DECISION_SCHEMA)
        with pytest.raises(ValueError): validate_decision(value)


def candidate(evidence=()):
    value = copy.deepcopy(ANSWER)
    value['evidence'] = list(evidence)
    value['scope'].pop('period')
    value['scope'].pop('subscription_ids')
    return value


@pytest.mark.parametrize('problem', ['unknown', 'kind', 'title', 'source', 'foreign_tenant', 'foreign_user'])
def test_effective_schema_rejects_invalid_evidence_before_backend_firewall(problem):
    schema = provider_response_schema(authorized_evidence=[SOURCE])
    record = {key: SOURCE[key] for key in ('id', 'kind', 'title', 'source')}
    values = [record]
    if problem in ('unknown', 'foreign_tenant', 'foreign_user'): record['id'] = 'corpus:' + problem
    else: record[problem] = 'user_input' if problem == 'kind' else 'Altered provenance'
    with pytest.raises(ResponseValidationError):
        _validate(candidate(values), schema, schema)


def test_no_sources_allows_useful_greeting_but_no_invented_evidence_or_ok():
    schema = provider_response_schema(authorized_evidence=[])
    value = candidate()
    _validate(value, schema, schema)
    value['evidence'] = [{k: SOURCE[k] for k in ('id', 'kind', 'title', 'source')}]
    with pytest.raises(ResponseValidationError): _validate(value, schema, schema)
    value['evidence'] = []
    value['status'] = 'ok'
    with pytest.raises(ResponseValidationError): _validate(value, schema, schema)


def test_exact_authorized_source_is_allowed_and_contract_matches_processor():
    schema = provider_response_schema(authorized_evidence=[SOURCE])
    _validate(candidate([{**{k: SOURCE[k] for k in ('id', 'kind', 'title', 'source')},
                          'support_quote':SOURCE['content']}]), schema, schema)
    path = Path(__file__).parents[2] / 'processor/app/agents/schemas.py'
    spec = importlib.util.spec_from_file_location('processor_evidence_schema', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for sources in ([], [SOURCE]):
        for financial in (False, True):
            assert provider_response_schema(financial_metrics_allowed=financial, authorized_evidence=sources) == module.chat_provider_schema(financial_metrics_allowed=financial, authorized_evidence=sources)


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
