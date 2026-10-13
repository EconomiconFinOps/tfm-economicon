"""JUP-054 (H-07): reentrega idempotente y payload persistido corrupto en IngestTask.

Se usan SQLite aislada (fixture `isolation_database`), el `JobRepository` real y el
`IngestTask` real. Los dobles solo estan en las fronteras: el proveedor del agente
y el sumidero vectorial (como en `test_agent_ingestion_integration.py`).

Casos que NO se repiten aqui porque ya los cubren otros archivos:
- exito/fallo del primer procesamiento: test_agent_ingestion_integration.py;
- rechazos de alcance/identidad sobre trabajos en cola y la reentrega de un
  completado con miembro revocado: test_tenant_isolation_jobs.py / test_ingest_task.py.

Lo que si cubre este archivo son dos ramas que ninguna prueba ejecutaba:
- reentrega de un trabajo `completed`: devuelve el resultado guardado sin
  reejecutar el pipeline ni tocar el estado (una reentrega del broker no puede
  duplicar efectos);
- `payload` persistido que no es un JSON valido (o no es un objeto): rechazo
  permanente `InvalidJobMessage` que no cambia el estado persistido.
"""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from app.agents.service import AgentRuntime
from app.core.config import Settings
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask, InvalidJobMessage
from tenant_isolation_support import isolation_database, seed_job, snapshot
from test_agent_ingestion_integration import provider_response

# Solo SQLite: CockroachDB no es un servicio disponible offline y un skip no es valido.
pytestmark = pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)

MUTATING_CALLS = {"mark_running", "mark_completed", "mark_failed"}


class RecordingRepository(JobRepository):
    """Repositorio REAL que ademas anota que operaciones se invocan.

    `decode_result=True` emula al controlador de CockroachDB, que entrega las
    columnas JSONB ya deserializadas (dict). SQLite las entrega como texto, de modo
    que sin este adaptador la rama "resultado ya dict" no se podria ejercitar.
    """

    def __init__(self, database, *, decode_result=False):
        super().__init__(database)
        self.decode_result = decode_result
        self.calls = []
        self.fetched = []

    def fetch_authorized_job(self, job_id, *, tenant_id, created_by):
        self.calls.append("fetch_authorized_job")
        stored = super().fetch_authorized_job(job_id, tenant_id=tenant_id, created_by=created_by)
        if stored is not None and self.decode_result and isinstance(stored["result"], str):
            stored = {**stored, "result": json.loads(stored["result"])}
        self.fetched.append(stored)
        return stored

    def mark_running(self, job_id, **scope):
        self.calls.append("mark_running")
        return super().mark_running(job_id, **scope)

    def mark_completed(self, job_id, result, **scope):
        self.calls.append("mark_completed")
        return super().mark_completed(job_id, result, **scope)

    def mark_failed(self, job_id, error_message, **scope):
        self.calls.append("mark_failed")
        return super().mark_failed(job_id, error_message, **scope)


def set_row(database, job_id, **columns):
    """Fija columnas de la fila sembrada por SQL, saltandose el repositorio a proposito."""
    assignments = ", ".join(f"{name}=:{name}" for name in columns)
    with database.engine.begin() as connection:
        connection.execute(text(f"UPDATE jobs SET {assignments} WHERE id=:job_id"), {**columns, "job_id": job_id})


def persisted_rows(database):
    return snapshot(database, "jobs")[0]


@pytest.fixture
def redelivery(isolation_database):
    database = isolation_database
    job = seed_job(database, identifier="jup054-redelivery-job")
    # Contenido largo para que el troceado produzca varios chunks y el sumidero
    # vectorial reciba trabajo real que NO debe repetirse en la reentrega.
    job["payload"]["text_content"] = (
        "Synthetic Azure cost report. Its content spans multiple chunks so that "
        "a redelivery would visibly duplicate embeddings if it re-ran the pipeline."
    )
    # "report" es una fuente fuera del alcance Azure y el agente no consultaria al
    # proveedor; se usa una fuente soportada para que el primer procesamiento sea completo.
    job["source"] = job["payload"]["source"] = "azure-cost"
    set_row(database, job["id"], source=job["source"], payload=json.dumps(job["payload"]))

    provider = MagicMock(spec_set=["invoke"])
    provider.invoke.side_effect = lambda prompt, *, response_format: json.dumps(provider_response())
    vector = MagicMock(spec_set=["store_document"])
    vector.store_document.side_effect = lambda **payload: {
        "document_id": payload["job_id"],
        "chunk_count": len(payload["chunks"]),
        "embedding_count": len(payload["embeddings"]),
        "vector_store": "test-double",
        "provider": payload["provider_name"],
    }
    embeddings = MagicMock(wraps=MockEmbeddingProvider(8))
    embeddings.name = "mock"
    settings = Settings(_env_file=None, llm_provider="mock", litellm_api_key="jup054-synthetic-injected-provider-key")
    pipeline = PipelineRunner(AgentRuntime(settings, provider=provider), TextChunker(48, 8), embeddings, vector)
    repository = RecordingRepository(database)
    return SimpleNamespace(
        database=database, job=job, provider=provider, vector=vector, embeddings=embeddings,
        pipeline=pipeline, repository=repository, task=IngestTask(repository, pipeline),
    )


