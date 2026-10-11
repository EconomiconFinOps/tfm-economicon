import json

from app.agents.guardrails import AgentInputError
from app.clients.litellm import ProviderError
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository


class InvalidJobMessage(ValueError):
    """A permanent delivery rejection that must not change persisted state."""


class IngestionFailed(RuntimeError):
    """Fallo de ingesta ya registrado como `failed`, con su clasificacion de permanencia.

    Sigue siendo `RuntimeError("ingestion_failed")` para no romper a quien ya lo captura.
    El booleano `permanent` es el unico dato de la causa que viaja al worker: True solo si
    la causa fue un `AgentInputError`; el texto de la causa nunca se conserva.
    """

    def __init__(self, *, permanent: bool):
        super().__init__("ingestion_failed")
        self.permanent = permanent


def _identifier(value) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return not any(
        character.isspace() or ord(character) < 32 or ord(character) == 127 or character == ","
        for character in value
    )


def _payload(job: dict, *, persisted: bool = False) -> dict:
    payload = job.get("payload")
    if persisted and isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (ValueError, TypeError):
            raise InvalidJobMessage("Invalid job message.") from None
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("text_content"), str)
        or not payload["text_content"].strip()
        or not isinstance(payload.get("metadata", {}), dict)
        or not isinstance(job.get("source"), str)
        or not job["source"].strip()
        or (job.get("artifact_uri") is not None and not isinstance(job["artifact_uri"], str))
        or payload.get("tenant_id") != job["tenant_id"]
        or payload.get("source") != job["source"]
        or payload.get("artifact_uri") != job.get("artifact_uri")
    ):
        raise InvalidJobMessage("Invalid job message.")
    return {"artifact_uri": None, "metadata": {}, **payload}


class IngestTask:
    def __init__(self, repository: JobRepository, pipeline: PipelineRunner):
        self.repository = repository
        self.pipeline = pipeline

    def execute(self, job: dict) -> dict:
        if not isinstance(job, dict) or not all(
            _identifier(job.get(key)) for key in ("id", "tenant_id", "created_by")
        ):
            raise InvalidJobMessage("Invalid job message.")
        job_id = job["id"]
        incoming = _payload(job)
        scope = {"tenant_id": job["tenant_id"], "created_by": job["created_by"]}
        stored = self.repository.fetch_authorized_job(job_id, **scope)
        if stored is None:
            raise InvalidJobMessage("Invalid job message.")
        payload = _payload(stored, persisted=True)
        if (
            any(job[key] != stored[key] for key in ("id", "tenant_id", "created_by", "source"))
            or job.get("artifact_uri") != stored.get("artifact_uri")
            or incoming != payload
            or job.get("job_id", job_id) != job_id
        ):
            raise InvalidJobMessage("Invalid job message.")
        if stored["status"] == "completed":
            result = stored.get("result")
            return json.loads(result) if isinstance(result, str) else result or {}

        self.repository.mark_running(job_id, **scope)
        try:
            # Only persisted execution content reaches the graph after authorization.
            pipeline_input = {
                "job_id": job_id,
                "tenant_id": stored["tenant_id"],
                "source": stored["source"],
                "artifact_uri": stored.get("artifact_uri"),
                "text_content": payload["text_content"],
                "metadata": payload.get("metadata", {}),
            }
            result = self.pipeline.run(pipeline_input)
            self.repository.mark_completed(job_id, result, **scope)
            return result
        except ProviderError:
            self.repository.mark_failed(job_id, "ingestion_failed", **scope)
            raise
        except Exception as exc:
            self.repository.mark_failed(job_id, "ingestion_failed", **scope)
            # Si `mark_failed` falla, su excepcion se propaga tal cual (reencolable): no se
            # sabe que quedo escrito y descartar la entrega podria perder el fallo.
            # `permanent` se calcula aqui, donde aun se ve la causa, y no se deja que el
            # worker la lea: la causa se aplana a proposito (`from None`) para no filtrar
            # secretos ni el motivo del guardrail por trazas (JUP-053).
            raise IngestionFailed(permanent=isinstance(exc, AgentInputError)) from None
