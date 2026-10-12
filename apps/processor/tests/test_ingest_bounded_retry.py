"""JUP-113 (tareas 4.2 y 4.3): un fallo no clasificado se reintenta como maximo UNA vez.

Hoy el worker reencola SIN LIMITE (`nack(requeue=True)` y relanza) todo `IngestionFailed`
con `permanent=False` y cualquier otra excepcion, de modo que un fallo persistente del
pipeline retiene la cola para siempre. Este grupo acota el reintento con la marca
`redelivered` de RabbitMQ (`QueueMessage.redelivered`).

Contrato que fijan estas pruebas (lo implementa el coder):
- Solo para `IngestionFailed(permanent=False)` (el fallo YA quedo registrado como `failed`):
    * `redelivered` falso -> `nack(tag, requeue=True)` y relanza (como hoy);
    * `redelivered` verdadero -> UN `nack(tag, requeue=False)`, NO relanza (la llamada
      devuelve normalmente) y evento `warning` fijo `job_retry_exhausted`, sin otros campos
      (el `request_id` lo aporta el contexto de structlog).
- El permanente de entrada se descarta igual con ambos valores (`job_input_rejected`).
- `InvalidJobMessage` y `ProviderError` no cambian con ninguno de los dos valores
  (`nack(requeue=False)`, sin `job_retry_exhausted`).
- Cualquier OTRA excepcion (leer el trabajo, `mark_running` o `mark_failed` fallan: el estado
  no se pudo leer o registrar) -> `nack(requeue=True)` y relanza AUNQUE `redelivered` sea
  verdadero. Sin tope a proposito: descartar dejaria el trabajo en `queued`/`running` sin
  mensaje que lo recupere.

Doble de pruebas solo en las fronteras (pipeline, canal de la cola); `ProcessorWorker`,
`IngestTask` y `JobRepository` (sobre SQLite) son los reales. El mensaje se construye con la
firma actual y la reentrega se marca asignando `message.redelivered = True`, de modo que los
casos fallan por comportamiento y no por un `TypeError` del constructor.
"""
import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import structlog

from app.agents.service import AgentRuntime
from app.clients.litellm import ProviderError
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

TAG = 61
RETRY_TAG = 62
OTHER_TAG = 63
SECRET_ERROR = "marcador-secreto-xyz detalle interno que nunca debe salir en logs"
SECRET_SOURCE = "origen-marcador-jup113"
SECRET_CONTENT = "CONTENIDO-SENSIBLE-JUP113-REINTENTO informe del trimestre"
FIXED_FIELDS = {"event", "level", "logger", "request_id", "timestamp", "service"}


def _message(job, tag, redelivered):
    # Se construye SIEMPRE con la firma actual (job, tag) y la reentrega se marca asignando
    # el atributo (el dataclass no es inmutable). Asi estos casos de worker fallan HOY por
    # COMPORTAMIENTO (el worker ignora la marca) y no por un TypeError al construir; la
    # construccion por palabra clave se fija aparte en test_queue_message_redelivered.py.
    message = QueueMessage(job, tag)
    if redelivered:
        message.redelivered = True
    return message


def _deliver(worker, job, tag=TAG, redelivered=False):
    worker._process_message(_message(job, tag, redelivered))


def _store_marked_job(database, job):
    """Guarda un origen y un contenido distintivos en la fila, el payload y el dict de la entrega.

    El processor exige que fila, payload y mensaje coincidan; si no, el trabajo se descarta
    como `InvalidJobMessage`. Con marcadores unicos se puede afirmar que no se filtran a logs.
    """
    job["source"] = job["payload"]["source"] = SECRET_SOURCE
    job["payload"]["text_content"] = SECRET_CONTENT
    with database.engine.begin() as connection:
        connection.execute(
            text("UPDATE jobs SET source=:source, payload=:payload WHERE id=:id"),
            {"id": job["id"], "source": SECRET_SOURCE, "payload": json.dumps(job["payload"])},
        )


def _events(rendered, name):
    """Eventos JSON de log con ese nombre dentro del texto capturado."""
    events = []
    for line in rendered.splitlines():
        if line.startswith("{") and name in line:
            event = json.loads(line)
            if event.get("event") == name:
                events.append(event)
    return events


@pytest.fixture
def stack(isolation_database):
    """Trabajo guardado + worker real con pipeline doblado (se configura en cada test)."""
    database = isolation_database
    job = seed_job(database, identifier="jup113-retry")
    _store_marked_job(database, job)
    pipeline = MagicMock()
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = IngestTask(JobRepository(database), pipeline)
    yield SimpleNamespace(
        database=database, job=job, pipeline=pipeline, worker=worker, queue=worker.queue,
        row=lambda identifier="jup113-retry": next(
            r for r in snapshot(database, "jobs")[0] if r["id"] == identifier),
    )
    structlog.contextvars.clear_contextvars()


