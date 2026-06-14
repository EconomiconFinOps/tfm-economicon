from pydantic import BaseModel


class TenantRecord(BaseModel):
    id: str
    name: str
    slug: str
    plan: str


class TenantCollection(BaseModel):
    items: list[TenantRecord]

