"""Closed functional captures. Validation never normalizes the stored snapshot."""
import json
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Text = Annotated[str, Field(strict=True, min_length=1, max_length=256)]
Currency = Annotated[str, Field(strict=True, pattern=r'^[A-Z]{3}$')]
Amount = Annotated[str, Field(strict=True, max_length=128, pattern=r'^-?(0|[1-9][0-9]*)(\.[0-9]+)?$')]
Count = Annotated[int, Field(strict=True, ge=0)]


class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Period(Closed):
    start_date: date
    end_date: date
    timezone: Literal['UTC'] = 'UTC'

    @model_validator(mode='after')
    def ordered(self):
        if self.start_date >= self.end_date:
            raise ValueError('Invalid period.')
        return self


class Tag(Closed):
    key: Text
    value: Text


class Filters(Closed):
    tags: list[Tag] = Field(default_factory=list, max_length=128)
    subscriptions: list[Text] = Field(default_factory=list, max_length=128)
    resource_groups: list[Text] = Field(default_factory=list, max_length=128)
    services: list[Text] = Field(default_factory=list, max_length=128)
    projects: list[Text] = Field(default_factory=list, max_length=128)


class Selection(Closed):
    period: Period | None = None
    start_date: date | None = None
    end_date: date | None = None
    group_by: Literal['subscription','resource_group','service','project','tag'] | None = None
    tag_key: Text | None = None
    selected_currency: Currency | None = None
    currency: Currency | None = None
    filters: Filters | None = None

    @model_validator(mode='after')
    def ordered(self):
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError('Incomplete period.')
        if self.start_date is not None and self.start_date >= self.end_date:
            raise ValueError('Invalid period.')
        return self


class Identity(Closed):
    tenant_id: Text
    user_id: Text


class Total(Closed):
    currency: Currency
    amount: Amount
    record_count: Count | None = None


class Group(Total):
    label: Annotated[str, Field(strict=True, max_length=256)]
    subscription_id: Text | None = None


class Series(Total):
    period: Period
    label: Annotated[str, Field(strict=True, max_length=256)] | None = None
    load_state: Literal['loaded','loading','error','empty','partial','refresh_pending'] = 'loaded'


class Completeness(Closed):
    status: Literal['complete','partial','empty','unknown','unavailable']
    missing_dimensions: list[Text] = Field(max_length=128)
    excluded_undated_count: Count | None = None


class Counts(Closed):
    records: Count
    groups: Count
    series: Count | None = None


class Dataset(Closed):
    source: Text
    load_state: Literal['loaded','loading','error','empty','partial','refresh_pending','unavailable']
    loaded_at: datetime | None
    selection: Selection
    data_environment: Literal['demo','simulated','unknown','unavailable']
    completeness: Completeness
    totals: list[Total]
    groups: list[Group]
    series: list[Series]
    counts: Counts
    missing_dimensions: list[Text] | None = None

    @field_validator('loaded_at')
    @classmethod
    def timestamp(cls, value):
        if value is not None and value.utcoffset() is None:
            raise ValueError('Timestamp requires timezone.')
        return value


class ScreenCapture(Closed):
    schema_version: Literal['2']
    screen_version: Text
    route: Literal['/','/overview-legacy','/operational','/cuts','/anomalies','/recommendations','/ingest','/assistant','/system-health']
    tab_id: Text
    source: Literal['loaded-screen','loading','error','no-adapter','refresh_pending']
    identity: Identity
    captured_at: datetime
    selection: Selection
    datasets: list[Dataset] = Field(max_length=128)

    @field_validator('captured_at')
    @classmethod
    def timestamp(cls, value):
        if value.utcoffset() is None:
            raise ValueError('Timestamp requires timezone.')
        return value


def depth_exceeds(raw, limit=32):
    """Bound nesting lexically before JSON creates nested Python objects."""
    depth = 0
    quoted = False
    escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (123, 91):
            depth += 1
            if depth > limit:
                return True
        elif byte in (125, 93):
            depth -= 1
    return False


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate input field.')
        result[key] = value
    return result


async def read_generation(request, model):
    from fastapi import HTTPException
    from pydantic import ValidationError
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 2097152:
            raise HTTPException(413, 'input_limit')
        chunks.append(chunk)
    raw = b''.join(chunks)
    if depth_exceeds(raw):
        raise HTTPException(413, 'input_limit')
    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if isinstance(value, dict):
            content = value.get('content')
            if isinstance(content, str) and len(content.encode('utf-8')) > 16384:
                raise HTTPException(413, 'question_limit')
            screen = value.get('screen_context')
            if len(json.dumps(screen, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':'), allow_nan=False).encode('utf-8')) > 1048576:
                raise HTTPException(413, 'screen_limit')
        return model.model_validate(value)
    except (ValueError, TypeError, UnicodeError, RecursionError, ValidationError):
        raise HTTPException(422, 'invalid_generation') from None
