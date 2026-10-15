"""JUP-113 (tareas 6.1 y 6.2): reintentos acotados de ingesta con SERVICIOS REALES (opt-in).

CockroachDB + pgvector + RabbitMQ reales y desechables. No hay fase Red: estas pruebas
verifican, de extremo a extremo y sin dobles en las fronteras de persistencia ni de cola, lo
que ya implementan `IngestTask`, `ProcessorWorker._process_message` y `RabbitMQQueue`
(descarte de un fallo permanente de entrada, reintento unico de un fallo no clasificado con la
marca `redelivered` REAL del broker, y rechazo de un resultado guardado que no es objeto).

Requieren las tres variables de entorno (sin ellas TODAS se omiten limpiamente, igual que
`test_tenant_isolation_integration.py`, cuyas fixtures se reutilizan por importacion):

    PROCESSOR_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:<puerto>/defaultdb?sslmode=disable'
    JUP086_VECTOR_TEST_URL='postgresql+psycopg://postgres@127.0.0.1:<puerto>/postgres'
    JUP086_RABBITMQ_TEST_URL='amqp://<usuario>:<clave>@127.0.0.1:<puerto>/%2F'

Comando (desde `apps/processor`):

    python -m pytest tests/test_ingestion_retry_integration.py -q -ra -p no:cacheprovider

Las fixtures crean y borran su propia base y su propia cola con UUID y rechazan cualquier
destino que no sea desechable: estas pruebas no purgan colas ni tocan otras bases.

Los trabajos se siembran con `seed_job` y se publican directamente en la cola; no se usa el
backend. El worker es el real (`ProcessorWorker.__new__` + `_process_message`) y el bucle de
consumo se sustituye por `pump`, una version ACOTADA del bucle real: nunca se cuelga, de modo
que contra un codigo defectuoso la prueba falla por asercion y no queda en bucle infinito.
"""
import json
import traceback
from unittest.mock import MagicMock

import pika
import pytest
from sqlalchemy import text

from app.agents.service import AgentRuntime
from app.clients.rabbitmq_queue import RabbitMQQueue
from app.core.config import Settings
from app.core.logging import configure_logging
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask, IngestionFailed
from app.workers.runner import ProcessorWorker
from tenant_isolation_support import cockroach_isolation_database, seed_job, snapshot  # noqa: F401
from test_azure_cost_cockroach_integration import database_factory  # noqa: F401
from test_secret_boundaries import restore_logging  # noqa: F401  (fixture autouse)
from test_tenant_isolation_integration import real_database, real_queue  # noqa: F401
from test_tenant_isolation_vector import vector_snapshot, vector_store  # noqa: F401

# Origen real del defecto: pasa la forma del processor (no vacio) pero el guardrail lo rechaza.
HOSTILE_SOURCE = "Azure Cost Management"
# Origen valido para el guardrail pero no soportado: la ruta `unsupported` no llama al proveedor.
VALID_SOURCE = "local-smoke"
# Marcador de la causa de un fallo no clasificado: no debe aparecer en ninguna salida.
MARKER = "marcador-integracion-jup113"


# ------------------------------------------------------------------ ayudantes


def pump(worker, queue, limit=10, errors=None):
    """Version acotada del bucle del worker: entrega hasta vaciar la cola o hasta `limit` entregas.

    Procesa cada mensaje con `_process_message` y absorbe las excepciones que el bucle real
    capturaria (`except Exception`), anotandolas en `errors` si se pasa. El tope `limit` es lo
    que impide un bucle infinito si el codigo reencolase sin fin: la prueba fallaria entonces
    porque se procesarian `limit` entregas y no las esperadas.
    """
    processed = []
    while len(processed) < limit:
        message = queue.blocking_pop(timeout=2)
        if message is None:
            break
        processed.append(message)
        try:
            worker._process_message(message)
        except Exception as exc:  # igual que `run_forever`
            if errors is not None:
                errors.append(exc)
    return processed


def publish(queue, job):
    """Publica el trabajo tal cual en la cola real (mensaje persistente, como el backend)."""
    queue.channel.basic_publish(
        exchange="", routing_key=queue.queue_name, body=json.dumps(job),
        properties=pika.BasicProperties(delivery_mode=2),
    )


def assert_queue_empty(queue):
    """El estado FINAL de la cola: nada listo y nada pendiente de confirmar.

    Primero `basic_get` en la misma conexion (no queda mensaje listo). Despues se cierra esa
    conexion y se mira desde otra nueva: un mensaje entregado y NI ack NI nack (en vuelo)
    volveria a la cola al cerrar la conexion y apareceria aqui, de modo que una entrega sin
    resolver no pasa por "cola vacia".
    """
    queue._connect()
    assert queue.channel.basic_get(queue=queue.queue_name, auto_ack=False) == (None, None, None)
    queue.close()
    fresh = RabbitMQQueue(queue.rabbitmq_url, queue.queue_name)
    try:
        fresh._connect()
        assert fresh.channel.basic_get(queue=fresh.queue_name, auto_ack=False) == (None, None, None)
    finally:
        fresh.close()


