"""Bounded, explicit ownership selection; labels never confer authorization."""
import re
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

from app.schemas.billing import canonical_tag_key


SelectionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]


class OwnershipSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_by: Literal["project", "application", "owner", "cost_center", "tag"]
    tag_key: SelectionText | None = None
    value: SelectionText | None = None
    currency: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("tag_key", "value", "currency", mode="before")
    @classmethod
    def reject_controls(cls, value):
        if isinstance(value, str) and any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("Control characters are unsupported")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value):
        if value is not None:
            if re.fullmatch(r"[A-Za-z]{3}", value) is None:
                raise ValueError("Expected a three-letter currency")
            return value.upper()
        return value

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def require_iso_date(cls, value):
        if value is not None and not (
            type(value) is date or
            isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
        ):
            raise ValueError("Expected an ISO date")
        return value

    @model_validator(mode="after")
    def validate_selection(self):
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("Both period dates are required")
        if self.start_date is not None and self.start_date >= self.end_date:
            raise ValueError("start_date must precede end_date")
        if self.group_by == "tag":
            if self.tag_key is None or not canonical_tag_key(self.tag_key):
                raise ValueError("A usable tag key is required")
            self.tag_key = canonical_tag_key(self.tag_key)
        elif self.tag_key is not None:
            raise ValueError("tag_key is only allowed for tag grouping")
        return self
