from pydantic import BaseModel, Field


class IngestJobRequest(BaseModel):
    tenant_id: str
    source: str
    artifact_uri: str | None = None
    metadata: dict = Field(default_factory=dict)


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    queue: str

