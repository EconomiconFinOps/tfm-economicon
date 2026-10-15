"""JUP-113 (RF-054-001, correccion de la validacion del PR #118): la representacion del JSON guardado.

Hallazgo reproducido con CockroachDB y RabbitMQ reales: `_stored_result` aplicaba `json.loads` a
CUALQUIER `str`. En produccion `jobs.result` es JSONB y el controlador lo entrega YA decodificado:
un `str` ahi es siempre una CADENA JSON, que nunca es un objeto. Pero si esa cadena contenia `{}`,
`{"ok":1}` o `null`, la segunda decodificacion la convertia en `dict`/`None` y el worker la
aceptaba con `ack` (debia ser `nack(requeue=False)`). SQLite (solo pruebas) guarda el objeto
serializado como TEXTO, de modo que no basta con rechazar todo `str`: hay que distinguir ambas
representaciones.

Contrato que fijan estas pruebas (lo implementa el coder; aun NO existe):
- `JobRepository.json_stored_as_text` (propiedad booleana de solo lectura): `True` si el dialecto
  del motor es `sqlite`, `False` en cualquier otro (CockroachDB, PostgreSQL).
- `IngestTask` lee `getattr(repository, "json_stored_as_text", True)` al validar un `completed`:
  - `True` (texto serializado) -> comportamiento actual: un `str` se decodifica con `json.loads`.
  - `False` (JSONB ya decodificado) -> un `str` NUNCA se decodifica y se rechaza con
    `InvalidJobMessage("Invalid job message.")`; `None` -> `{}`; `dict` -> el dict; otro tipo ->
    rechazo.
  - sin el atributo (dobles) -> se comporta como `True` (compatibilidad).
- El rechazo conserva todas las garantias ya fijadas: tipo exacto, mensaje fijo, fila intacta, solo
  `fetch_authorized_job`, pipeline sin ejecutar, contador de fallos sin cambios y el valor guardado
  ausente de `str`, `repr`, traza y registros; por el worker, `nack(tag, requeue=False)`, sin `ack`,
  evento `job_message_rejected` y sin `worker_loop_failed`.

Clasificacion Red/guarda:
- Fallan hoy (Red): la propiedad (AttributeError: el nombre es nuevo) y el rechazo de las cadenas
  decodificadas `'{}'`, `'{"ok":1}'` y `'null'` (DID NOT RAISE) con `json_stored_as_text=False`,
  tanto en `IngestTask` como por el worker.
- Pasan ya hoy (guardas contra un coder que rompa lo existente): los validos con `False`, la
  compatibilidad con texto en SQLite, el doble sin atributo y el `ack` con `True`.

Los ayudantes (`RecordingRepository`, `guarded`, `set_row`, `persisted_rows`, `assert_no_effects`)
se reutilizan por importacion de `test_ingest_redelivery.py`. Solo SQLite: el equivalente con
servicios reales esta en `test_ingestion_jsonb_string_integration.py` (opt-in).
"""
import traceback
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from app.clients.rabbitmq_queue import QueueMessage
from app.core.logging import configure_logging
from app.core.metrics import ingest_jobs_failed_total
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask, InvalidJobMessage
from app.workers.runner import ProcessorWorker
from tenant_isolation_support import isolation_database  # noqa: F401  (fixture)
from test_ingest_redelivery import (  # noqa: F401  (guarded se usa como fixture)
    RecordingRepository,
    assert_no_effects,
    guarded,
    persisted_rows,
    set_row,
)
from test_secret_boundaries import restore_logging  # noqa: F401  (fixture autouse)

# Solo SQLite: CockroachDB no es un servicio disponible offline y un skip no es valido.
# Este `pytestmark` exige la fixture `isolation_database` en TODAS las pruebas del archivo; las
# que usan una base falsa la reciben sin usarla (solo para satisfacer la marca).
pytestmark = pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)

# Marcador dentro de la cadena guardada: si aparece en una excepcion o registro, el rechazo filtra
# el valor guardado.
MARKER = "marcador-cadena-jsonb-jup113"
TAG = 77