@pytest.fixture
def guarded(isolation_database):
    """Trabajo sembrado con un pipeline que, si se ejecutara, haria fallar la prueba."""
    job = seed_job(isolation_database, identifier="jup054-guarded-job")
    pipeline = MagicMock()
    pipeline.run.side_effect = AssertionError("el pipeline no debe ejecutarse")
    repository = RecordingRepository(isolation_database)
    return SimpleNamespace(
        database=isolation_database, job=job, pipeline=pipeline, repository=repository,
        task=IngestTask(repository, pipeline),
    )


def assert_no_effects(case, before):
    # Contrato comun de un rechazo o una reentrega: ni pipeline, ni cambios de estado,
    # ni fila alterada (incluido `updated_at`).
    case.pipeline.run.assert_not_called()
    assert MUTATING_CALLS.isdisjoint(case.repository.calls)
    assert persisted_rows(case.database) == before


def test_redelivery_after_real_processing_returns_same_result_without_repeating_effects(redelivery):
    # Primer procesamiento real: el trabajo pasa a completed y escribe vectores una vez.
    first = redelivery.task.execute(redelivery.job)
    [after_first] = persisted_rows(redelivery.database)
    assert after_first["status"] == "completed"
    assert json.loads(after_first["result"]) == first
    provider_calls = redelivery.provider.invoke.call_count
    embed_calls = redelivery.embeddings.embed.call_count
    assert (provider_calls, redelivery.vector.store_document.call_count) == (1, 1)
    assert embed_calls > 1
    before = persisted_rows(redelivery.database)
    redelivery.repository.calls.clear()

    # El broker reentrega EXACTAMENTE el mismo mensaje (copia, como llega por la cola).
    second = redelivery.task.execute(deepcopy(redelivery.job))

    assert second == first
    # Solo se consulta el estado: ninguna transicion running/completed/failed.
    assert redelivery.repository.calls == ["fetch_authorized_job"]
    # Sin efectos repetidos: ni proveedor, ni embeddings, ni escritura vectorial.
    assert redelivery.provider.invoke.call_count == provider_calls
    assert redelivery.embeddings.embed.call_count == embed_calls
    assert redelivery.vector.store_document.call_count == 1
    assert persisted_rows(redelivery.database) == before


def test_repeated_redeliveries_stay_idempotent(redelivery):
    first = redelivery.task.execute(redelivery.job)
    before = persisted_rows(redelivery.database)

    # Varias reentregas seguidas (reintentos del broker) no acumulan efectos.
    results = [redelivery.task.execute(deepcopy(redelivery.job)) for _ in range(3)]

    assert results == [first, first, first]
    assert redelivery.provider.invoke.call_count == 1
    assert redelivery.vector.store_document.call_count == 1
    assert persisted_rows(redelivery.database) == before


@pytest.mark.parametrize(
    "stored_result, decode_result, expected",
    [
        pytest.param('{"summary": "guardado", "chunks": 2}', False, {"summary": "guardado", "chunks": 2}, id="string-json"),
        pytest.param('{"summary": "guardado", "chunks": 2}', True, {"summary": "guardado", "chunks": 2}, id="dict-ya-deserializado"),
        pytest.param("{}", False, {}, id="string-objeto-vacio"),
        pytest.param("{}", True, {}, id="dict-vacio"),
        pytest.param(None, False, {}, id="null-sin-resultado"),
    ],
)
def test_completed_redelivery_returns_stored_result_in_any_representation(
    guarded, stored_result, decode_result, expected
):
    # El resultado almacenado puede llegar como texto (SQLite), como dict (JSONB
    # de CockroachDB) o ser NULL; en todos los casos la salida es un dict utilizable.
    set_row(guarded.database, guarded.job["id"], status="completed", result=stored_result)
    guarded.repository.decode_result = decode_result
    before = persisted_rows(guarded.database)

    result = guarded.task.execute(deepcopy(guarded.job))

    assert result == expected
    assert isinstance(result, dict)
    # Comprueba que la rama ejercitada es la prevista: dict entregado vs. texto entregado.
    delivered = guarded.repository.fetched[-1]["result"]
    if stored_result is None:
        assert delivered is None
    elif decode_result:
        assert isinstance(delivered, dict)
    else:
        assert isinstance(delivered, str)
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


def test_completed_redelivery_ignores_payload_serialization_differences(guarded):
    # La comparacion se hace sobre el objeto deserializado: reordenar claves o cambiar
    # espacios en el JSON persistido no debe convertir una reentrega legitima en rechazo.
    set_row(
        guarded.database, guarded.job["id"], status="completed",
        result='{"stored": "ok"}',
        payload=json.dumps(guarded.job["payload"], indent=4, sort_keys=True),
    )
    before = persisted_rows(guarded.database)

    assert guarded.task.execute(deepcopy(guarded.job)) == {"stored": "ok"}
    assert_no_effects(guarded, before)