def set_source(database, job, source):
    """Guarda `source` en la fila, en el payload y en el dict del mensaje, de forma coherente.

    El processor exige que fila, payload y mensaje coincidan; si no, descarta por
    `InvalidJobMessage` y nunca llegaria al guardrail que se quiere ejercitar.
    """
    job["source"] = job["payload"]["source"] = source
    with database.engine.begin() as connection:
        connection.execute(
            text("UPDATE jobs SET source=:source, payload=CAST(:payload AS JSONB) WHERE id=:id"),
            {"id": job["id"], "source": source, "payload": json.dumps(job["payload"])},
        )


def as_object(value):
    """Normaliza el JSONB leido: el controlador de CockroachDB ya lo entrega decodificado."""
    return json.loads(value) if isinstance(value, str) else value


def job_row(database, identifier):
    return next(row for row in snapshot(database, "jobs")[0] if row["id"] == identifier)


def build_worker(database, queue, vector, agent=None):
    """Worker real con pipeline real; solo se dobla la frontera del proveedor (o del agente).

    Sin `agent` se usa el `AgentRuntime` real con un proveedor doblado que no debe llamarse
    (la ruta `unsupported` no lo invoca). Con `agent` se sustituye el agente completo por un
    doble que falla o acierta a voluntad. En ambos casos el chunker, el embedding, el
    `PipelineRunner` (LangGraph), el repositorio, el almacen vectorial y la cola son reales.
    `pipeline.run` se envuelve para CONTAR las ejecuciones sin cambiar su comportamiento.
    """
    provider = MagicMock(spec_set=["invoke"])
    if agent is None:
        settings = Settings(_env_file=None, llm_provider="mock", litellm_api_key="jup113-synthetic-injected-provider-key")
        agent = AgentRuntime(settings, provider=provider)
    pipeline = PipelineRunner(agent, TextChunker(64, 8), MockEmbeddingProvider(8), vector)
    pipeline.run = MagicMock(wraps=pipeline.run)
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = queue
    worker.task = IngestTask(JobRepository(database), pipeline)
    worker.provider = provider
    worker.pipeline = pipeline
    return worker


class ScriptedAgent:
    """Doble del agente: cada llamada sigue el guion (excepcion -> se lanza, valor -> se devuelve).

    La ultima entrada del guion se repite si hay mas llamadas que entradas.
    """

    def __init__(self, *script):
        self.script = script
        self.calls = 0

    def invoke(self, state, status):
        outcome = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def rendered(capsys, caplog):
    captured = capsys.readouterr()
    return captured.out + captured.err + caplog.text


# ------------------------------------------------------------------ 6.1: un envenenado no retiene a un valido


def test_poisoned_job_does_not_hold_back_valid_job_of_another_tenant(real_database, real_queue, vector_store, capsys, caplog):
    # RF-086-004 con servicios reales: dos trabajos de tenants distintos se publican en este
    # orden (primero el envenenado). Antes del cambio el envenenado se reencolaba sin fin y el
    # valido no se procesaba nunca. Ahora el envenenado se descarta en UNA entrega y el valido
    # se completa y llega a pgvector, sin que la cola conserve nada.
    configure_logging()
    poison = seed_job(real_database, identifier="jup113-poison", tenant="tenant-a", creator="alice")
    valid = seed_job(real_database, identifier="jup113-valid", tenant="tenant-b", creator="bob")
    set_source(real_database, poison, HOSTILE_SOURCE)
    set_source(real_database, valid, VALID_SOURCE)
    publish(real_queue, poison)
    publish(real_queue, valid)
    worker = build_worker(real_database, real_queue, vector_store)
    errors = []

    processed = pump(worker, real_queue, errors=errors)

    # Exactamente dos entregas: ni el envenenado se reintenta ni el valido se retrasa.
    assert [message.payload["id"] for message in processed] == ["jup113-poison", "jup113-valid"]
    # Ninguna entrega del envenenado fue reentrega (se descarto en la primera).
    assert [message.redelivered for message in processed] == [False, False]
    # El descarte no relanza: el bucle real no habria registrado `worker_loop_failed`.
    assert errors == []
    row = job_row(real_database, "jup113-poison")
    assert row["status"] == "failed"
    assert as_object(row["result"]) == {"error": "ingestion_failed"}
    assert job_row(real_database, "jup113-valid")["status"] == "completed"
    # El rechazo ocurre en el guardrail, antes de cualquier efecto externo: ni proveedor.
    worker.provider.invoke.assert_not_called()
    # Solo el documento del valido llega a pgvector, y con su propio tenant.
    documents = vector_snapshot(vector_store)[0]
    assert [(doc["job_id"], doc["tenant_id"]) for doc in documents] == [("jup113-valid", "tenant-b")]
    output = rendered(capsys, caplog)
    assert "job_input_rejected" in output
    assert "worker_loop_failed" not in output
    assert HOSTILE_SOURCE.lower() not in output.lower()
    assert_queue_empty(real_queue)