# Cadenas JSON ya decodificadas que el contrato rechaza con `json_stored_as_text=False`. Las tres
# primeras son las reproducidas con CockroachDB real: la segunda decodificacion las convertia en
# `dict`/`None` y se aceptaban. El resto confirma que NINGUNA cadena es un objeto, tenga el
# contenido que tenga (valido JSON o no).
JSONB_STRINGS = [
    pytest.param("{}", id="objeto-vacio-como-cadena"),
    pytest.param('{"ok":1}', id="objeto-como-cadena"),
    pytest.param("null", id="null-como-cadena"),
    pytest.param("[1]", id="lista-como-cadena"),
    pytest.param("true", id="true-como-cadena"),
    pytest.param("123", id="numero-como-cadena"),
    pytest.param('"x"', id="cadena-json-como-cadena"),
    pytest.param("", id="cadena-vacia"),
    pytest.param("not json", id="no-json"),
    pytest.param('{"secreto": "' + MARKER + '"}', id="objeto-con-marcador-como-cadena"),
    pytest.param(MARKER, id="marcador-suelto"),
]

_UNSET = object()


class JsonbLikeRepository(RecordingRepository):
    """Repositorio REAL que emula al controlador de CockroachDB para la columna JSONB.

    Tiene `json_stored_as_text=False` (como el real sobre Cockroach) y entrega `result` YA
    decodificado con el valor indicado; el resto de la fila es la real de SQLite. Un `str`
    directo representa una CADENA JSON guardada en el JSONB (no un objeto serializado).
    La propiedad se sobrescribe a proposito: asi el contrato del IngestTask se prueba sin
    depender de la deteccion por dialecto (que se prueba aparte).
    """

    def __init__(self, database, decoded=_UNSET):
        super().__init__(database)
        self.decoded = decoded

    @property
    def json_stored_as_text(self):
        return False

    def fetch_authorized_job(self, job_id, *, tenant_id, created_by):
        stored = super().fetch_authorized_job(job_id, tenant_id=tenant_id, created_by=created_by)
        if stored is not None and self.decoded is not _UNSET:
            stored = {**stored, "result": self.decoded}
            self.fetched[-1] = stored
        return stored


class TextStoredRepository(RecordingRepository):
    """Repositorio REAL que declara explicitamente `json_stored_as_text=True` (como SQLite)."""

    @property
    def json_stored_as_text(self):
        return True


class AttributelessRepository:
    """Doble minimo que NO define `json_stored_as_text`: delega en el repositorio real.

    Representa a los dobles y `MagicMock` de otras pruebas: el contrato exige tratarlos como
    texto serializado (valor por defecto `True`) para no romper la compatibilidad.
    """

    def __init__(self, database):
        self._real = JobRepository(database)
        self.calls = []

    def fetch_authorized_job(self, job_id, *, tenant_id, created_by):
        self.calls.append("fetch_authorized_job")
        return self._real.fetch_authorized_job(job_id, tenant_id=tenant_id, created_by=created_by)

    def mark_running(self, job_id, **scope):
        self.calls.append("mark_running")
        return self._real.mark_running(job_id, **scope)

    def mark_completed(self, job_id, result, **scope):
        self.calls.append("mark_completed")
        return self._real.mark_completed(job_id, result, **scope)

    def mark_failed(self, job_id, error_message, **scope):
        self.calls.append("mark_failed")
        return self._real.mark_failed(job_id, error_message, **scope)


def _use(case, repository):
    """Sustituye el repositorio del caso conservando el pipeline guardian."""
    case.repository = repository
    case.task = IngestTask(repository, case.pipeline)


def _use_jsonb(case, decoded):
    """El caso entrega `decoded` ya decodificado y con `json_stored_as_text=False`."""
    _use(case, JsonbLikeRepository(case.database, decoded))


def _worker_for(case):
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = case.task
    return worker


def _mark_completed(case):
    # Fila `completed` real; el valor decodificado lo sobrescribe el repositorio al leer.
    set_row(case.database, case.job["id"], status="completed", result='{"fila": "real"}')


