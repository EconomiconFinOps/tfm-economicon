import pytest
from pydantic import ValidationError

from app.schemas.jobs import IngestJobRequest


def test_ingest_job_request_accepts_text_content():
    payload = IngestJobRequest(
        tenant_id="tenant-core",
        source="aws-cur",
        text_content="Monthly cost report for tenant core.",
        metadata={"region": "eu-west-1"},
    )

    assert payload.text_content == "Monthly cost report for tenant core."


def test_ingest_job_request_rejects_blank_text_content():
    with pytest.raises(ValidationError):
        IngestJobRequest(
            tenant_id="tenant-core",
            source="aws-cur",
            text_content="   ",
        )
