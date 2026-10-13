"""JUP-113 (RF-054-001, remediacion de mutacion): cierre de dos mutantes de `_stored_result`.

`_stored_result` valida la forma del resultado guardado de un trabajo `completed` y lo rechaza
con `InvalidJobMessage("Invalid job message.") from None`. Sobrevivian dos mutantes REALES que
las pruebas de `test_completed_result_shape.py` no distinguian:

1. Quitar `RecursionError` de `except (ValueError, RecursionError)`.
   `json.loads` lanza `RecursionError` (que NO es `ValueError`) con una anidacion patologica.
   Sin esa captura el error escaparia del `IngestTask` como error generico: el worker haria
   `nack(requeue=True)` y el mensaje volveria a la cola y fallaria igual sin fin.
2. Quitar `from None` del `raise` del `except`.
   La excepcion conservaria `__context__` con el `JSONDecodeError`, cuyo atributo `.doc` es el
   texto ÍNTEGRO del resultado guardado (datos del tenant). Con `from None`,
   `__suppress_context__` vale True y la traza no arrastra ese contexto.

No hay fase Red: el producto actual ya hace lo correcto y estas pruebas PASAN contra el; solo
faltaba la prueba que lo fije. Se verifica contra los mutantes por separado (lo hace el
orquestador).

Se usan SQLite aislada, el `JobRepository` real, el `IngestTask` real y el `ProcessorWorker`
real; los dobles solo estan en las fronteras (pipeline y cola). Los ayudantes se reutilizan de
`test_ingest_redelivery.py`, como hace `test_completed_result_shape.py`.
"""
import json
import traceback
from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from app.clients.rabbitmq_queue import QueueMessage
from app.core.logging import configure_logging
from app.core.metrics import ingest_jobs_failed_total
from app.tasks.ingest import IngestTask, InvalidJobMessage
from app.workers.runner import ProcessorWorker
from test_ingest_redelivery import (  # noqa: F401  (guarded se usa como fixture)
    guarded,
    persisted_rows,
    set_row,
)
from test_secret_boundaries import restore_logging  # noqa: F401  (fixture autouse)
from tenant_isolation_support import isolation_database  # noqa: F401  (fixture parametrizada)

# Solo SQLite: CockroachDB no es un servicio disponible offline y un skip no es valido.
# Se aplica como decorador a cada prueba con base de datos; la sonda de `json.loads` no la usa.
SQLITE_ONLY = pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)

POISON_TAG = 51
EXPOSURE_MARKER = "marcador-exposicion-jup113"

# Profundidad con la que `json.loads` lanza `RecursionError` en CPython (la sonda del tester
# midio 100000 niveles resueltos en menos de un milisegundo). Muy por encima del limite de
# recursion del escaner de `json`, de modo que no depende del valor exacto de ese limite.
DEPTH = 100000
DEEP_LIST = "[" * DEPTH + "]" * DEPTH
DEEP_OBJECT = '{"a":' * DEPTH + "1" + "}" * DEPTH

DEEP_NESTING = [
    pytest.param(DEEP_LIST, id="lista-anidada"),
    pytest.param(DEEP_OBJECT, id="objeto-anidado"),
]


def test_probe_pathological_nesting_makes_json_loads_raise_recursion_error():
    # Premisa de las pruebas siguientes: estas entradas hacen que `json.loads` lance
    # `RecursionError` y NO un `ValueError`. Si un intérprete futuro dejase de lanzarlo, las
    # pruebas de anidacion ya no ejercitarian la rama que cubre el mutante 1 y esta sonda
    # lo hace visible en lugar de dar un falso verde.
    for text in (DEEP_LIST, DEEP_OBJECT):
        with pytest.raises(RecursionError):
            json.loads(text)
        assert not issubclass(RecursionError, ValueError)