# ------------------------------------------------------------------ 1. la propiedad


def test_json_stored_as_text_is_true_for_real_sqlite_database(isolation_database):
    # SQLite guarda el objeto serializado como TEXTO: el repositorio debe declararlo asi.
    repository = JobRepository(isolation_database)

    assert isolation_database.engine.dialect.name == "sqlite"
    assert repository.json_stored_as_text is True


@pytest.mark.parametrize("dialect", ["cockroachdb", "postgresql"])
def test_json_stored_as_text_is_false_for_non_sqlite_dialects(dialect, isolation_database):
    # Cualquier motor que no sea SQLite (CockroachDB, PostgreSQL) entrega el JSONB ya decodificado.
    # Base falsa: solo importa `engine.dialect.name`, no se abre ninguna conexion.
    database = SimpleNamespace(engine=SimpleNamespace(dialect=SimpleNamespace(name=dialect)))

    assert JobRepository(database).json_stored_as_text is False


def test_json_stored_as_text_is_true_for_a_fake_sqlite_database(isolation_database):
    # La deteccion depende SOLO del nombre del dialecto, no de la clase de la base.
    database = SimpleNamespace(engine=SimpleNamespace(dialect=SimpleNamespace(name="sqlite")))

    assert JobRepository(database).json_stored_as_text is True


def test_json_stored_as_text_is_read_only(isolation_database):
    # Es un dato derivado del motor: no se puede forzar desde fuera (un `True` impuesto sobre
    # CockroachDB reabriria el defecto de la doble decodificacion).
    database = SimpleNamespace(engine=SimpleNamespace(dialect=SimpleNamespace(name="cockroachdb")))
    repository = JobRepository(database)

    with pytest.raises(AttributeError):
        repository.json_stored_as_text = True
    assert repository.json_stored_as_text is False


# ------------------------------------------------------------------ 2. rechazo de cadenas JSONB


@pytest.mark.parametrize("decoded", JSONB_STRINGS)
def test_decoded_string_is_rejected_when_json_is_not_stored_as_text(guarded, decoded):
    # Una cadena ya decodificada de un JSONB NO es un objeto, aunque su contenido parezca JSON de
    # objeto (`{}`, `{"ok":1}`) o de `null`. Hoy se vuelve a decodificar y se ACEPTA (Red).
    _mark_completed(guarded)
    _use_jsonb(guarded, decoded)
    before = persisted_rows(guarded.database)
    failed_before = ingest_jobs_failed_total._value.get()

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(deepcopy(guarded.job))

    # Rechazo permanente propio, con el mensaje fijo y sin causa ni contexto arrastrados.
    assert type(caught.value) is InvalidJobMessage
    assert str(caught.value) == "Invalid job message."
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
    # El valor guardado no se filtra por texto, `repr` ni traza completa.
    assert MARKER not in str(caught.value)
    assert MARKER not in repr(caught.value)
    assert MARKER not in "".join(traceback.format_exception(caught.value))
    # Se comprobo que la rama ejercitada es la prevista: llego una cadena y no un objeto.
    delivered = guarded.repository.fetched[-1]["result"]
    assert type(delivered) is str and delivered == decoded
    # Solo se consulta el estado; ni transiciones, ni pipeline, ni fila alterada.
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)
    # Rechazar un mensaje no es un fallo de ingesta: el contador no sube.
    assert ingest_jobs_failed_total._value.get() == failed_before


@pytest.mark.parametrize("decoded", [
    pytest.param([1], id="lista"),
    pytest.param([], id="lista-vacia"),
    pytest.param(123, id="numero"),
    pytest.param(0, id="cero"),
    pytest.param(True, id="true"),
    pytest.param(False, id="false"),
])
def test_other_decoded_types_are_still_rejected_when_json_is_not_stored_as_text(guarded, decoded):
    # Guarda: los demas tipos no objeto siguen rechazandose con `False` (los falsy no se
    # confunden con "sin resultado"). Pasa ya hoy.
    _mark_completed(guarded)
    _use_jsonb(guarded, decoded)
    before = persisted_rows(guarded.database)

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(deepcopy(guarded.job))

    assert type(caught.value) is InvalidJobMessage
    assert str(caught.value) == "Invalid job message."
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


