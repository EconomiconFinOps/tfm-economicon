"""Closed public request and derived canonical response validation (JUP-035)."""
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.chat_screen import ScreenCapture


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    content: str = Field(min_length=1,max_length=16384)
    screen_context: dict
    retry_of_operation_id: UUID | None = None

    @field_validator('content')
    @classmethod
    def question(cls,value):
        if not value.strip() or len(value.encode('utf-8')) > 16384:
            raise ValueError('Invalid question.')
        return value

    @field_validator('screen_context')
    @classmethod
    def screen(cls,value):
        ScreenCapture.model_validate(value)
        if len(canonical(value).encode('utf-8')) > 1048576:
            raise ValueError('Screen is too large.')
        return value


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


SCHEMA_PATH = Path(__file__).with_name('finops_response_v1.json')


class ResponseValidationError(ValueError):
    """Internal closed rule identifier; no rejected values in diagnostics."""
    def __init__(self, rule_code):
        self.rule_code = rule_code
        super().__init__('Invalid response.')


def response_schema():
    raw = SCHEMA_PATH.read_bytes()
    schema = json.loads(raw)
    return schema, hashlib.sha256(canonical(schema).encode()).hexdigest()


def _bind_chat_evidence(schema, authorized_evidence):
    """Constrain generation to exact records from this authenticated attempt.

    This is a generation constraint, not a substitute for the backend firewall.
    None builds the static manifest template; [] authorizes no citations.
    """
    if authorized_evidence is None:
        return schema
    if not isinstance(authorized_evidence, list) or len(authorized_evidence) > 20:
        raise ValueError('Invalid authorized evidence.')
    choices, identifiers = [], set()
    for source in authorized_evidence:
        if not isinstance(source, dict):
            raise ValueError('Invalid authorized evidence.')
        fields = {key: source.get(key) for key in ('id', 'kind', 'title', 'source')}
        if (any(type(value) is not str or not value for value in fields.values())
                or fields['id'] in identifiers):
            raise ValueError('Invalid authorized evidence.')
        identifiers.add(fields['id'])
        choice = copy.deepcopy(schema['$defs']['Evidence'])
        for key, value in fields.items():
            rule = choice['properties'][key]
            if '$ref' in rule:
                rule = copy.deepcopy(schema['$defs'][rule['$ref'].removeprefix('#/$defs/')])
                choice['properties'][key] = rule
            rule['const'] = value
        choices.append(choice)
    # The endpoint rejects uniqueItems; processor and backend reject duplicates
    # independently after generation. Keep exact provenance constraints here.
    if choices:
        schema['$defs']['Evidence'] = {'anyOf': choices}
    else:
        # No unsatisfiable actionable branch and no fabricated citation to satisfy it.
        abstention = schema['anyOf'][1]
        abstention['properties']['evidence']['maxItems'] = 0
        schema = {**abstention, '$defs': schema['$defs']}
    return schema


def provider_response_schema(*, financial_metrics_allowed=False, authorized_evidence=None):
    if type(financial_metrics_allowed) is not bool:
        raise ValueError('Invalid financial authority control.')
    schema, _ = response_schema()
    scope = schema['$defs']['ResponseScope']
    scope['properties'].pop('period')
    scope['required'].remove('period')
    scope['properties'].pop('subscription_ids')
    scope['required'].remove('subscription_ids')
    schema['$defs'].pop('Period')
    if not financial_metrics_allowed:
        schema['properties']['metrics']['maxItems'] = 0
    # Complete branches preserve every base constraint, sharing root definitions.
    branch_base = {key: value for key, value in schema.items() if key != '$defs'}
    actionable = copy.deepcopy(branch_base)
    abstention = copy.deepcopy(branch_base)
    actionable['properties']['status'] = {'type': 'string', 'enum': ['ok', 'partial']}
    actionable['properties']['evidence']['minItems'] = 1
    abstention['properties']['status'] = {'type': 'string', 'enum': [
        status for status in schema['$defs']['ResponseStatus']['enum']
        if status not in ('ok', 'partial')]}
    schema['anyOf'] = [actionable, abstention]
    return _bind_chat_evidence(schema, authorized_evidence)


def _validate(value, rule, schema, depth=0):
    if depth > 32:
        raise ResponseValidationError('schema_depth')
    if '$ref' in rule:
        name = rule['$ref'].removeprefix('#/$defs/')
        return _validate(value,schema['$defs'][name],schema,depth+1)
    if 'anyOf' in rule:
        for alternative in rule['anyOf']:
            try:
                _validate(value,alternative,schema,depth+1)
                return
            except (ValueError,TypeError):
                pass
        raise ResponseValidationError('schema_union')
    kind = rule.get('type')
    valid = {'object':isinstance(value,dict),'array':isinstance(value,list),
             'string':isinstance(value,str),'boolean':type(value) is bool,
             'integer':type(value) is int,'number':type(value) in (int,float) and math.isfinite(value),
             'null':value is None}
    if kind is not None and not valid.get(kind,False):
        raise ResponseValidationError('schema_type')
    if 'enum' in rule and value not in rule['enum'] or 'const' in rule and value != rule['const']:
        raise ResponseValidationError('schema_enum')
    if kind == 'object':
        if set(rule.get('required',[]))-value.keys():
            raise ResponseValidationError('schema_required')
        props = rule.get('properties',{})
        if rule.get('additionalProperties') is False and value.keys()-props.keys():
            raise ResponseValidationError('schema_extra')
        for key,item in value.items():
            if key in props:
                _validate(item,props[key],schema,depth+1)
    if kind == 'array':
        if len(value)<rule.get('minItems',0) or len(value)>rule.get('maxItems',100000):
            raise ResponseValidationError('schema_array')
        if rule.get('uniqueItems') is True and len({canonical(item) for item in value}) != len(value):
            raise ResponseValidationError('schema_unique')
        for item in value:
            _validate(item,rule.get('items',{}),schema,depth+1)
    if kind == 'string':
        if len(value)<rule.get('minLength',0) or len(value)>rule.get('maxLength',1048576):
            raise ResponseValidationError('schema_text')
        if rule.get('pattern') and re.search(rule['pattern'],value) is None:
            raise ResponseValidationError('schema_format')
        if rule.get('format') == 'date':
            from datetime import date
            try:
                date.fromisoformat(value)
            except ValueError:
                raise ResponseValidationError('schema_date') from None