@SQLITE_ONLY
@pytest.mark.parametrize("stored_text", DEEP_NESTING)
def test_completed_redelivery_with_pathologically_nested_result_is_rejected(guarded, stored_text):
    # Resultado guardado como TEXTO con anidacion patologica. `json.loads` lanza
    # `RecursionError`; si `_stored_result` no la captura, el error escapa como generico (no
    # `InvalidJobMessage`) y el worker reencolaria sin fin. Debe rechazarse igual que un
    # resultado corrupto cualquiera, sin tocar la fila ni ejecutar el pipeline.
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_text)
    before = persisted_rows(guarded.database)
    failed_before = ingest_jobs_failed_total._value.get()

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(deepcopy(guarded.job))

    # Es exactamente InvalidJobMessage con el mensaje fijo (no una subclase ni otro error).
    assert type(caught.value) is InvalidJobMessage
    assert str(caught.value) == "Invalid job message."
    # Solo se consulta el estado: ninguna transicion, pipeline ni fila alterada.
    assert guarded.repository.calls == ["fetch_authorized_job"]
    guarded.pipeline.run.assert_not_called()
    assert persisted_rows(guarded.database) == before
    # Rechazar un mensaje invalido no es un fallo de ingesta: el contador no sube.
    assert ingest_jobs_failed_total._value.get() == failed_before


@SQLITE_ONLY
@pytest.mark.parametrize("stored_text", DEEP_NESTING)
def test_worker_discards_completed_job_with_pathologically_nested_result_in_one_delivery(
    guarded, stored_text, capsys, caplog
):
    # El mismo caso por el worker real: el rechazo llega como `InvalidJobMessage`, asi que se
    # descarta UNA vez con `nack(requeue=False)`, sin `ack` y sin relanzar. Si la
    # `RecursionError` escapase, el worker caeria en el `except Exception` generico, haria
    # `nack(requeue=True)` y relanzaria (`worker_loop_failed`): bucle de reentregas sin fin.
    configure_logging()
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_text)
    before = persisted_rows(guarded.database)
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = guarded.task

    worker._process_message(QueueMessage(deepcopy(guarded.job), delivery_tag=POISON_TAG))  # no debe lanzar

    worker.queue.nack.assert_called_once_with(POISON_TAG, requeue=False)
    worker.queue.ack.assert_not_called()
    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert "job_message_rejected" in rendered
    assert "worker_loop_failed" not in rendered
    assert guarded.repository.calls == ["fetch_authorized_job"]
    guarded.pipeline.run.assert_not_called()
    assert persisted_rows(guarded.database) == before


@SQLITE_ONLY
def test_invalid_stored_result_rejection_does_not_chain_the_decoding_error(guarded):
    # El `JSONDecodeError` de un texto corrupto lleva en `.doc` el texto íntegro del resultado
    # guardado (aqui, con un marcador). El rechazo usa `from None` para no encadenarlo.
    # - `__cause__ is None`: no hay `raise ... from error` explicito.
    # - `__suppress_context__ is True`: es la huella directa de `from None`. SIN `from None`
    #   (mutante 2), `raise` dentro del `except` deja `__suppress_context__ == False` y
    #   `__context__` apuntando al `JSONDecodeError`, de modo que esta asercion falla. La traza
    #   formateada puede no incluir el `.doc` (el mensaje de `JSONDecodeError` no lo repite),
    #   por eso la comprobacion de la traza sola NO bastaria para matar al mutante.
    corrupt = '{"secreto": "' + EXPOSURE_MARKER + '"'  # objeto cortado: JSON invalido
    set_row(guarded.database, guarded.job["id"], status="completed", result=corrupt)
    before = persisted_rows(guarded.database)

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(deepcopy(guarded.job))

    exc = caught.value
    assert str(exc) == "Invalid job message."
    assert exc.__cause__ is None
    assert exc.__suppress_context__ is True
    # El marcador del resultado guardado no aparece en la traza completa ni en el repr.
    assert EXPOSURE_MARKER not in "".join(traceback.format_exception(exc))
    assert EXPOSURE_MARKER not in repr(exc)
    assert persisted_rows(guarded.database) == before
