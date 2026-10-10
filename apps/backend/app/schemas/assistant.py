from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.ownership import OwnershipSelection


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText = Field(max_length=200)


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: NonEmptyText = Field(max_length=4000)
    ownership_query: OwnershipSelection | None = None


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
