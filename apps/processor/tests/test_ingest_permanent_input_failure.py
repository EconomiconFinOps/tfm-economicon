"""JUP-113 (RF-086-004): un fallo PERMANENTE de entrada se registra y se descarta en una entrega.

Hoy un trabajo ya guardado cuyo `source` rechaza el guardrail de entrada (por ejemplo
`Azure Cost Management`, que no cumple `^[a-z0-9][a-z0-9._-]{0,63}$`) falla dentro de
`AgentRuntime.invoke`, `IngestTask` lo convierte en `RuntimeError("ingestion_failed")` y el
worker hace `nack(requeue=True)` y relanza: la entrega vuelve a la cola, falla igual y
retiene la cola para siempre.

Contrato que fijan estas pruebas (lo implementa el coder):
- `AgentInputError` (subclase de `AgentGuardrailError`) la lanzan solo las comprobaciones de
  ENTRADA del guardrail; un fallo de la RESPUESTA del proveedor no es permanente de entrada.
- `IngestionFailed` (subclase de `RuntimeError`, mensaje `ingestion_failed`) lleva el booleano
  `permanent`: True solo si la causa es `AgentInputError`.
- El worker descarta (un `nack(requeue=False)`, sin relanzar) lo permanente y registra un
  evento fijo `job_input_rejected`; lo no permanente conserva `nack(requeue=True)` + relanzar.

Doble de pruebas solo en las fronteras (proveedor LLM y almacen vectorial); `AgentRuntime`,
`PipelineRunner` (LangGraph), `JobRepository` y `ProcessorWorker` son los reales. Los casos
del worker NO importan nombres nuevos para fallar por COMPORTAMIENTO y no por ImportError.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from sqlalchemy import text
import structlog

from app.agents.service import AgentRuntime
from app.clients.rabbitmq_queue import QueueMessage
from app.core.config import Settings
from app.core.logging import configure_logging
from app.core.metrics import ingest_jobs_failed_total
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask
from app.workers.runner import ProcessorWorker
from tenant_isolation_support import cockroach_isolation_database, isolation_database, seed_job, snapshot
from test_azure_cost_cockroach_integration import database_factory
from test_secret_boundaries import restore_logging

# Origen real del defecto: pasa la validacion de forma del processor (no vacio) pero el
# guardrail lo rechaza por contener espacios y mayusculas.
HOSTILE_SOURCE = "Azure Cost Management"
POISON_TAG = 31
VALID_TAG = 32


def _store_source(database, job, source, *, text_content=None):
    """Guarda `source` en la fila y en el payload (y en el dict de la entrega) de forma coherente.

    El processor exige que fila, payload y mensaje coincidan; si no, descarta por
    `InvalidJobMessage` y nunca llegaria al guardrail que queremos ejercitar.
    """
    job["source"] = job["payload"]["source"] = source
    if text_content is not None:
        job["payload"]["text_content"] = text_content
    with database.engine.begin() as connection:
        connection.execute(
            text("UPDATE jobs SET source=:source, payload=:payload WHERE id=:id"),
            {"id": job["id"], "source": source, "payload": json.dumps(job["payload"])},
        )


def _build_stack(database, provider, vector):
    settings = Settings(_env_file=None, llm_provider="mock",
                        litellm_api_key="jup113-synthetic-injected-provider-key")
    runtime = AgentRuntime(settings, provider=provider)
    pipeline = PipelineRunner(runtime, TextChunker(48, 8), MockEmbeddingProvider(8), vector)
    return IngestTask(JobRepository(database), pipeline)


def _vector_double():
    vector = MagicMock(spec_set=["store_document"])
    vector.store_document.side_effect = lambda **payload: {
        "document_id": payload["job_id"], "chunk_count": len(payload["chunks"]),
        "embedding_count": len(payload["embeddings"]), "vector_store": "test-double",
        "provider": payload["provider_name"],
    }
    return vector


@pytest.fixture
def poisoned(isolation_database):
    """Trabajo guardado con origen no admitido + worker con pipeline real."""
    database = isolation_database
    job = seed_job(database, identifier="jup113-poison")
    secret_content = "CONTENIDO-SENSIBLE-JUP113 informe de costes del trimestre"
    _store_source(database, job, HOSTILE_SOURCE, text_content=secret_content)
    provider = MagicMock(spec_set=["invoke"])
    vector = _vector_double()
    task = _build_stack(database, provider, vector)
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = task
    yield SimpleNamespace(
        database=database, job=job, provider=provider, vector=vector, task=task,
        worker=worker, content=secret_content,
        row=lambda identifier="jup113-poison": next(
            r for r in snapshot(database, "jobs")[0] if r["id"] == identifier),
    )
    structlog.contextvars.clear_contextvars()


def _deliver(worker, job, tag):
    worker._process_message(QueueMessage(job, delivery_tag=tag))


# ----------------------------------------------------------------- worker (sin nombres nuevos)

@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_worker_discards_stored_job_with_unsupported_source_in_one_delivery(poisoned):
    # Caso central RF-086-004: la entrega se descarta UNA vez (nack sin requeue), no se
    # relanza (la llamada devuelve normalmente) y el trabajo queda fallido y contado una vez.
    before = ingest_jobs_failed_total._value.get()

    _deliver(poisoned.worker, poisoned.job, POISON_TAG)  # sin pytest.raises: no debe lanzar

    queue = poisoned.worker.queue
    queue.nack.assert_called_once_with(POISON_TAG, requeue=False)
    queue.ack.assert_not_called()
    row = poisoned.row()
    assert row["status"] == "failed"
    assert json.loads(row["result"]) == {"error": "ingestion_failed"}
    # El rechazo ocurre en el guardrail, antes de cualquier efecto externo.
    poisoned.provider.invoke.assert_not_called()
    poisoned.vector.store_document.assert_not_called()
    assert ingest_jobs_failed_total._value.get() == before + 1


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_rejection_diagnostic_carries_request_id_and_no_job_data(poisoned, capsys, caplog):
    # El unico diagnostico es el evento fijo `job_input_rejected` con el request_id del
    # contexto; ni el origen, ni el contenido del documento, ni el texto de la excepcion
    # original (que el guardrail redacta con el motivo del rechazo) pueden aparecer.
    configure_logging()

    _deliver(poisoned.worker, poisoned.job, POISON_TAG)

    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert "job_input_rejected" in rendered
    assert poisoned.job["request_id"] in rendered
    lowered = rendered.lower()
    assert HOSTILE_SOURCE.lower() not in lowered
    assert "azure cost" not in lowered
    assert poisoned.content not in rendered
    assert "CONTENIDO-SENSIBLE-JUP113" not in rendered
    assert "source must be a safe provider identifier" not in lowered
    # Ningun dato mas que los campos fijos del log: el evento no arrastra el trabajo.
    [event] = [json.loads(line) for line in rendered.splitlines()
               if line.startswith("{") and "job_input_rejected" in line]
    assert event["level"] == "warning"
    assert set(event) <= {"event", "level", "logger", "request_id", "timestamp", "service"}
    assert event["request_id"] == poisoned.job["request_id"]


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_poison_message_does_not_hold_back_next_valid_delivery(poisoned, capsys, caplog):
    # Con el bucle real del worker: el envenenado se descarta sin que el bucle registre
    # `worker_loop_failed` (no escapa excepcion) y el mensaje siguiente, de OTRO tenant y
    # con origen valido, se procesa y se confirma en la misma ejecucion.
    configure_logging()
    database = poisoned.database
    valid = seed_job(database, identifier="jup113-valid", tenant="tenant-b", creator="bob")
    valid_vector = poisoned.vector
    worker = poisoned.worker
    worker.settings = SimpleNamespace(processor_queue_name="jup113-test")
    worker._stopping = MagicMock()
    worker._stopping.is_set.side_effect = [False, False, True]  # dos vueltas del bucle
    worker.queue.blocking_pop.side_effect = [
        QueueMessage(poisoned.job, POISON_TAG),
        QueueMessage(valid, VALID_TAG),
        None,
    ]

    worker.run_forever()

    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert "worker_loop_failed" not in rendered
    assert worker.queue.nack.call_args_list == [call(POISON_TAG, requeue=False)]
    assert worker.queue.ack.call_args_list == [call(VALID_TAG)]
    assert poisoned.row()["status"] == "failed"
    assert poisoned.row("jup113-valid")["status"] == "completed"
    # Solo el documento valido llega al almacen vectorial.
    valid_vector.store_document.assert_called_once()
    assert valid_vector.store_document.call_args.kwargs["tenant_id"] == "tenant-b"


# ----------------------------------------------------------------- IngestTask (nombres nuevos)

@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_ingest_task_marks_unsupported_source_as_permanent_ingestion_failed(poisoned):
    from app.tasks.ingest import IngestionFailed

    # Tras `mark_failed`, el fallo se publica como IngestionFailed permanente y mantiene
    # el mensaje sanitizado "ingestion_failed" sin encadenar la causa (`from None`), para que
    # ninguna traza arrastre el origen ni el motivo del guardrail.
    with pytest.raises(IngestionFailed) as caught:
        poisoned.task.execute(poisoned.job)

    assert caught.value.permanent is True
    assert str(caught.value) == "ingestion_failed"
    assert isinstance(caught.value, RuntimeError)
    assert caught.value.__cause__ is None
    assert poisoned.row()["status"] == "failed"
    assert json.loads(poisoned.row()["result"]) == {"error": "ingestion_failed"}


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("error_name", ["AgentInputError", "RuntimeError", "ValueError", "AgentGuardrailError"])
def test_ingest_task_permanent_only_when_cause_is_agent_input_error(poisoned, error_name):
    from app.agents import guardrails
    from app.tasks.ingest import IngestionFailed

    # Origen valido y pipeline doble que lanza cada causa: solo AgentInputError es
    # permanente. El guardrail base (AgentGuardrailError) y errores genericos no lo son,
    # asi un fallo transitorio del pipeline nunca se descarta por error.
    _store_source(poisoned.database, poisoned.job, "report")
    errors = {
        "AgentInputError": guardrails.AgentInputError("detalle-interno"),
        "RuntimeError": RuntimeError("detalle-interno"),
        "ValueError": ValueError("detalle-interno"),
        "AgentGuardrailError": guardrails.AgentGuardrailError("detalle-interno"),
    }
    pipeline = MagicMock()
    pipeline.run.side_effect = errors[error_name]
    task = IngestTask(JobRepository(poisoned.database), pipeline)

    with pytest.raises(IngestionFailed) as caught:
        task.execute(poisoned.job)

    assert caught.value.permanent is (error_name == "AgentInputError")
    assert str(caught.value) == "ingestion_failed"
    assert caught.value.__cause__ is None
    assert poisoned.row()["status"] == "failed"


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_provider_response_failure_is_not_permanent_input_failure(poisoned):
    from app.tasks.ingest import IngestionFailed

    # Ruta `mock`: el proveedor devuelve texto que no es JSON, `AgentResponseError`. Es un
    # fallo de la RESPUESTA (el proveedor puede acertar en un reintento), no de la entrada.
    _store_source(poisoned.database, poisoned.job, "azure-cost")
    poisoned.provider.invoke.return_value = "esto no es JSON"

    with pytest.raises(IngestionFailed) as caught:
        poisoned.task.execute(poisoned.job)

    assert caught.value.permanent is False
    assert str(caught.value) == "ingestion_failed"
    poisoned.provider.invoke.assert_called_once()
    poisoned.vector.store_document.assert_not_called()
    assert poisoned.row()["status"] == "failed"


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_worker_keeps_requeue_and_reraise_for_non_permanent_failure(poisoned):
    # Sin cambios en este grupo: un fallo no permanente se devuelve a la cola y se relanza.
    _store_source(poisoned.database, poisoned.job, "report")
    pipeline = MagicMock()
    pipeline.run.side_effect = RuntimeError("fallo-transitorio")
    poisoned.worker.task = IngestTask(JobRepository(poisoned.database), pipeline)

    with pytest.raises(RuntimeError) as caught:
        _deliver(poisoned.worker, poisoned.job, POISON_TAG)

    queue = poisoned.worker.queue
    queue.nack.assert_called_once_with(POISON_TAG, requeue=True)
    queue.ack.assert_not_called()
    assert str(caught.value) == "ingestion_failed"
    from app.tasks.ingest import IngestionFailed
    assert isinstance(caught.value, IngestionFailed)
    assert caught.value.permanent is False


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("failing", ["mark_failed", "mark_running"])
def test_persistence_failures_propagate_unchanged_and_are_not_ingestion_failed(poisoned, failing):
    # Si la propia persistencia del estado falla no se sabe que quedo escrito: se propaga
    # la excepcion ORIGINAL (reintentable) y nunca se disfraza de IngestionFailed, que
    # podria descartar la entrega sin haber registrado el fallo.
    original = RuntimeError("base-de-datos-no-disponible")
    repository = JobRepository(poisoned.database)
    setattr(repository, failing, MagicMock(side_effect=original))
    task = IngestTask(repository, poisoned.task.pipeline)

    with pytest.raises(RuntimeError) as caught:
        task.execute(poisoned.job)

    assert caught.value is original
    from app.tasks.ingest import IngestionFailed
    assert not isinstance(caught.value, IngestionFailed)


# ----------------------------------------------------------------- guardrails (nombres nuevos)

@pytest.mark.parametrize("value", ["Azure Cost Management", "", "   ", None, 42, "a" * 65, "-azure"])
def test_normalize_source_rejection_is_permanent_input_error(value):
    from app.agents.guardrails import AgentGuardrailError, AgentInputError, normalize_source

    # Cualquier origen no admisible es un fallo de entrada; al ser subclase tambien sigue
    # siendo AgentGuardrailError para no romper a quien ya captura la base.
    with pytest.raises(AgentInputError) as caught:
        normalize_source(value)
    assert isinstance(caught.value, AgentGuardrailError)


@pytest.mark.parametrize("payload,status", [
    ([], "running"),                                                  # payload no objeto
    ("texto", "running"),
    ({"source": "azure", "metadata": {}}, "running"),                 # tenant ausente
    ({"tenant_id": "  ", "source": "azure"}, "running"),              # tenant en blanco
    ({"tenant_id": "t", "source": "azure"}, "estado invalido"),       # estado con caracteres no admitidos
    ({"tenant_id": "t", "source": "azure"}, None),                    # estado no string
    ({"tenant_id": "t", "source": "azure", "metadata": []}, "running"),  # metadatos no objeto
    ({"tenant_id": "t", "source": "Azure Cost Management"}, "running"),  # origen invalido
])
def test_prepare_agent_input_rejections_are_permanent_input_errors(payload, status):
    from app.agents.guardrails import AgentGuardrailError, AgentInputError, prepare_agent_input

    with pytest.raises(AgentInputError) as caught:
        prepare_agent_input(payload, status)
    assert isinstance(caught.value, AgentGuardrailError)


@pytest.mark.parametrize("raw", ["", "   ", "no es json", "{}", None])
def test_provider_response_failures_are_not_input_errors(raw):
    from app.agents.guardrails import AgentGuardrailError, AgentInputError, AgentResponseError
    from app.agents.guardrails import parse_and_validate_response

    # La respuesta del proveedor sigue siendo AgentResponseError y NO AgentInputError:
    # si lo fuera, un fallo del proveedor se descartaria como permanente de entrada.
    with pytest.raises(AgentResponseError) as caught:
        parse_and_validate_response(raw)
    assert isinstance(caught.value, AgentGuardrailError)
    assert not isinstance(caught.value, AgentInputError)
    assert not issubclass(AgentResponseError, AgentInputError)
