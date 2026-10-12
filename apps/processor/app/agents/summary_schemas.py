"""Authoritative, strictly typed QA-memory output; distinct from FinOpsResponse."""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

QuestionRef = Annotated[
    str, Field(min_length=66, max_length=66, pattern=r"^q-[0-9a-f]{64}$")
]
AnswerRef = Annotated[
    str, Field(min_length=66, max_length=66, pattern=r"^a-[0-9a-f]{64}$")
]
SourceRef = Annotated[
    str, Field(min_length=66, max_length=66, pattern=r"^[qa]-[0-9a-f]{64}$")
]
Text = Annotated[str, Field(min_length=1, max_length=512)]


class SummaryTopic(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    text: Text
    question_refs: list[QuestionRef] = Field(
        max_length=8, json_schema_extra={"uniqueItems": True}
    )
    answer_refs: list[AnswerRef] = Field(
        max_length=8, json_schema_extra={"uniqueItems": True}
    )

    @field_validator("question_refs", "answer_refs")
    @classmethod
    def unique_refs(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Duplicate source references.")
        return value


class SummaryFact(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    quote: Text
    source_ref: SourceRef


class SummaryResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    v: Literal[2]
    topics: list[SummaryTopic] = Field(max_length=8)
    facts: list[SummaryFact] = Field(max_length=8)
    limitations: list[Annotated[str, Field(min_length=1, max_length=256)]] = Field(
        max_length=4
    )

    @field_validator("v", mode="before")
    @classmethod
    def exact_version(cls, value):
        if type(value) is not int or value != 2:
            raise ValueError("Invalid summary version.")
        return value
