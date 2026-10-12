import re
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# Regla de admision del `source` (JUP-113, RF-086-004). Es una COPIA deliberada
# de `SAFE_SOURCE` en apps/processor/app/agents/guardrails.py: backend y
# processor son servicios independientes que no comparten codigo, e importar
# el del otro acoplaria sus despliegues. Lo que impide que diverjan es la tabla
# docs/api/ingest-source-contract-cases.json, que prueban ambos servicios.
# Rechazar aqui (422) evita aceptar un job que el processor rechazaria siempre en
# su guardrail de entrada, y que el cliente no se entere hasta que falle en cola.
# Se usa `fullmatch` y no `$`: `$` aceptaria un salto de linea final. Sin
# re.ASCII ni re.IGNORECASE a proposito: la normalizacion Unicode de
# `strip()`/`lower()` debe coincidir exactamente con la del processor.
SAFE_SOURCE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")


class IngestJobRequest(BaseModel):
    tenant_id: str
    source: str
    text_content: NonEmptyText
    artifact_uri: str | None = None
    metadata: dict = Field(default_factory=dict)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        # Un unico camino: vacio o solo espacios tampoco cumplen el patron.
        # Se valida la forma normalizada pero se devuelve el valor ORIGINAL,
        # porque se guarda y publica literal (JUP-086). El mensaje no incluye
        # el valor para no filtrarlo en la respuesta de validacion.
        if not SAFE_SOURCE.fullmatch(value.strip().lower()):
            raise ValueError("Invalid request value")
        return value


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    queue: str
