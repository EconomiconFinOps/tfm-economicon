import json
import re

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
        or not (
            (isinstance(payload.get("text_content"), str) and payload["text_content"].strip())
            or (isinstance(payload.get("upload_id"), str)
                and re.fullmatch(r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}', payload['upload_id'])
                and 'text_content' not in payload)
        )
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


def _stored_result(result, stored_as_text: bool = True) -> dict:
    """Devuelve el resultado guardado de un trabajo `completed` como objeto, o lo rechaza (RF-054-001).

    Se rechaza con `InvalidJobMessage` y no se relanza el error de decodificacion: el worker
    descarta ese tipo con `nack(requeue=False)`, y un resultado corrupto no se arregla
    reentregando el mismo mensaje (antes un `JSONDecodeError` caia en el camino generico,
    se reencolaba y fallaba igual sin fin).
    Se usa `from None` y nunca se formatea el valor: el resultado guardado puede contener
    datos del tenant y no debe aparecer en el mensaje, la excepcion ni la traza.

    `stored_as_text` lo declara el repositorio y decide como se interpreta un `str`:
    - `True` (SQLite, solo pruebas): el objeto se guarda serializado como texto, asi que un
      `str` se decodifica con `json.loads` y el resultado debe ser un objeto.
    - `False` (JSONB sobre CockroachDB/psycopg): el controlador ya decodifico el valor, asi que
      un `str` es una CADENA JSON y nunca un objeto. Decodificarla otra vez convertiria `{}`,
      `{"ok":1}` o `null` en `dict`/`None` y se aceptaria un resultado que no lo es; por eso se
      rechaza sin mirar su contenido. No basta con rechazar todo `str` siempre: SQLite lo
      necesita decodificar.
    """
    if isinstance(result, str):
        if not stored_as_text:
            raise InvalidJobMessage("Invalid job message.") from None
        try:
            result = json.loads(result)
        except (ValueError, RecursionError):
            # `RecursionError` cubre una anidacion patologica que `json.loads` no acota.
            raise InvalidJobMessage("Invalid job message.") from None
    # La forma se valida sobre CUALQUIER valor y no solo sobre el texto: CockroachDB entrega
    # el JSONB ya decodificado y SQLite entrega `123`/`0` como entero por afinidad de columna.
    # Por eso tampoco se usa `or {}`, que convertiria `[]`, `0`, `False` o `""` en "sin resultado".
    if result is None:
        return {}
    if isinstance(result, dict):
        return result
    raise InvalidJobMessage("Invalid job message.") from None


class IngestTask:
    def __init__(self, repository: JobRepository, pipeline: PipelineRunner, documents=None):
        self.repository = repository
        self.pipeline = pipeline
        self.documents = documents

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
            # El valor por defecto es `True` y no `False`: los dobles y `MagicMock` de otras
            # pruebas no declaran el atributo y siempre se han comportado como texto
            # serializado; un `False` por defecto cambiaria su comportamiento sin motivo.
            # El repositorio real (que si lo declara) es quien fija `False` sobre CockroachDB.
            stored_as_text = getattr(self.repository, "json_stored_as_text", True)
            result = _stored_result(stored.get("result"), stored_as_text)
            if self.documents is not None:
                self.documents.completed(stored, payload)
            return result

        if self.documents is not None:
            self.documents.claim(stored, payload)
        elif 'upload_id' in payload:
            raise InvalidJobMessage('Document processing is not configured.')
        try:
            self.repository.mark_running(job_id, **scope)
        except Exception:
            if self.documents is not None:
                self.documents.release(stored)
            raise
        try:
            document = self.documents.prepare(stored, payload) if self.documents is not None else None
            # Only persisted execution content reaches the graph after authorization.
            pipeline_input = {
                "job_id": job_id,
                "tenant_id": stored["tenant_id"],
                "source": stored["source"],
                "artifact_uri": stored.get("artifact_uri"),
                "text_content": document["text"] if document is not None else payload["text_content"],
                "metadata": payload.get("metadata", {}),
            }
            if document is not None:
                pipeline_input['normalized_document'] = document
            if self.documents is not None:
                self.documents.assert_owned(stored, payload)
            result = self.pipeline.run(pipeline_input)
            # This execution-only input already lives in the extraction checkpoint.
            result = {key:value for key,value in result.items() if key != 'normalized_document'}
            if self.documents is not None:
                self.documents.assert_owned(stored, payload)
            completion_scope = scope
            if self.documents is not None and 'upload_id' in payload:
                # File text/chunks are already durable in checkpoint/pgvector. Do not
                # duplicate an unbounded document in Cockroach's jobs.result message.
                result = {key: value for key, value in result.items() if key not in {'text_content', 'chunks'}}
                result.update(document_id=job_id, document_schema_version=1)
                completion_scope = {**scope, 'document_owner': self.documents.owner}
            self.repository.mark_completed(job_id, result, **completion_scope)
            if self.documents is not None:
                self.documents.completed(stored, payload)
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

        finally:
            if self.documents is not None:
                self.documents.release(stored)
