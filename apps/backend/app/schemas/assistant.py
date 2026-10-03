from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText


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
        if value is not None and not isinstance(value, (str, date)):
            raise ValueError("Expected an ISO date")
        return value

    @model_validator(mode="after")
    def validate_selection(self):
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("Both period dates are required")
        if self.start_date is not None and self.start_date >= self.end_date:
            raise ValueError("start_date must precede end_date")
        return self


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: NonEmptyText
    cost_query: AzureCostSelection | None = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    source: str
    content: str
    distance: float


class MessageRecord(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict
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
