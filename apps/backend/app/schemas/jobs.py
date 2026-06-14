from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class IngestJobRequest(BaseModel):
    tenant_id: str
    source: str
    text_content: NonEmptyText
    artifact_uri: str | None = None
    metadata: dict = Field(default_factory=dict)


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    queue: str
