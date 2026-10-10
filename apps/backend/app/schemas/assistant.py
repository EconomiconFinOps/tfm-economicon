from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.schemas.savings import SavingsSelection


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText


class MessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: NonEmptyText
    savings_query: SavingsSelection | None = None

    @model_validator(mode="after")
    def explicit_savings_command(self):
        # Usable from the existing chat without interpreting free text as filters.
        parts = self.content.split()
        if not parts:
            raise ValueError("content must contain non-whitespace text")
        if parts[0].lower() == "/ahorro":
            if len(parts) != 3 or self.savings_query is not None:
                raise ValueError("Use /ahorro YYYY-MM-DD YYYY-MM-DD or savings_query, not both")
            self.savings_query = SavingsSelection(start_date=parts[1], end_date=parts[2])
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
