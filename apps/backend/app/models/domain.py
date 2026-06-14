from dataclasses import dataclass


@dataclass(slots=True)
class Tenant:
    id: str
    name: str
    slug: str
    plan: str

