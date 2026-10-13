"""JUP-113 (RF-054-001): la reentrega de un trabajo `completed` exige un resultado con forma de objeto.

Defecto actual (`IngestTask.execute`, rama `completed`):
`return json.loads(result) if isinstance(result, str) else result or {}`
- un resultado guardado corrupto (`''`, `'not json'`) lanza `json.JSONDecodeError`, que es un
  `ValueError` pero NO `InvalidJobMessage`: el worker lo trata como error generico, hace
  `nack(requeue=True)` y relanza, asi que la entrega vuelve a la cola y falla igual sin fin;
- un resultado que no es un objeto (`[1]`, `"x"`, `123`, `true`) se devuelve tal cual aunque la
  firma promete `dict`;
- el texto `null` devuelve `None`;
- un valor YA decodificado (CockroachDB entrega JSONB deserializado) que sea falsy y no objeto
  (`[]`, `0`, `False`, `""`) se convierte en `{}` por el `or {}` en vez de rechazarse.

Contrato que fijan estas pruebas (lo implementa el coder):
- ausente (`NULL`), texto `null` o `None` ya decodificado -> `{}`;
- objeto (texto que decodifica a objeto, o `dict` ya decodificado) -> ese objeto (tambien `{}`);
- cualquier otra cosa -> `InvalidJobMessage("Invalid job message.")`, sin tocar la fila, sin
  `mark_*`, sin pipeline, sin contador de fallos y sin que el resultado guardado aparezca en la
  excepcion ni en los registros;
- el worker convierte ese rechazo en `nack(requeue=False)` sin relanzar y registra el evento fijo
  `job_message_rejected`.

Se usan SQLite aislada, el `JobRepository` real, el `IngestTask` real y el `ProcessorWorker` real.
Los dobles solo estan en las fronteras (pipeline y cola). Los ayudantes se reutilizan de
`test_ingest_redelivery.py`.

Clasificacion Red/guarda:
- Fallan hoy (Red): todos los rechazos de `IngestTask` y del worker, y el `null` textual.
- Pasan ya hoy (guardas contra un coder que rompa lo existente): los resultados validos objeto/NULL
  de `IngestTask` y el `ack` del worker con un resultado valido.
"""
import json
import traceback
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
import structlog

from app.clients.rabbitmq_queue import QueueMessage
from app.core.logging import configure_logging
from app.core.metrics import ingest_jobs_failed_total
from app.tasks.ingest import IngestTask, InvalidJobMessage
from app.workers.runner import ProcessorWorker
from tenant_isolation_support import isolation_database, seed_job
from test_ingest_redelivery import (  # noqa: F401  (guarded se usa como fixture)
    RecordingRepository,
    assert_no_effects,
    guarded,
    persisted_rows,
    set_row,
)
from test_secret_boundaries import restore_logging  # noqa: F401  (fixture autouse)

# Solo SQLite: CockroachDB no es un servicio disponible offline y un skip no es valido.
pytestmark = pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)

# Marcador distintivo dentro del resultado guardado: si aparece en una excepcion o en un
# registro, el rechazo esta filtrando el contenido del resultado.
MARKER = "marcador-resultado-jup113"
POISON_TAG = 41
VALID_TAG = 42

# Resultados guardados como TEXTO (lo que entrega SQLite) que el contrato rechaza. Todos llevan
# el marcador cuando el formato lo permite, para poder comprobar que no se filtra.
INVALID_TEXTS = [
    pytest.param("", id="texto-vacio"),
    pytest.param("not json", id="not-json"),
    pytest.param("{", id="llave-sin-cerrar"),
    pytest.param('{"secreto": "' + MARKER + '"', id="objeto-truncado-con-marcador"),
    pytest.param("[1]", id="lista"),
    pytest.param("[]", id="lista-vacia"),
    pytest.param('["' + MARKER + '"]', id="lista-con-marcador"),
    pytest.param('"x"', id="texto-json"),
    pytest.param('""', id="texto-json-vacio"),
    pytest.param('"' + MARKER + '"', id="texto-json-con-marcador"),
    pytest.param("123", id="numero"),
    pytest.param("0", id="cero"),
    pytest.param("true", id="booleano-true"),
    pytest.param("false", id="booleano-false"),
]

