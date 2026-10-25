"""JUP-113 (RF-054-001, correccion de la validacion del PR #118): cadena JSONB con CockroachDB y RabbitMQ REALES (opt-in).

Reproduccion minima del hallazgo de la validacion: en produccion `jobs.result` es JSONB y el
controlador de CockroachDB lo entrega YA decodificado. Un JSONB que contiene una CADENA
(por ejemplo la cadena de dos caracteres `{}` o la de cuatro caracteres `null`) llega como `str`;
`IngestTask` lo volvia a decodificar con `json.loads`, obtenia `dict`/`None` y el worker lo aceptaba con `ack` en lugar de descartarlo con
`nack(requeue=False)`. Aqui se ejercita con la base y el broker reales, sin dobles en esas fronteras;
el unico doble es el pipeline (`MagicMock`), que nunca debe ejecutarse para un `completed`.

Fase Red (antes de la correccion): los tres casos de cadena JSONB fallan con `ack=[call(<tag>)]` y
`nack=[]`. Los controles (objeto, `{}`, JSONB null, SQL NULL y la cadena `"x"`) pasan ya hoy y
protegen la reentrega legitima. La propiedad `json_stored_as_text` falla hoy por AttributeError.

Requieren `PROCESSOR_COCKROACH_TEST_URL` y `JUP086_RABBITMQ_TEST_URL` (sin ellas se omiten limpiamente
mediante las fixtures reutilizadas; este archivo NO necesita pgvector ni `JUP086_VECTOR_TEST_URL`):

    PROCESSOR_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:<puerto>/defaultdb?sslmode=disable'
    JUP086_RABBITMQ_TEST_URL='amqp://<usuario>:<clave>@127.0.0.1:<puerto>/%2F'

Comando (desde `apps/processor`):

    python -m pytest tests/test_ingestion_jsonb_string_integration.py -q -ra -p no:cacheprovider

Las fixtures crean y borran su propia base y su propia cola con UUID y rechazan cualquier destino que
no sea desechable. Se reutilizan por importacion los ayudantes de `test_ingestion_retry_integration.py`.
"""
import json
from unittest.mock import MagicMock, call

import pytest

from app.core.logging import configure_logging
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask
from app.workers.runner import ProcessorWorker
from tenant_isolation_support import cockroach_isolation_database, seed_job, snapshot  # noqa: F401
from test_azure_cost_cockroach_integration import database_factory  # noqa: F401
from test_ingestion_retry_integration import (
    assert_queue_empty,
    completed_job_with_result,
    publish,
    pump,
    rendered,
)
from test_secret_boundaries import restore_logging  # noqa: F401  (fixture autouse)
from test_tenant_isolation_integration import real_database, real_queue  # noqa: F401

# Marcador dentro de una cadena JSONB: no debe aparecer en ninguna salida del rechazo.
MARKER = "marcador-cadena-jsonb-integracion-jup113"


def deliver(database, queue, job):
    """Publica `job`, lo entrega al worker REAL y devuelve lo observable de la entrega.

    Se envuelven `ack` y `nack` de la cola real (`MagicMock(wraps=...)`) para anotar como se
    resolvio la entrega SIN cambiar su comportamiento: el broker recibe la respuesta real. El
    pipeline es un doble que falla si se ejecuta (un `completed` no debe reejecutarse).
    """
    publish(queue, job)
    queue.ack = MagicMock(wraps=queue.ack)
    queue.nack = MagicMock(wraps=queue.nack)
    pipeline = MagicMock(spec_set=["run"])
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = queue
    worker.task = IngestTask(JobRepository(database), pipeline)
    errors = []
    processed = pump(worker, queue, errors=errors)
    return processed, errors, pipeline


def delivered_result(database, job):
    """El `result` tal cual lo entrega el controlador real a traves de `fetch_authorized_job`."""
    return database.fetch_authorized_job(job["id"], tenant_id=job["tenant_id"], created_by=job["created_by"])["result"]


# ------------------------------------------------------------------ propiedad real


def test_real_cockroach_repository_does_not_store_json_as_text(real_database):
    # El motor real es CockroachDB: entrega el JSONB decodificado, no como texto. Hoy falla por
    # AttributeError (el nombre es nuevo); es la propiedad que gobierna la decision del IngestTask.
    assert real_database.engine.dialect.name != "sqlite"
    assert JobRepository(real_database).json_stored_as_text is False


# ------------------------------------------------------------------ Red: cadena JSONB