def tamper(job, attack):
    """Altera el mensaje reentregado; devuelve el mensaje modificado."""
    job = deepcopy(job)
    if attack == "text_content":
        job["payload"]["text_content"] = "Contenido distinto del persistido"
    elif attack == "metadata":
        job["payload"]["metadata"] = {"title": "Otro titulo"}
    elif attack == "payload-sin-metadata":
        del job["payload"]["metadata"]
    elif attack == "source-ambos":
        job["source"] = job["payload"]["source"] = "otro-source"
    elif attack == "source-solo-envoltorio":
        job["source"] = "otro-source"
    elif attack == "artifact-ambos":
        job["artifact_uri"] = job["payload"]["artifact_uri"] = "corpus://otro-artefacto"
    elif attack == "artifact-solo-envoltorio":
        job["artifact_uri"] = "corpus://otro-artefacto"
    elif attack == "artifact-ausente":
        job["artifact_uri"] = job["payload"]["artifact_uri"] = None
    elif attack == "tenant-ambos":
        job["tenant_id"] = job["payload"]["tenant_id"] = "tenant-b"
    elif attack == "creador-ajeno":
        job["created_by"] = "bob"
    elif attack == "creador-miembro-del-mismo-tenant":
        job["created_by"] = "carol"
    elif attack == "id-ajeno":
        job["id"] = "jup054-otro-job"
    return job


@pytest.mark.parametrize(
    "attack",
    [
        "text_content", "metadata", "payload-sin-metadata", "source-ambos",
        "source-solo-envoltorio", "artifact-ambos", "artifact-solo-envoltorio",
        "artifact-ausente", "tenant-ambos", "creador-ajeno",
        "creador-miembro-del-mismo-tenant", "id-ajeno",
    ],
)
def test_completed_job_is_not_a_shortcut_around_message_validation(guarded, attack):
    # Hay otros usuarios/trabajos reales para que el rechazo no dependa de que la
    # identidad alternativa "no exista", sino de la validacion de alcance.
    seed_job(guarded.database, identifier="jup054-foreign-b", tenant="tenant-b", creator="bob")
    seed_job(guarded.database, identifier="jup054-otro-job", tenant="tenant-a", creator="alice")
    seed_job(guarded.database, identifier="jup054-carol-job", tenant="tenant-a", creator="carol")
    set_row(guarded.database, guarded.job["id"], status="completed", result='{"secreto": "resultado-guardado"}')
    before = persisted_rows(guarded.database)
    message = tamper(guarded.job, attack)

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(message)

    # El rechazo no filtra el resultado almacenado ni detalles del trabajo.
    assert str(caught.value) == "Invalid job message."
    assert "resultado-guardado" not in repr(caught.value)
    assert_no_effects(guarded, before)


@pytest.mark.parametrize("status", ["queued", "completed", "failed"])
@pytest.mark.parametrize(
    "corrupt_payload",
    ["{no es json", "", "   ", '{"text_content": "truncado', "texto suelto", "{'comillas': 'simples'}"],
)
def test_persisted_payload_that_is_not_valid_json_is_rejected_without_state_change(guarded, status, corrupt_payload):
    set_row(guarded.database, guarded.job["id"], status=status, payload=corrupt_payload)
    before = persisted_rows(guarded.database)

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(deepcopy(guarded.job))

    # Es el rechazo permanente propio, no el JSONDecodeError (que tambien es ValueError)
    # ni un error generico que el worker pudiera reintentar.
    assert type(caught.value) is InvalidJobMessage
    assert str(caught.value) == "Invalid job message."
    # `from None`: no se arrastra la causa ni el contexto con fragmentos del payload.
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)


@pytest.mark.parametrize("status", ["queued", "completed"])
@pytest.mark.parametrize(
    "non_object_payload",
    ["[]", '["text_content"]', "null", '"texto"', "123", "true"],
)
def test_persisted_payload_that_is_valid_json_but_not_an_object_is_rejected(guarded, status, non_object_payload):
    # JSON valido pero no objeto: la decodificacion tiene exito y debe rechazarlo la
    # validacion estructural. (SQLite puede convertir "123"/"true" a entero por la
    # afinidad de la columna JSONB; el resultado esperado es el mismo rechazo.)
    set_row(guarded.database, guarded.job["id"], status=status, payload=non_object_payload,
            result='{"secreto": "resultado-guardado"}')
    before = persisted_rows(guarded.database)

    with pytest.raises(InvalidJobMessage) as caught:
        guarded.task.execute(deepcopy(guarded.job))

    assert type(caught.value) is InvalidJobMessage
    assert "resultado-guardado" not in repr(caught.value)
    assert guarded.repository.calls == ["fetch_authorized_job"]
    assert_no_effects(guarded, before)
