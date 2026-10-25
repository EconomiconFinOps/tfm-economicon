import re
from datetime import date, datetime
from typing import Annotated, Literal, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from pydantic import model_validator, model_serializer

from app.schemas.anomaly_explanations import AnomalySelection
from app.schemas.ownership import OwnershipSelection


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText


class ConversationRenameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = " ".join(value.split())
        if not 1 <= len(value) <= 60:
            raise ValueError("Title must contain between 1 and 60 characters.")
        return value


SelectionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]


class AzureCostSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_by: Literal["subscription", "account", "service"]
    value: SelectionText | None = None
    subscription_id: SelectionText | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("value", "subscription_id", mode="before")
    @classmethod
    def validate_control_characters(cls, value):
        if isinstance(value, str) and any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("Control characters are unsupported")
        return value

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_type(cls, value):
        if value is not None and not (
            type(value) is date or
            isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
        ):
            raise ValueError("Expected an ISO date")
        return value

    @model_validator(mode="after")
    def validate_selection(self):
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("Both period dates are required")
        if self.start_date is not None and self.start_date >= self.end_date:
            raise ValueError("start_date must precede end_date")
        if self.subscription_id is not None:
            self.subscription_id = self.subscription_id.casefold()
        if self.group_by == "subscription" and self.value is not None:
            self.value = self.value.casefold()
        return self


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: NonEmptyText
    ownership_query: OwnershipSelection | None = None
    cost_query: AzureCostSelection | None = None
    # JUP-038: la explicación de anomalías se pide con una selección explícita, nunca interpretando el
    # texto libre. Es excluyente con `ownership_query`: cada petición dispara una sola ruta y así nunca
    # hay que decidir cuál gana ni se mezclan dos evidencias en un mismo mensaje.
    anomaly_query: AnomalySelection | None = None

    @model_validator(mode="after")
    def reject_two_structured_queries(self):
        if sum(query is not None for query in (self.anomaly_query, self.ownership_query, self.cost_query)) > 1:
            raise ValueError("anomaly_query, ownership_query and cost_query are mutually exclusive")
        return self


class RetrievedChunk(BaseModel):
    chunk_id: str
    source: str
    content: str
    distance: float


class SourceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: NonEmptyText
    kind: Literal["corpus"]
    document_id: NonEmptyText
    title: NonEmptyText
    source: NonEmptyText
    reference: NonEmptyText
    section: NonEmptyText | None = None
    page: int | None = Field(default=None, ge=1)
    excerpt: str
    content: str | None = None
    source_spans: list[dict] | None = None
    position_contract: dict | None = None

    @model_serializer(mode='wrap')
    def serialize_provenance(self, handler):
        # Revalidating an older citation must not append new null fields to its
        # persisted metadata or change the conversation's evidence snapshot.
        value = handler(self)
        for name in ('source_spans', 'position_contract', 'content'):
            if value.get(name) is None:
                value.pop(name, None)
        return value


class MessageRecord(BaseModel):
    id: str
    role: str
    content: str
    metadata: Any
    created_at: datetime


class ConversationRecord(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationCollection(BaseModel):
    items: list[ConversationRecord]


class ConversationDetail(BaseModel):
    conversation: ConversationRecord
    messages: list[MessageRecord]


class AssistantReply(BaseModel):
    conversation: ConversationRecord
    user_message: MessageRecord
    assistant_message: MessageRecord
    retrieved_context: list[RetrievedChunk]