@pytest.mark.parametrize("value", [
    pytest.param("{}", id="objeto-vacio-como-cadena"),
    pytest.param('{"ok":1}', id="objeto-como-cadena"),
    pytest.param("null", id="null-como-cadena"),
    pytest.param('{"secreto": "' + MARKER + '"}', id="objeto-con-marcador-como-cadena"),
])
def test_real_jsonb_string_with_json_content_is_nacked_without_requeue(real_database, real_queue, capsys, caplog, value):
    # El JSONB guardado contiene una CADENA (`json.dumps(value)` la entrecomilla) cuyo texto parece
    # JSON de objeto o de `null`. Una cadena JSON no es un objeto: se descarta en UNA entrega con
    # `nack(requeue=False)`, sin `ack`, sin relanzar, sin tocar la fila y sin ejecutar el pipeline.
    # Hoy la doble decodificacion la convierte en `dict`/`None` y se acepta con `ack` (el hallazgo).
    configure_logging()
    job = completed_job_with_result(real_database, json.dumps(value))
    delivered = delivered_result(real_database, job)
    # Frontera real: el controlador entrega la cadena JSONB como `str` (no como dict ni None).
    assert type(delivered) is str and delivered == value
    before = snapshot(real_database, "jobs")

    processed, errors, pipeline = deliver(real_database, real_queue, job)

    assert len(processed) == 1  # una sola entrega: no se reencola
    tag = processed[0].delivery_tag
    # Se comprueba la resolucion exacta, no solo "algo ocurrio": el estado Red es ack=[call(tag)], nack=[].
    # Un solo diccionario para que el fallo muestre ack y nack a la vez (Red: ack=[call(tag)], nack=[]).
    assert {"ack": real_queue.ack.call_args_list, "nack": real_queue.nack.call_args_list} == {
        "ack": [], "nack": [call(tag, requeue=False)],
    }
    assert errors == []  # sin relanzar: el bucle real no registraria `worker_loop_failed`
    pipeline.run.assert_not_called()
    assert snapshot(real_database, "jobs") == before
    output = rendered(capsys, caplog)
    assert "job_message_rejected" in output
    assert "worker_loop_failed" not in output
    assert MARKER not in output  # el valor guardado no se filtra a los registros
    assert_queue_empty(real_queue)


# ------------------------------------------------------------------ controles (pasan ya hoy)


@pytest.mark.parametrize("literal, python_type", [
    pytest.param('{"ok": 1}', dict, id="objeto"),
    pytest.param("{}", dict, id="objeto-vacio"),
    pytest.param("null", type(None), id="jsonb-null"),
    pytest.param(None, type(None), id="sql-null"),
])
def test_real_jsonb_object_or_null_is_still_acked(real_database, real_queue, capsys, caplog, literal, python_type):
    # Control: la correccion no debe rechazar la reentrega legitima. Un JSONB objeto (tambien el
    # vacio, falsy), un JSONB null y un SQL NULL se confirman con `ack`, sin `nack`, sin pipeline y
    # sin tocar la fila. El tipo entregado se anota: objeto -> dict, null/NULL -> None.
    configure_logging()
    job = completed_job_with_result(real_database, literal)
    assert type(delivered_result(real_database, job)) is python_type
    before = snapshot(real_database, "jobs")

    processed, errors, pipeline = deliver(real_database, real_queue, job)

    assert len(processed) == 1 and errors == []
    assert real_queue.ack.call_args_list == [call(processed[0].delivery_tag)]
    assert real_queue.nack.call_args_list == []
    pipeline.run.assert_not_called()
    assert snapshot(real_database, "jobs") == before
    output = rendered(capsys, caplog)
    assert "job_message_rejected" not in output and "worker_loop_failed" not in output
    assert_queue_empty(real_queue)


def test_real_jsonb_plain_string_is_still_nacked_without_requeue(real_database, real_queue, capsys, caplog):
    # Control: una cadena JSONB cuyo contenido NO es JSON (`"x"`) ya se descartaba antes porque
    # `json.loads("x")` falla; debe seguir descartandose con `nack(requeue=False)`. Pasa ya hoy.
    configure_logging()
    job = completed_job_with_result(real_database, json.dumps("x"))
    delivered = delivered_result(real_database, job)
    assert type(delivered) is str and delivered == "x"
    before = snapshot(real_database, "jobs")

    processed, errors, pipeline = deliver(real_database, real_queue, job)

    assert len(processed) == 1 and errors == []
    assert real_queue.nack.call_args_list == [call(processed[0].delivery_tag, requeue=False)]
    assert real_queue.ack.call_args_list == []
    pipeline.run.assert_not_called()
    assert snapshot(real_database, "jobs") == before
    output = rendered(capsys, caplog)
    assert "job_message_rejected" in output and "worker_loop_failed" not in output
    assert_queue_empty(real_queue)