# ------------------------------------------------------------------ 3. validos con JSONB decodificado


@pytest.mark.parametrize("decoded, expected", [
    pytest.param({}, {}, id="dict-vacio"),
    pytest.param({"ok": 1}, {"ok": 1}, id="dict-con-claves"),
    pytest.param({"anidado": {"a": [1, 2]}}, {"anidado": {"a": [1, 2]}}, id="dict-anidado"),
    pytest.param(None, {}, id="none-sin-resultado"),
])
def test_decoded_object_or_none_is_accepted_when_json_is_not_stored_as_text(guarded, decoded, expected):
    # El rechazo de cadenas no debe tocar las reentregas legitimas: objeto (tambien el vacio,
    # que es falsy) -> ese objeto; None (SQL NULL o JSONB null) -> `{}`. Pasa ya hoy (guarda).
    _mark_completed(guarded)
    _use_jsonb(guarded, decoded)
    before = persisted_rows(guarded.database)

    result = guarded.task.execute(deepcopy(guarded.job))

    assert result == expected
    assert isinstance(result, dict)
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


# ------------------------------------------------------------------ 4. compatibilidad con SQLite (texto)


@pytest.mark.parametrize("stored_text, expected", [
    pytest.param("{}", {}, id="objeto-vacio"),
    pytest.param('{"ok": 1}', {"ok": 1}, id="objeto"),
    pytest.param("null", {}, id="null"),
])
def test_serialized_text_is_still_decoded_when_json_is_stored_as_text(guarded, stored_text, expected):
    # Con SQLite el objeto se guarda como TEXTO: `{}`, `{"ok": 1}` y `null` siguen siendo
    # resultados validos tras decodificar. Es la otra mitad de la distincion: rechazar todo `str`
    # romperia estas pruebas. Pasa ya hoy (guarda).
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_text)
    _use(guarded, TextStoredRepository(guarded.database))
    before = persisted_rows(guarded.database)

    result = guarded.task.execute(deepcopy(guarded.job))

    assert result == expected
    assert isinstance(result, dict)
    assert type(guarded.repository.fetched[-1]["result"]) is str  # llego como texto
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


def test_default_sqlite_repository_accepts_serialized_object(guarded):
    # Igual que el anterior pero con el repositorio por defecto del caso (sin sobrescribir la
    # propiedad): con el codigo final, `JobRepository` sobre SQLite debe comportarse como texto.
    set_row(guarded.database, guarded.job["id"], status="completed", result='{"ok": 1}')
    before = persisted_rows(guarded.database)

    assert guarded.task.execute(deepcopy(guarded.job)) == {"ok": 1}
    assert_no_effects(guarded, before)


def test_serialized_json_string_is_rejected_when_json_is_stored_as_text(guarded):
    # Una cadena JSON guardada como texto (`"{}"` con comillas) decodifica a la cadena `{}`, que
    # no es un objeto: se rechaza. Distingue "texto que contiene un objeto" de "texto que contiene
    # una cadena". Pasa ya hoy (guarda).
    set_row(guarded.database, guarded.job["id"], status="completed", result='"{}"')
    _use(guarded, TextStoredRepository(guarded.database))
    before = persisted_rows(guarded.database)

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(deepcopy(guarded.job))

    assert type(caught.value) is InvalidJobMessage
    assert str(caught.value) == "Invalid job message."
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


# ------------------------------------------------------------------ 5. doble sin el atributo