# Resultados ya DECODIFICADOS (lo que entrega CockroachDB para JSONB) que no son objeto ni None.
# Incluye los falsy (`[]`, `0`, `False`, `""`), que el `or {}` actual convierte en `{}`.
INVALID_DECODED = [
    pytest.param([1], id="lista"),
    pytest.param([], id="lista-vacia-falsy"),
    pytest.param([MARKER], id="lista-con-marcador"),
    pytest.param("x", id="texto"),
    pytest.param("", id="texto-vacio-falsy"),
    pytest.param(MARKER, id="texto-con-marcador"),
    pytest.param(123, id="numero"),
    pytest.param(0, id="cero-falsy"),
    pytest.param(True, id="booleano-true"),
    pytest.param(False, id="booleano-false-falsy"),
]

_UNSET = object()


class DecodedResultRepository(RecordingRepository):
    """Repositorio REAL que entrega el resultado ya decodificado con el valor que se le indique.

    El adaptador `decode_result` de `RecordingRepository` solo sabe producir lo que `json.loads`
    devuelve a partir de TEXTO guardado, y SQLite no puede guardar, p. ej., un `""` o un `0`
    como valor decodificado distinto de su texto. Este doble emula al controlador de
    CockroachDB: la fila es la real, pero `result` llega ya deserializado con el valor pedido.
    """

    def __init__(self, database, decoded=_UNSET):
        super().__init__(database)
        self.decoded = decoded

    def fetch_authorized_job(self, job_id, *, tenant_id, created_by):
        stored = super().fetch_authorized_job(job_id, tenant_id=tenant_id, created_by=created_by)
        if stored is not None and self.decoded is not _UNSET:
            stored = {**stored, "result": self.decoded}
            self.fetched[-1] = stored
        return stored


def _use_decoded(case, value):
    """Sustituye el repositorio del caso por uno que entrega `value` ya decodificado."""
    repository = DecodedResultRepository(case.database, value)
    case.repository = repository
    case.task = IngestTask(repository, case.pipeline)


def _assert_rejected(case, message, before, failed_before):
    """Comprueba el contrato comun de un resultado `completed` rechazado como invalido."""
    with pytest.raises(InvalidJobMessage) as caught:
        case.task.execute(message)

    # Mismo mensaje que el resto de rechazos: no distingue la causa ni la expone.
    assert type(caught.value) is InvalidJobMessage
    assert str(caught.value) == "Invalid job message."
    # El resultado guardado no se filtra por texto, `repr` ni traza completa.
    assert MARKER not in str(caught.value)
    assert MARKER not in repr(caught.value)
    assert MARKER not in "".join(traceback.format_exception(caught.value))
    # Solo se consulta el estado; ninguna transicion ni pipeline ni fila alterada.
    assert case.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(case, before)
    # Rechazar un mensaje invalido no es un fallo de ingesta: el contador no sube.
    assert ingest_jobs_failed_total._value.get() == failed_before


# ------------------------------------------------------------------ IngestTask: rechazos


@pytest.mark.parametrize("stored_text", INVALID_TEXTS)
def test_completed_redelivery_with_invalid_stored_text_is_rejected_as_invalid_message(guarded, stored_text):
    # Resultado guardado como TEXTO que no decodifica o no es un objeto. Hoy: el texto
    # corrupto lanza `JSONDecodeError` (ni siquiera InvalidJobMessage) y los textos que
    # decodifican a lista/texto/numero/booleano se DEVUELVEN sin validar.
    # (SQLite puede entregar "123"/"0"/"true" como entero por la afinidad de la columna;
    # el resultado esperado es el mismo rechazo en cualquier caso.)
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_text)
    before = persisted_rows(guarded.database)
    failed_before = ingest_jobs_failed_total._value.get()

    _assert_rejected(guarded, deepcopy(guarded.job), before, failed_before)


@pytest.mark.parametrize("decoded", INVALID_DECODED)
def test_completed_redelivery_with_invalid_decoded_value_is_rejected_as_invalid_message(guarded, decoded):
    # Resultado YA decodificado (JSONB de CockroachDB) que no es objeto ni None. Hoy se
    # devuelve tal cual, y los falsy (`[]`, `0`, `False`, `""`) se convierten en `{}` por el
    # `or {}`, que oculta un resultado corrupto como si fuese "sin resultado".
    set_row(guarded.database, guarded.job["id"], status="completed", result=json.dumps({"fila": "real"}))
    _use_decoded(guarded, decoded)
    before = persisted_rows(guarded.database)
    failed_before = ingest_jobs_failed_total._value.get()

    _assert_rejected(guarded, deepcopy(guarded.job), before, failed_before)
    # La rama ejercitada es la prevista: el repositorio entrego el valor ya decodificado.
    delivered = guarded.repository.fetched[-1]["result"]
    assert delivered == decoded
    assert type(delivered) is type(decoded)


