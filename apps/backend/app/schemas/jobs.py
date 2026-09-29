from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class IngestJobRequest(BaseModel):
    tenant_id: str
    source: str
    text_content: NonEmptyText
    artifact_uri: str | None = None
    metadata: dict = Field(default_factory=dict)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Invalid request value")
        return value


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    queue: str
