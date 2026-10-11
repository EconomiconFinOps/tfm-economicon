"""Closed public request and derived canonical response validation (JUP-035)."""
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


def response_schema():
    raw = SCHEMA_PATH.read_bytes()
    schema = json.loads(raw)
    return schema, hashlib.sha256(canonical(schema).encode()).hexdigest()


def provider_response_schema():
    schema, _ = response_schema()
    scope = schema['$defs']['ResponseScope']
    scope['properties'].pop('period')
    scope['required'].remove('period')
    schema['$defs'].pop('Period')
    return schema


def _validate(value, rule, schema, depth=0):
    if depth > 32:
        raise ValueError('Invalid response.')
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
        raise ValueError('Invalid response union.')
    kind = rule.get('type')
    valid = {'object':isinstance(value,dict),'array':isinstance(value,list),
             'string':isinstance(value,str),'boolean':type(value) is bool,
             'integer':type(value) is int,'number':type(value) in (int,float) and math.isfinite(value),
             'null':value is None}
    if kind is not None and not valid.get(kind,False):
        raise ValueError('Invalid response type.')
    if 'enum' in rule and value not in rule['enum'] or 'const' in rule and value != rule['const']:
        raise ValueError('Invalid response enum.')
    if kind == 'object':
        if set(rule.get('required',[]))-value.keys():
            raise ValueError('Missing response fields.')
        props = rule.get('properties',{})
        if rule.get('additionalProperties') is False and value.keys()-props.keys():
            raise ValueError('Unexpected response fields.')
        for key,item in value.items():
            if key in props:
                _validate(item,props[key],schema,depth+1)
    if kind == 'array':
        if len(value)<rule.get('minItems',0) or len(value)>rule.get('maxItems',100000):
            raise ValueError('Invalid response array.')
        if rule.get('uniqueItems') is True and len({canonical(item) for item in value}) != len(value):
            raise ValueError('Duplicate response array items.')
        for item in value:
            _validate(item,rule.get('items',{}),schema,depth+1)
    if kind == 'string':
        if len(value)<rule.get('minLength',0) or len(value)>rule.get('maxLength',1048576):
            raise ValueError('Invalid response text.')
        if rule.get('pattern') and re.search(rule['pattern'],value) is None:
            raise ValueError('Invalid response format.')
        if rule.get('format') == 'date':
            from datetime import date
            date.fromisoformat(value)


def validate_response(value, authorized_evidence, *, expected_period=...):
    schema,_ = response_schema()
    _validate(value,schema,schema)
    known = {item['id']:item for item in authorized_evidence}
    returned = {item['id']:item for item in value['evidence']}
    if len(returned) != len(value['evidence']) or returned.keys()-known.keys():
        raise ValueError('Invalid response evidence.')
    for key,item in returned.items():
        if any(item[field] != known[key].get(field) for field in ['kind','source','title']):
            raise ValueError('Invalid response provenance.')
    if value['status'] in ['ok','partial'] and not returned:
        raise ValueError('Missing response evidence.')
    if value['status'] in ['no_data','insufficient_data','unsupported','refused','error'] and (value['metrics'] or value['recommendations']):
        raise ValueError('Invalid non-actionable response.')
    for metric in value['metrics']:
        if set(metric['evidence_ids'])-returned.keys():
            raise ValueError('Invalid metric reference.')
        # Financial numbers must match values in the authorized server record.
        eligible = [known[x] for x in metric['evidence_ids'] if known[x]['kind']=='cost_query']
        if not any({'name':metric['name'],'value':metric['value'],'unit':metric['unit']} in e.get('metrics',[]) for e in eligible):
            raise ValueError('Unverified financial metric.')
    for recommendation in value['recommendations']:
        if set(recommendation['evidence_ids'])-returned.keys():
            raise ValueError('Invalid recommendation reference.')
        if (recommendation['estimated_savings'] is None) != (recommendation['currency'] is None):
            raise ValueError('Invalid savings currency.')
        if recommendation['estimated_savings'] is not None:
            raise ValueError('Savings estimation is outside this chat scope.')
    period = value['scope']['period']
    if expected_period is not ... and period != expected_period:
        raise ValueError('Response period differs from verified context.')
    if period and period['from'] >= period['to']:
        raise ValueError('Invalid period.')
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
        if not isinstance(frozen,list): raise ValueError('Invalid frozen citations.')
        matches = [item for item in frozen if isinstance(item,dict) and item.get('evidence_id') == evidence['id']]
        if len(matches) != 1: raise ValueError('Unresolved corpus citation.')
        citation = SourceCitation.model_validate(matches[0]).model_dump()
        source = known[evidence['id']]
        if (citation['title'] != source['title'].strip() or citation['source'] != source['source'].strip()
                or not isinstance(source.get('content'),str) or citation['excerpt'] != source['content'][:140]):
            raise ValueError('Mismatched corpus citation.')
        selected.append(citation)
    return [item['evidence_id'] for item in selected], selected