def _capture(capsys, caplog):
    captured = capsys.readouterr()
    return captured.out + captured.err + caplog.text


# ----------------------------------------------------------------- 1. primera entrega

@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("error", [RuntimeError, ValueError, KeyError])
def test_first_delivery_unclassified_failure_is_requeued_and_reraised(stack, capsys, caplog, error):
    # Primera entrega (sin marca): el fallo se registra como `failed` y se devuelve a la
    # cola UNA vez (`requeue=True`) relanzando `ingestion_failed`. Es el reintento que el
    # tope SI permite; el tipo concreto de la excepcion original no cambia la clasificacion.
    configure_logging()
    stack.pipeline.run.side_effect = error(SECRET_ERROR)
    before = ingest_jobs_failed_total._value.get()

    with pytest.raises(RuntimeError) as caught:
        _deliver(stack.worker, stack.job)

    stack.queue.nack.assert_called_once_with(TAG, requeue=True)
    stack.queue.ack.assert_not_called()
    assert str(caught.value) == "ingestion_failed"
    row = stack.row()
    assert row["status"] == "failed"
    assert json.loads(row["result"]) == {"error": "ingestion_failed"}
    assert ingest_jobs_failed_total._value.get() == before + 1
    # Aun queda el reintento: no se anuncia el agotamiento.
    assert _events(_capture(capsys, caplog), "job_retry_exhausted") == []


# ----------------------------------------------------------------- 2. reentrega agotada

@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("error", [RuntimeError, ValueError, KeyError])
def test_redelivered_unclassified_failure_is_discarded_without_reraising(stack, error):
    # Caso central RF-086: en la reentrega el mismo fallo agota el tope. Se descarta con UN
    # `nack(requeue=False)` y la llamada devuelve normalmente (si relanzase, el bucle
    # registraria `worker_loop_failed` y esperaria 2 s por un mensaje ya resuelto). El
    # trabajo queda `failed` y el contador sube una sola vez.
    stack.pipeline.run.side_effect = error(SECRET_ERROR)
    before = ingest_jobs_failed_total._value.get()

    _deliver(stack.worker, stack.job, redelivered=True)  # sin pytest.raises: no debe lanzar

    stack.queue.nack.assert_called_once_with(TAG, requeue=False)
    stack.queue.ack.assert_not_called()
    row = stack.row()
    assert row["status"] == "failed"
    assert json.loads(row["result"]) == {"error": "ingestion_failed"}
    assert ingest_jobs_failed_total._value.get() == before + 1
    stack.pipeline.run.assert_called_once()


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_retry_exhausted_event_is_fixed_and_leaks_no_job_data(stack, capsys, caplog):
    # El unico diagnostico es el evento fijo `job_retry_exhausted` (warning) con el
    # request_id del contexto. Ni el origen, ni el contenido del documento, ni el texto de
    # la excepcion original pueden aparecer en la salida: nada del trabajo viaja al log.
    configure_logging()
    stack.pipeline.run.side_effect = RuntimeError(SECRET_ERROR)

    _deliver(stack.worker, stack.job, redelivered=True)

    rendered = _capture(capsys, caplog)
    [event] = _events(rendered, "job_retry_exhausted")
    assert event["level"] == "warning"
    assert set(event) <= FIXED_FIELDS
    assert event["request_id"] == stack.job["request_id"]
    lowered = rendered.lower()
    assert "marcador-secreto-xyz" not in lowered
    assert SECRET_ERROR not in rendered
    assert SECRET_SOURCE.lower() not in lowered
    assert SECRET_CONTENT not in rendered
    assert "contenido-sensible-jup113" not in lowered
    # No es un rechazo de entrada ni un fallo del bucle.
    assert _events(rendered, "job_input_rejected") == []
    assert "worker_loop_failed" not in rendered


# ----------------------------------------------------------------- 3. el reintento se completa / secuencia de tope