def test_repository_without_attribute_is_treated_as_text(guarded):
    # Compatibilidad: un doble que no define `json_stored_as_text` se trata como texto
    # serializado, de modo que `'{"ok": 1}'` se decodifica y se acepta. Pasa ya hoy (guarda del
    # valor por defecto: si el coder usase `False` por defecto, esto fallaria).
    set_row(guarded.database, guarded.job["id"], status="completed", result='{"ok": 1}')
    repository = AttributelessRepository(guarded.database)
    assert not hasattr(repository, "json_stored_as_text")
    _use(guarded, repository)
    before = persisted_rows(guarded.database)

    result = guarded.task.execute(deepcopy(guarded.job))

    assert result == {"ok": 1}
    assert repository.calls == ["fetch_authorized_job"]
    guarded.pipeline.run.assert_not_called()
    assert persisted_rows(guarded.database) == before


# ------------------------------------------------------------------ 6. por el worker


@pytest.mark.parametrize("decoded", [
    pytest.param("{}", id="objeto-vacio-como-cadena"),
    pytest.param('{"ok":1}', id="objeto-como-cadena"),
    pytest.param("null", id="null-como-cadena"),
    pytest.param('{"secreto": "' + MARKER + '"}', id="objeto-con-marcador-como-cadena"),
])
def test_worker_nacks_decoded_string_result_without_requeue(guarded, decoded, capsys, caplog):
    # Extremo a extremo con el worker real: la cadena JSONB se descarta UNA vez con
    # `nack(requeue=False)`, sin relanzar (la llamada devuelve normalmente), sin `ack` y con el
    # evento fijo `job_message_rejected`. Hoy se `ack`-ea como si fuera un resultado valido (Red).
    configure_logging()
    _mark_completed(guarded)
    _use_jsonb(guarded, decoded)
    before = persisted_rows(guarded.database)
    worker = _worker_for(guarded)

    worker._process_message(QueueMessage(deepcopy(guarded.job), delivery_tag=TAG))  # no debe lanzar

    # Un solo diccionario para que el fallo muestre ack y nack a la vez (Red: ack=[call(TAG)], nack=[]).
    assert {"ack": worker.queue.ack.call_args_list, "nack": worker.queue.nack.call_args_list} == {
        "ack": [], "nack": [call(TAG, requeue=False)],
    }
    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert "job_message_rejected" in rendered
    assert "worker_loop_failed" not in rendered
    assert MARKER not in rendered  # el valor guardado no aparece en ninguna salida
    assert_no_effects(guarded, before)


def test_worker_acks_serialized_text_object_when_json_is_stored_as_text(guarded, capsys, caplog):
    # Guarda: con texto serializado (SQLite) la reentrega legitima se confirma con `ack`, sin
    # `nack` ni evento de rechazo. Pasa ya hoy.
    configure_logging()
    set_row(guarded.database, guarded.job["id"], status="completed", result='{"ok": 1}')
    _use(guarded, TextStoredRepository(guarded.database))
    before = persisted_rows(guarded.database)
    worker = _worker_for(guarded)

    worker._process_message(QueueMessage(deepcopy(guarded.job), delivery_tag=TAG))

    worker.queue.ack.assert_called_once_with(TAG)
    worker.queue.nack.assert_not_called()
    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    assert "job_message_rejected" not in rendered
    assert "worker_loop_failed" not in rendered
    assert_no_effects(guarded, before)


@pytest.mark.parametrize("decoded", [
    pytest.param({}, id="dict-vacio"),
    pytest.param({"ok": 1}, id="dict"),
    pytest.param(None, id="none"),
])
def test_worker_acks_decoded_object_or_none_when_json_is_not_stored_as_text(guarded, decoded, capsys, caplog):
    # Guarda: con JSONB decodificado, un objeto (tambien el vacio) o None sigue confirmandose.
    configure_logging()
    _mark_completed(guarded)
    _use_jsonb(guarded, decoded)
    before = persisted_rows(guarded.database)
    worker = _worker_for(guarded)

    worker._process_message(QueueMessage(deepcopy(guarded.job), delivery_tag=TAG))

    worker.queue.ack.assert_called_once_with(TAG)
    worker.queue.nack.assert_not_called()
    captured = capsys.readouterr()
    assert "job_message_rejected" not in captured.out + captured.err + caplog.text
    assert_no_effects(guarded, before)
