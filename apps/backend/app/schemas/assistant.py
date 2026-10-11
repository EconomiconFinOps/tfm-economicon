from datetime import datetime
from typing import Annotated, Literal, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


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


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: NonEmptyText


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