@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_retry_that_succeeds_completes_job_and_acks_second_delivery(stack):
    # El reintento sirve para algo: si el fallo era transitorio, la reentrega del MISMO
    # trabajo (marcada `redelivered`) lo completa y confirma con `ack`, sin ningun `nack`.
    stack.pipeline.run.side_effect = [RuntimeError(SECRET_ERROR), {"summary": "ok-tras-reintento"}]

    with pytest.raises(RuntimeError):
        _deliver(stack.worker, stack.job, tag=TAG)
    assert stack.queue.nack.call_args_list == [call(TAG, requeue=True)]
    assert stack.row()["status"] == "failed"
    stack.queue.reset_mock()

    _deliver(stack.worker, stack.job, tag=RETRY_TAG, redelivered=True)

    assert stack.queue.method_calls == [call.ack(RETRY_TAG)]
    stack.queue.nack.assert_not_called()
    row = stack.row()
    assert row["status"] == "completed"
    assert json.loads(row["result"]) == {"summary": "ok-tras-reintento"}
    assert stack.pipeline.run.call_count == 2


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_persistent_failure_runs_pipeline_exactly_twice_then_is_discarded(stack):
    # Secuencia completa del tope: 1a entrega falla y se reencola; la reentrega falla y se
    # descarta. El pipeline se ejecuta exactamente 2 veces (1 + 1 reintento) y el trabajo
    # queda `failed`; no hay una tercera oportunidad.
    stack.pipeline.run.side_effect = RuntimeError(SECRET_ERROR)

    with pytest.raises(RuntimeError):
        _deliver(stack.worker, stack.job, tag=TAG)
    _deliver(stack.worker, stack.job, tag=RETRY_TAG, redelivered=True)

    assert stack.queue.nack.call_args_list == [
        call(TAG, requeue=True),
        call(RETRY_TAG, requeue=False),
    ]
    stack.queue.ack.assert_not_called()
    assert stack.pipeline.run.call_count == 2
    row = stack.row()
    assert row["status"] == "failed"
    assert json.loads(row["result"]) == {"error": "ingestion_failed"}


# ----------------------------------------------------------------- 4. el bucle real no se atasca

@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_exhausted_retry_does_not_hold_back_next_valid_delivery(stack, capsys, caplog):
    # Con el bucle real (`run_forever`): el reintento agotado se descarta sin que escape
    # ninguna excepcion (no hay `worker_loop_failed`) y el mensaje siguiente, de OTRO tenant,
    # se procesa y se confirma en la misma ejecucion.
    configure_logging()
    valid = seed_job(stack.database, identifier="jup113-valid", tenant="tenant-b", creator="bob")

    def run(payload):
        if payload["job_id"] == stack.job["id"]:
            raise RuntimeError(SECRET_ERROR)
        return {**payload, "summary": "done"}

    stack.pipeline.run.side_effect = run
    worker = stack.worker
    worker.settings = SimpleNamespace(processor_queue_name="jup113-test")
    worker._stopping = MagicMock()
    worker._stopping.is_set.side_effect = [False, False, True]  # dos vueltas del bucle
    worker.queue.blocking_pop.side_effect = [
        _message(stack.job, TAG, redelivered=True),
        _message(valid, OTHER_TAG, redelivered=False),
        None,
    ]

    worker.run_forever()

    rendered = _capture(capsys, caplog)
    assert "worker_loop_failed" not in rendered
    assert worker.queue.nack.call_args_list == [call(TAG, requeue=False)]
    assert worker.queue.ack.call_args_list == [call(OTHER_TAG)]
    assert stack.row()["status"] == "failed"
    assert stack.row("jup113-valid")["status"] == "completed"
    assert len(_events(rendered, "job_retry_exhausted")) == 1


# ----------------------------------------------------------------- 5. permanente de entrada

def _real_pipeline_task(database):
    settings = Settings(_env_file=None, llm_provider="mock",
                        litellm_api_key="jup113-synthetic-injected-provider-key")
    provider = MagicMock(spec_set=["invoke"])
    vector = MagicMock(spec_set=["store_document"])
    pipeline = PipelineRunner(AgentRuntime(settings, provider=provider), TextChunker(48, 8),
                              MockEmbeddingProvider(8), vector)
    return IngestTask(JobRepository(database), pipeline), provider, vector


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("redelivered", [False, True])
def test_permanent_input_failure_is_discarded_the_same_with_either_flag(stack, capsys, caplog, redelivered):
    # El permanente de entrada (origen que el guardrail rechaza) se descarta en una entrega
    # con cualquier valor de la marca y se anuncia como `job_input_rejected`, NO como
    # agotamiento de reintentos: son causas distintas con diagnosticos distintos.
    configure_logging()
    hostile = "Azure Cost Management"
    job = stack.job
    job["source"] = job["payload"]["source"] = hostile
    with stack.database.engine.begin() as connection:
        connection.execute(
            text("UPDATE jobs SET source=:source, payload=:payload WHERE id=:id"),
            {"id": job["id"], "source": hostile, "payload": json.dumps(job["payload"])},
        )
    task, provider, vector = _real_pipeline_task(stack.database)
    stack.worker.task = task

    _deliver(stack.worker, job, redelivered=redelivered)  # no debe lanzar

    stack.queue.nack.assert_called_once_with(TAG, requeue=False)
    stack.queue.ack.assert_not_called()
    provider.invoke.assert_not_called()
    vector.store_document.assert_not_called()
    assert stack.row()["status"] == "failed"
    rendered = _capture(capsys, caplog)
    assert len(_events(rendered, "job_input_rejected")) == 1
    assert _events(rendered, "job_retry_exhausted") == []


