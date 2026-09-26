from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: NonEmptyText


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