@pytest.mark.parametrize("stored_json", [
    pytest.param("[1]", id="lista"),
    pytest.param("[]", id="lista-vacia"),
    pytest.param('["' + MARKER + '"]', id="lista-con-marcador"),
    pytest.param('"x"', id="texto"),
    pytest.param('""', id="texto-vacio"),
    pytest.param("123", id="numero"),
    pytest.param("0", id="cero"),
    pytest.param("true", id="true"),
    pytest.param("false", id="false"),
])
def test_completed_redelivery_with_json_decoded_by_adapter_is_rejected(guarded, stored_json):
    # Mismo contrato con el adaptador `decode_result` de `RecordingRepository`, que emula a
    # CockroachDB deserializando el texto que entrega SQLite. Si SQLite ya entrega un entero
    # (afinidad de columna), el adaptador no decodifica y es el rechazo "como entero".
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_json)
    guarded.repository.decode_result = True
    before = persisted_rows(guarded.database)
    failed_before = ingest_jobs_failed_total._value.get()

    _assert_rejected(guarded, deepcopy(guarded.job), before, failed_before)


# ------------------------------------------------------------------ IngestTask: validos (guardas)


@pytest.mark.parametrize("stored_text, expected", [
    pytest.param(None, {}, id="null-sin-resultado"),
    pytest.param("null", {}, id="texto-null"),
    pytest.param("{}", {}, id="objeto-vacio"),
    pytest.param('{"ok": 1, "anidado": {"a": [1, 2]}}', {"ok": 1, "anidado": {"a": [1, 2]}}, id="objeto-con-claves"),
])
@pytest.mark.parametrize("decode_result", [False, True], ids=["texto", "adaptador-decodificado"])
def test_completed_redelivery_with_object_or_null_result_returns_object(
    guarded, stored_text, expected, decode_result
):
    # Resultados validos. El texto `null` hoy devuelve `None` (Red en ese caso); el resto ya
    # funciona y es la guarda contra un coder que rompa la reentrega legitima.
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_text)
    guarded.repository.decode_result = decode_result
    before = persisted_rows(guarded.database)

    result = guarded.task.execute(deepcopy(guarded.job))

    assert result == expected
    assert isinstance(result, dict)
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


@pytest.mark.parametrize("decoded, expected", [
    pytest.param(None, {}, id="none-decodificado"),
    pytest.param({}, {}, id="dict-vacio"),
    pytest.param({"ok": 1, "lista": [1, 2]}, {"ok": 1, "lista": [1, 2]}, id="dict-con-claves"),
])
def test_completed_redelivery_with_already_decoded_object_or_none_returns_object(guarded, decoded, expected):
    # Valor ya decodificado `None` -> `{}` y objeto -> ese objeto (tambien el vacio, que no
    # debe confundirse con "resultado invalido" por ser falsy).
    set_row(guarded.database, guarded.job["id"], status="completed", result=json.dumps({"fila": "real"}))
    _use_decoded(guarded, decoded)
    before = persisted_rows(guarded.database)

    result = guarded.task.execute(deepcopy(guarded.job))

    assert result == expected
    assert isinstance(result, dict)
    assert guarded.repository.fetched[-1]["result"] == decoded
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


# ------------------------------------------------------------------ Worker (tarea 5.2)


def _worker_for(case):
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = case.task
    return worker


WORKER_INVALID = [
    pytest.param("", id="texto-vacio"),
    pytest.param("not json", id="not-json"),
    pytest.param('{"secreto": "' + MARKER + '"', id="objeto-truncado-con-marcador"),
    pytest.param("[1]", id="lista"),
    pytest.param('["' + MARKER + '"]', id="lista-con-marcador"),
    pytest.param('"x"', id="texto-json"),
    pytest.param("123", id="numero"),
    pytest.param("true", id="booleano"),
]


