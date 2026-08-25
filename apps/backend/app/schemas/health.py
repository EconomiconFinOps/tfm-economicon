from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]
    checked_at: datetime
