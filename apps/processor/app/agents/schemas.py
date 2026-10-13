from __future__ import annotations

import copy
from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from app.core.chat_segments import bind_segments, quote_choices


ShortText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]
AnswerText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
]
EvidenceId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=256,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$",
    ),
]
DecimalText = Annotated[
    str,
    StringConstraints(pattern=r"^-?(?:0|[1-9]\d*)(?:\.\d{1,12})?$"),
]
NonNegativeDecimalText = Annotated[
    str,
    StringConstraints(pattern=r"^(?:0|[1-9]\d*)(?:\.\d{1,12})?$"),
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ResponseStatus(str, Enum):
    ok = "ok"
    partial = "partial"
    no_data = "no_data"
    insufficient_data = "insufficient_data"
    unsupported = "unsupported"
    refused = "refused"
    error = "error"


class EvidenceKind(str, Enum):
    cost_query = "cost_query"
    corpus = "corpus"
    user_input = "user_input"


class RecommendationCategory(str, Enum):
    tagging = "tagging"
    investigation = "investigation"
    rightsizing = "rightsizing"
    scheduling = "scheduling"
    orphan_cleanup = "orphan_cleanup"
    storage_optimization = "storage_optimization"
    observability_optimization = "observability_optimization"
    rate_optimization = "rate_optimization"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Risk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Period(StrictModel):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")

    @model_validator(mode="after")
    def validate_order(self) -> "Period":
        if self.from_date >= self.to_date:
            raise ValueError("period.from must be before period.to")
        return self


class ResponseScope(StrictModel):
    cloud: Literal["azure"]
    data_environment: Literal["simulated"]
    subscription_ids: list[ShortText] = Field(max_length=20)
    period: Period | None


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
        if fields['kind']=='corpus':
            # Provider-only grounding: force selection of an actual passage,
            # not merely an allowed identifier with a similar document title.
            choice['properties']['support_quote']={'type':'string','minLength':1,'maxLength':2048,
                'enum':quote_choices(source.get('content')),
                'description':'Exact contiguous quotation from this fragment supporting a relevant claim in answer. Do not cite a fragment merely because it is nearby or shares a title.'}
            choice['required'].append('support_quote')
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


def chat_provider_schema(*, financial_metrics_allowed=False, authorized_evidence=None, calculations=None, quantities=None):
    if type(financial_metrics_allowed) is not bool:
        raise ValueError('Invalid financial authority control.')
    schema = FinOpsResponse.model_json_schema()
    scope = schema['$defs']['ResponseScope']
    scope['properties'].pop('period')
    scope['required'].remove('period')
    scope['properties'].pop('subscription_ids')
    scope['required'].remove('subscription_ids')
    schema['$defs'].pop('Period')
    if not financial_metrics_allowed:
        schema['properties']['metrics']['maxItems'] = 0
    # Chat never authorizes estimated savings; mirror the backend firewall.
    for field in ('estimated_savings','currency'):
        schema['$defs']['Recommendation']['properties'][field]={'type':'null'}
    # Select documentary support before drafting prose in constrained decoding.
    schema['properties'] = {'evidence':schema['properties']['evidence'],
        **{key:value for key,value in schema['properties'].items() if key!='evidence'}}
    # Complete branches preserve every base constraint, sharing root definitions.
    branch_base = {key: value for key, value in schema.items() if key != '$defs'}
    actionable = copy.deepcopy(branch_base)
    abstention = copy.deepcopy(branch_base)
    actionable['properties']['status'] = {'type': 'string', 'enum': ['ok', 'partial']}
    actionable['properties']['evidence']['minItems'] = 1
    abstention['properties']['status'] = {'type': 'string', 'enum': [
        status for status in schema['$defs']['ResponseStatus']['enum']
        if status not in ('ok', 'partial')]}
    # A single union avoids intersecting long citation enums with identical
    # copies at root and branch (DeepInfra rejects that redundant grammar).
    schema = {'type':'object', 'anyOf':[actionable, abstention], '$defs':schema['$defs']}
    return bind_segments(_bind_chat_evidence(schema, authorized_evidence), calculations, quantities)


def assemble_chat_response(value, period, subscriptions=None, *, authorized_evidence=None):
    if not isinstance(value, dict) or not isinstance(value.get('scope'), dict):
        raise ValueError('Invalid response scope.')
    if 'period' in value['scope']:
        raise ValueError('Period is server-owned.')
    if 'subscription_ids' in value['scope']:
        raise ValueError('Subscriptions are server-owned.')
    selected = [] if subscriptions is None else subscriptions
    if (not isinstance(selected, list) or len(selected) > 20
            or any(type(item) is not str or not item or len(item) > 256 for item in selected)
            or selected != sorted(set(selected))):
        raise ValueError('Invalid canonical subscriptions.')
    if authorized_evidence is not None:
        known={item['id']:item for item in authorized_evidence}
        if 'evidence' not in value or not isinstance(value['evidence'],list):
            raise ValueError('Invalid evidence collection.')
        evidence=[]
        for item in value['evidence']:
            if not isinstance(item,dict): raise ValueError('Invalid evidence record.')
            item=dict(item)
            if item.get('kind')=='corpus':
                quote=item.pop('support_quote',None)
                source=known.get(item.get('id'),{})
                if (not isinstance(quote,str) or not quote.strip() or len(quote)>2048
                        or quote not in quote_choices(source.get('content',''))):
                    raise ValueError('Citation passage is not grounded.')
            evidence.append(item)
        value={**value,'evidence':evidence}
    assembled = {**value, 'scope': {**value['scope'], 'period': period, 'subscription_ids': selected}}
    return FinOpsResponse.model_validate(assembled).model_dump(mode='json', by_alias=True)


class Evidence(StrictModel):
    id: EvidenceId
    kind: EvidenceKind
    title: ShortText
    source: ShortText


class Metric(StrictModel):
    name: ShortText
    value: DecimalText
    unit: ShortText
    evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=20)