def validate_response(value, authorized_evidence, *, expected_period=..., expected_subscriptions=...):
    schema,_ = response_schema()
    _validate(value,schema,schema)
    known = {item['id']:item for item in authorized_evidence}
    returned = {item['id']:item for item in value['evidence']}
    if len(returned) != len(value['evidence']):
        raise ResponseValidationError('evidence_duplicate_id')
    if returned.keys()-known.keys():
        raise ResponseValidationError('evidence_unknown_id')
    for key,item in returned.items():
        if any(item[field] != known[key].get(field) for field in ['kind','source','title']):
            raise ResponseValidationError('evidence_provenance')
    if value['status'] in ['ok','partial'] and not returned:
        raise ResponseValidationError('actionable_requires_evidence')
    if value['status'] in ['no_data','insufficient_data','unsupported','refused','error'] and (value['metrics'] or value['recommendations']):
        raise ResponseValidationError('non_actionable_payload')
    for metric in value['metrics']:
        if set(metric['evidence_ids'])-returned.keys():
            raise ResponseValidationError('metric_reference')
        # Financial numbers must match values in the authorized server record.
        eligible = [known[x] for x in metric['evidence_ids'] if known[x]['kind']=='cost_query']
        if not any({'name':metric['name'],'value':metric['value'],'unit':metric['unit']} in e.get('metrics',[]) for e in eligible):
            raise ResponseValidationError('financial_metric_unverified')
    for recommendation in value['recommendations']:
        if set(recommendation['evidence_ids'])-returned.keys():
            raise ResponseValidationError('recommendation_reference')
        if (recommendation['estimated_savings'] is None) != (recommendation['currency'] is None):
            raise ResponseValidationError('savings_currency')
        if recommendation['estimated_savings'] is not None:
            raise ResponseValidationError('savings_out_of_scope')
    period = value['scope']['period']
    if expected_period is not ... and period != expected_period:
        raise ResponseValidationError('period_context')
    if period and period['from'] >= period['to']:
        raise ResponseValidationError('period_order')
    if expected_subscriptions is not ... and value['scope']['subscription_ids'] != expected_subscriptions:
        raise ResponseValidationError('subscription_context')
    return value


def reported_usage(value):
    """Closed diagnostic receipt, never a bill estimate or inferred cache hit."""
    from decimal import Decimal, InvalidOperation
    if not isinstance(value, dict): return None
    result = {key: value[key] for key in ('prompt_tokens','completion_tokens','total_tokens')
              if type(value.get(key)) is int and value[key] >= 0}
    if (all(key in result for key in ('prompt_tokens','completion_tokens','total_tokens'))
            and result['prompt_tokens'] + result['completion_tokens'] != result['total_tokens']):
        return None
    cost = value.get('cost_usd')
    if type(cost) in (str,int,float) or isinstance(cost,Decimal):
        raw = str(cost)
        if len(raw) <= 128:
            try:
                amount = Decimal(raw)
                if amount.is_finite() and amount >= 0 and -100 <= amount.as_tuple().exponent <= 100:
                    fixed = format(amount,'f')
                    if len(fixed) <= 128: result['cost_usd'] = fixed
            except (ValueError,InvalidOperation): pass
    return result or None


def response_citations(value, context):
    """Use only the server-resolved frozen records for returned corpus evidence."""
    from app.schemas.assistant import SourceCitation
    known = {item['id']:item for item in context.get('authorized_evidence',[])}
    frozen = context.get('source_citations',[])
    selected = []
    for evidence in value['evidence']:
        if evidence['kind'] != 'corpus': continue
        if not isinstance(frozen,list): raise ResponseValidationError('citation_snapshot')
        matches = [item for item in frozen if isinstance(item,dict) and item.get('evidence_id') == evidence['id']]
        if len(matches) != 1: raise ResponseValidationError('citation_unresolved')
        citation = SourceCitation.model_validate(matches[0]).model_dump()
        source = known[evidence['id']]
        if (citation['title'] != source['title'].strip() or citation['source'] != source['source'].strip()
                or not isinstance(source.get('content'),str) or citation['excerpt'] != source['content'][:140]):
            raise ResponseValidationError('citation_provenance')
        selected.append(citation)
    return [item['evidence_id'] for item in selected], selected