# ------------------------------------------------------------------ 6.2: un fallo no clasificado se reintenta UNA vez


def test_unclassified_failure_is_retried_once_with_real_broker_redelivered_flag(real_database, real_queue, vector_store, capsys, caplog):
    # Un fallo no clasificado (RuntimeError del agente) se reencola UNA vez: la segunda entrega
    # llega con `redelivered=True` puesta por el BROKER REAL (no por un doble) y se descarta
    # sin relanzar. Sin el tope, el mensaje volveria a la cola indefinidamente y `pump`
    # agotaria su limite de entregas.
    configure_logging()
    job = seed_job(real_database, identifier="jup113-flaky")
    publish(real_queue, job)
    agent = ScriptedAgent(RuntimeError(MARKER))
    worker = build_worker(real_database, real_queue, vector_store, agent=agent)
    errors = []

    processed = pump(worker, real_queue, errors=errors)

    assert worker.pipeline.run.call_count == 2
    assert [message.redelivered for message in processed] == [False, True]
    # Solo la primera entrega relanza (nack requeue=True + raise); la segunda se descarta.
    assert len(errors) == 1 and isinstance(errors[0], IngestionFailed) and errors[0].permanent is False
    row = job_row(real_database, "jup113-flaky")
    assert row["status"] == "failed"
    assert as_object(row["result"]) == {"error": "ingestion_failed"}
    assert vector_snapshot(vector_store)[0] == []
    output = rendered(capsys, caplog)
    assert "job_retry_exhausted" in output
    assert "worker_loop_failed" not in output
    # La causa no se filtra ni por la salida ni por la traza de la excepcion relanzada.
    assert MARKER not in output
    assert MARKER not in "".join(traceback.format_exception(errors[0]))
    assert_queue_empty(real_queue)


def test_retry_completes_when_second_delivery_succeeds(real_database, real_queue, vector_store):
    # El reintento tiene sentido: si el fallo era transitorio, la segunda entrega completa el
    # trabajo, deja UN solo documento en pgvector y la cola vacia.
    job = seed_job(real_database, identifier="jup113-recovers")
    publish(real_queue, job)
    agent = ScriptedAgent(RuntimeError(MARKER), {"status": "ok"})
    worker = build_worker(real_database, real_queue, vector_store, agent=agent)
    errors = []

    processed = pump(worker, real_queue, errors=errors)

    assert len(processed) == 2
    assert [message.redelivered for message in processed] == [False, True]
    assert len(errors) == 1  # solo el fallo de la primera entrega
    assert worker.pipeline.run.call_count == 2
    assert job_row(real_database, "jup113-recovers")["status"] == "completed"
    documents = vector_snapshot(vector_store)[0]
    assert [(doc["job_id"], doc["tenant_id"]) for doc in documents] == [("jup113-recovers", "tenant-a")]
    assert_queue_empty(real_queue)


def test_interrupted_first_delivery_arrives_redelivered_and_is_discarded_after_one_run(real_database, real_queue, vector_store):
    # Edge case: si la primera entrega se interrumpe (conexion perdida sin ack ni nack), el
    # broker la reentrega YA marcada `redelivered`. Con un pipeline que falla, esa entrega se
    # descarta tras UNA sola ejecucion: el tope es "una reentrega como maximo" y no garantiza
    # ninguna reentrega adicional.
    job = seed_job(real_database, identifier="jup113-interrupted")
    publish(real_queue, job)
    first = real_queue.blocking_pop(timeout=2)
    assert first is not None and first.redelivered is False
    real_queue.close()  # conexion perdida sin responder: el broker devuelve el mensaje
    second_queue = RabbitMQQueue(real_queue.rabbitmq_url, real_queue.queue_name)
    try:
        agent = ScriptedAgent(RuntimeError(MARKER))
        worker = build_worker(real_database, second_queue, vector_store, agent=agent)
        errors = []

        processed = pump(worker, second_queue, errors=errors)

        assert len(processed) == 1
        assert processed[0].redelivered is True
        assert worker.pipeline.run.call_count == 1
        assert errors == []  # descartada sin relanzar
        assert job_row(real_database, "jup113-interrupted")["status"] == "failed"
        assert vector_snapshot(vector_store)[0] == []
        assert_queue_empty(second_queue)
    finally:
        # Solo se cierra la conexion: la cola la borra la fixture `real_queue`.
        second_queue.close()