# ----------------------------------------------------------------- 6. sin cambios para otros descartes

@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("redelivered", [False, True])
def test_invalid_job_message_is_discarded_without_retry_exhausted_event(stack, capsys, caplog, redelivered):
    # `InvalidJobMessage` (aqui, tenant ajeno: el trabajo no existe para ese ambito) es un
    # rechazo permanente de la entrega: `nack(requeue=False)` con cualquier marca, sin tocar
    # el estado y sin confundirlo con un reintento agotado.
    configure_logging()
    foreign = deepcopy(stack.job)
    foreign["tenant_id"] = foreign["payload"]["tenant_id"] = "tenant-ajeno"
    before = snapshot(stack.database, "jobs")

    _deliver(stack.worker, foreign, redelivered=redelivered)  # no debe lanzar

    stack.queue.nack.assert_called_once_with(TAG, requeue=False)
    stack.queue.ack.assert_not_called()
    stack.pipeline.run.assert_not_called()
    assert snapshot(stack.database, "jobs") == before
    rendered = _capture(capsys, caplog)
    assert len(_events(rendered, "job_message_rejected")) == 1
    assert _events(rendered, "job_retry_exhausted") == []


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("redelivered", [False, True])
def test_provider_error_is_discarded_without_retry_exhausted_event(stack, capsys, caplog, redelivered):
    # `ProviderError` es un fallo terminal del proveedor (ya sin reintento): se descarta con
    # `nack(requeue=False)` con cualquier marca y se anuncia como `job_provider_failed`.
    configure_logging()
    stack.pipeline.run.side_effect = ProviderError("timeout")

    _deliver(stack.worker, stack.job, redelivered=redelivered)  # no debe lanzar

    stack.queue.nack.assert_called_once_with(TAG, requeue=False)
    stack.queue.ack.assert_not_called()
    assert stack.row()["status"] == "failed"
    rendered = _capture(capsys, caplog)
    assert len(_events(rendered, "job_provider_failed")) == 1
    assert _events(rendered, "job_retry_exhausted") == []


# ----------------------------------------------------------------- 7. estado no disponible: sin tope

def _break(stack, where, original):
    """Hace fallar la persistencia del estado en `where`; devuelve el estado esperado de la fila."""
    repository = JobRepository(stack.database)
    if where == "fetch_authorized_job":
        repository.fetch_authorized_job = MagicMock(side_effect=original)
        expected_status = "queued"  # ni siquiera se leyo el trabajo
        stack.pipeline.run.side_effect = lambda payload: {"summary": "no deberia ejecutarse"}
    elif where == "mark_running":
        repository.mark_running = MagicMock(side_effect=original)
        expected_status = "queued"  # no llego a registrarse `running`
        stack.pipeline.run.side_effect = lambda payload: {"summary": "no deberia ejecutarse"}
    else:  # "mark_failed": el pipeline falla y ADEMAS no se puede registrar el fallo
        repository.mark_failed = MagicMock(side_effect=original)
        expected_status = "running"  # quedo en `running`, sin registrar `failed`
        stack.pipeline.run.side_effect = RuntimeError(SECRET_ERROR)
    stack.worker.task = IngestTask(repository, stack.pipeline)
    return expected_status


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("redelivered", [False, True])
@pytest.mark.parametrize("where", ["fetch_authorized_job", "mark_running", "mark_failed"])
@pytest.mark.parametrize("make_error", [
    lambda: OperationalError("UPDATE jobs", {}, Exception("base-de-datos-no-disponible")),
    lambda: ConnectionError("base-de-datos-no-disponible"),
], ids=["operational-error", "connection-error"])
def test_unavailable_state_is_always_requeued_even_if_redelivered(stack, capsys, caplog, make_error, where, redelivered):
    # Sin tope a proposito (tarea 4.3): si el estado del trabajo no se pudo leer o registrar,
    # NO sabemos que quedo escrito. Descartar dejaria el trabajo en `queued`/`running` sin
    # mensaje que lo recupere, asi que se reencola y se relanza la excepcion ORIGINAL con
    # cualquier valor de la marca. Esto distingue "fallo ya registrado como failed" (acotado)
    # de "estado desconocido" (no acotado).
    configure_logging()
    original = make_error()
    expected_status = _break(stack, where, original)
    before_failed = ingest_jobs_failed_total._value.get()

    with pytest.raises(type(original)) as caught:
        _deliver(stack.worker, stack.job, redelivered=redelivered)

    assert caught.value is original
    stack.queue.nack.assert_called_once_with(TAG, requeue=True)
    stack.queue.ack.assert_not_called()
    assert stack.row()["status"] == expected_status
    assert ingest_jobs_failed_total._value.get() == before_failed
    assert _events(_capture(capsys, caplog), "job_retry_exhausted") == []