@pytest.mark.parametrize("stored_text", WORKER_INVALID)
def test_worker_discards_completed_job_with_invalid_result_in_one_delivery(guarded, stored_text, capsys, caplog):
    # El rechazo del resultado invalido llega al worker como `InvalidJobMessage`: se descarta
    # UNA vez con `nack(requeue=False)`, sin relanzar (la llamada devuelve normalmente) y con
    # el evento fijo `job_message_rejected`. Hoy el `JSONDecodeError` cae en el `except
    # Exception` generico: `nack(requeue=True)` y relanza (bucle sin fin); y los resultados
    # que no son objeto se `ack`-ean como si fuesen validos.
    configure_logging()
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_text)
    before = persisted_rows(guarded.database)
    worker = _worker_for(guarded)

    worker._process_message(QueueMessage(deepcopy(guarded.job), delivery_tag=POISON_TAG))  # no debe lanzar

    worker.queue.nack.assert_called_once_with(POISON_TAG, requeue=False)
    worker.queue.ack.assert_not_called()
    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert "job_message_rejected" in rendered
    # Ni el resultado guardado ni su marcador aparecen en ninguna salida.
    assert MARKER not in rendered
    assert_no_effects(guarded, before)


def test_worker_acks_completed_job_with_valid_object_result(guarded, capsys, caplog):
    # Guarda: la reentrega legitima de un completado con resultado objeto sigue confirmandose
    # (`ack`) sin `nack` ni evento de rechazo. Pasa ya hoy.
    configure_logging()
    set_row(guarded.database, guarded.job["id"], status="completed", result='{"ok": 1}')
    before = persisted_rows(guarded.database)
    worker = _worker_for(guarded)

    worker._process_message(QueueMessage(deepcopy(guarded.job), delivery_tag=VALID_TAG))

    worker.queue.ack.assert_called_once_with(VALID_TAG)
    worker.queue.nack.assert_not_called()
    captured = capsys.readouterr()
    assert "job_message_rejected" not in captured.out + captured.err + caplog.text
    assert_no_effects(guarded, before)


@pytest.mark.parametrize("stored_text", ["", "not json", '["' + MARKER + '"]'])
def test_corrupt_result_does_not_hold_back_next_valid_delivery(guarded, stored_text, capsys, caplog):
    # Con el bucle real del worker: la entrega con resultado invalido se descarta sin que
    # escape excepcion (no hay `worker_loop_failed` ni espera) y el mensaje siguiente, de OTRO
    # tenant y valido, se procesa y se confirma en la misma ejecucion.
    configure_logging()
    database = guarded.database
    set_row(database, guarded.job["id"], status="completed", result=stored_text)
    valid = seed_job(database, identifier="jup113-valid-after-corrupt", tenant="tenant-b", creator="bob")

    # Pipeline doble solo en la frontera: falla si recibe el trabajo corrupto y completa el valido.
    def run(pipeline_input):
        assert pipeline_input["job_id"] == valid["id"], "el pipeline no debe ejecutarse para el corrupto"
        return {"processed": pipeline_input["job_id"]}

    pipeline = MagicMock()
    pipeline.run.side_effect = run
    repository = RecordingRepository(database)
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = IngestTask(repository, pipeline)
    worker.settings = SimpleNamespace(processor_queue_name="jup113-test")
    worker._stopping = MagicMock()
    worker._stopping.is_set.side_effect = [False, False, True]  # dos vueltas del bucle
    worker.queue.blocking_pop.side_effect = [
        QueueMessage(deepcopy(guarded.job), POISON_TAG),
        QueueMessage(valid, VALID_TAG),
        None,
    ]

    worker.run_forever()

    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert "worker_loop_failed" not in rendered
    assert "job_message_rejected" in rendered
    assert MARKER not in rendered
    assert worker.queue.nack.call_args_list == [call(POISON_TAG, requeue=False)]
    assert worker.queue.ack.call_args_list == [call(VALID_TAG)]
    # Solo el trabajo valido llega al pipeline y pasa a completed; el corrupto queda intacto.
    pipeline.run.assert_called_once()
    rows = {row["id"]: row for row in persisted_rows(database)}
    assert rows[valid["id"]]["status"] == "completed"
    assert rows[guarded.job["id"]]["status"] == "completed"
    assert rows[guarded.job["id"]]["result"] == stored_text
    structlog.contextvars.clear_contextvars()