# ------------------------------------------------------------------ JSONB real (RF-054-001)

# (valor JSONB tal cual se guarda, tipo Python que entrega el controlador de CockroachDB).
# `None` en el primer campo es SQL NULL; el texto `null` es un JSONB null (ambos llegan como None).
VALID_RESULTS = [
    pytest.param('{"ok": 1}', dict, id="objeto"),
    pytest.param("{}", dict, id="objeto-vacio"),
    pytest.param("null", type(None), id="jsonb-null"),
    pytest.param(None, type(None), id="sql-null"),
]
INVALID_RESULTS = [
    pytest.param("[1]", list, id="lista"),
    pytest.param("[]", list, id="lista-vacia"),
    pytest.param('"x"', str, id="texto-json"),
    pytest.param("123", int, id="numero"),
    pytest.param("0", int, id="cero"),
    pytest.param("true", bool, id="true"),
    pytest.param("false", bool, id="false"),
]


def completed_job_with_result(database, literal):
    """Siembra un `completed` y fija su `result` con SQL a un JSONB concreto (o SQL NULL)."""
    job = seed_job(database, identifier="jup113-json", status="completed")
    with database.engine.begin() as connection:
        connection.execute(
            text("UPDATE jobs SET result = CAST(:value AS JSONB) WHERE id = 'jup113-json'"),
            {"value": literal},
        )
    return job


@pytest.mark.parametrize("literal, python_type", VALID_RESULTS)
def test_real_jsonb_object_or_null_result_is_acked(real_database, real_queue, capsys, caplog, literal, python_type):
    # Un `completed` con resultado objeto, objeto vacio o ausente (SQL NULL o JSONB null) es una
    # reentrega legitima: termina con `ack`, sin ejecutar el pipeline ni tocar la fila. Se
    # incluye el objeto vacio, que es falsy y no debe confundirse con un resultado invalido.
    configure_logging()
    job = completed_job_with_result(real_database, literal)
    delivered = real_database.fetch_authorized_job(job["id"], tenant_id=job["tenant_id"], created_by=job["created_by"])["result"]
    assert type(delivered) is python_type  # frontera real del controlador
    publish(real_queue, job)
    before = snapshot(real_database, "jobs")
    pipeline = MagicMock(spec_set=["run"])
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = real_queue
    worker.task = IngestTask(JobRepository(real_database), pipeline)
    errors = []

    processed = pump(worker, real_queue, errors=errors)

    assert len(processed) == 1 and errors == []
    pipeline.run.assert_not_called()
    assert snapshot(real_database, "jobs") == before
    output = rendered(capsys, caplog)
    assert "job_message_rejected" not in output and "worker_loop_failed" not in output
    assert_queue_empty(real_queue)


@pytest.mark.parametrize("literal, python_type", INVALID_RESULTS)
def test_real_jsonb_non_object_result_is_nacked_without_requeue(real_database, real_queue, capsys, caplog, literal, python_type):
    # Un `completed` cuyo resultado guardado NO es un objeto (lista, texto, numero, booleano,
    # incluidos los falsy `[]`, `0` y `false`) no se arregla reentregando el mismo mensaje: se
    # descarta con `nack(requeue=False)` en UNA entrega, sin relanzar, sin tocar la fila y sin
    # ejecutar el pipeline. Con el defecto anterior, los falsy se convertian en `{}` por `or {}`
    # y el resto se devolvia tal cual como si fuese valido.
    configure_logging()
    job = completed_job_with_result(real_database, literal)
    delivered = real_database.fetch_authorized_job(job["id"], tenant_id=job["tenant_id"], created_by=job["created_by"])["result"]
    # Anota la frontera real: el controlador entrega el JSONB YA decodificado a este tipo
    # (un `"x"` JSON llega como `str`, `123`/`0` como `int`, `true` como `bool`).
    assert type(delivered) is python_type
    publish(real_queue, job)
    before = snapshot(real_database, "jobs")
    pipeline = MagicMock(spec_set=["run"])
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = real_queue
    worker.task = IngestTask(JobRepository(real_database), pipeline)
    errors = []

    processed = pump(worker, real_queue, errors=errors)

    assert len(processed) == 1  # una sola entrega: no se reencola
    assert errors == []  # sin relanzar: el bucle real no registraria `worker_loop_failed`
    pipeline.run.assert_not_called()
    assert snapshot(real_database, "jobs") == before
    output = rendered(capsys, caplog)
    assert "job_message_rejected" in output
    assert "worker_loop_failed" not in output
    assert_queue_empty(real_queue)