class Recommendation(StrictModel):
    category: RecommendationCategory
    action: ShortText
    rationale: ShortText
    estimated_savings: NonNegativeDecimalText | None
    currency: Annotated[
        str,
        StringConstraints(pattern=r"^[A-Z]{3}$"),
    ] | None
    confidence: Confidence
    risk: Risk
    evidence_ids: list[EvidenceId] = Field(min_length=1, max_length=20)
    requires_human_approval: Literal[True]

    @model_validator(mode="after")
    def validate_savings_currency(self) -> "Recommendation":
        if (self.estimated_savings is None) != (self.currency is None):
            raise ValueError(
                "estimated_savings and currency must either both be set or both be null"
            )
        return self


class FinOpsResponse(StrictModel):
    schema_version: Literal["1.0"]
    status: ResponseStatus
    answer: AnswerText
    scope: ResponseScope
    evidence: list[Evidence] = Field(max_length=20)
    metrics: list[Metric] = Field(max_length=20)
    recommendations: list[Recommendation] = Field(max_length=10)
    assumptions: list[ShortText] = Field(max_length=10)
    limitations: list[ShortText] = Field(max_length=10)
    next_actions: list[ShortText] = Field(max_length=10)

    @model_validator(mode="after")
    def validate_evidence_and_status(self) -> "FinOpsResponse":
        evidence_ids = [item.id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence ids must be unique")

        non_actionable_statuses = {
            ResponseStatus.no_data,
            ResponseStatus.insufficient_data,
            ResponseStatus.unsupported,
            ResponseStatus.refused,
            ResponseStatus.error,
        }
        if self.status in non_actionable_statuses and (
            self.metrics or self.recommendations
        ):
            raise ValueError(
                "non-actionable responses cannot contain metrics or recommendations"
            )

        known_ids = set(evidence_ids)
        referenced_ids = {
            evidence_id
            for metric in self.metrics
            for evidence_id in metric.evidence_ids
        }
        referenced_ids.update(
            evidence_id
            for recommendation in self.recommendations
            for evidence_id in recommendation.evidence_ids
        )
        unknown_ids = sorted(referenced_ids - known_ids)
        if unknown_ids:
            raise ValueError("metrics and recommendations must reference known evidence")

        if self.status in {ResponseStatus.ok, ResponseStatus.partial} and not self.evidence:
            raise ValueError("ok and partial responses require evidence")
        return self


def finops_response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "economicon_finops_response_v1",
            "strict": True,
            "schema": FinOpsResponse.model_json_schema(by_alias=True),
        },
    }
