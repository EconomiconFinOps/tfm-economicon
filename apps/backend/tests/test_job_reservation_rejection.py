"""JUP-054 (hueco H-04): ramas de `POST /jobs/ingest` no cubiertas offline.

* Reserva rechazada (`reserve()` -> `outcome == "not_sent"`): 503 inmediato,
  ANTES de crear el trabajo.
* Resultado de publicacion fuera de contrato: `RuntimeError` interno que no debe
  filtrar el valor invalido ni dejar el trabajo aceptado.

`test_job_publication.py` ya cubre los resultados `not_sent`/`rejected`/`unknown`
que llegan por `queue.publish` y el fallo de finalizacion SQL; aqui no se repiten.
Ruta real, autenticacion y pertenencia reales, SQLite real; solo la cola es doble.
"""
import json
from types import SimpleNamespace

import pytest

from app.core.metrics import ingest_jobs_total
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_job_publication import BODY, DETAIL, OutcomeDouble, PublicationQueue, post, set_queue
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers

SQLITE = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
REJECTION = {"detail": DETAIL, "code": "publish_not_sent", "job_id": None, "retryable": False}


def rejecting_queue(api):
    # Reserva rechazada: un objeto con `outcome == "not_sent"` (como PublishResult real).
    queue = set_queue(api, PublicationQueue())
    queue.reserve.return_value = SimpleNamespace(outcome="not_sent", code="capacity")
    return queue


def assert_no_effects(api, queue, jobs_before):
    # El rechazo ocurre antes de tocar la base y de publicar: nada se escribe ni se envia.
    assert rows(api.db, "jobs") == jobs_before
    api.spies["create_job"].assert_not_called()
    queue.publish.assert_not_called()


@SQLITE
@pytest.mark.parametrize("user,tenant", [("alice", "tenant-a"), ("multi", "tenant-b")])
def test_rejected_reservation_is_503_before_creating_the_job(api, user, tenant, monkeypatch):
    # not_sent en la reserva: 503 con cuerpo cerrado (sin job_id ni publication_outcome),
    # sin efectos y sin tocar la metrica de trabajos aceptados. Con el usuario
    # multi-tenant sobre tenant-b el comportamiento es el mismo y no escribe en ninguno.
    queue = rejecting_queue(api)
    finalize = []
    monkeypatch.setattr(api.db, "finalize_job_publication", lambda *a, **k: finalize.append(a), raising=False)
    jobs_before, counter = rows(api.db, "jobs"), ingest_jobs_total._value.get()

    response = call(api, "POST", "/jobs/ingest", headers=headers(user, tenant),
                    json={**BODY, "tenant_id": tenant})

    assert response.status_code == 503
    assert response.json() == REJECTION
    assert "retry-after" not in response.headers
    assert "private-body-marker" not in response.text
    assert queue.reserve.call_count == 1
    assert_no_effects(api, queue, jobs_before)
    assert finalize == [] and ingest_jobs_total._value.get() == counter
    # No se asierta `cancel`: una reserva `not_sent` no registra ticket alguno, asi que no hay
    # nada que liberar y cancelar seria inocuo (asertarlo ataria el test a la implementacion).


@SQLITE
@pytest.mark.parametrize("reservation", [object(), SimpleNamespace(outcome="reserved"),
                                         SimpleNamespace(outcome="rejected"), SimpleNamespace(outcome="unknown"),
                                         SimpleNamespace(outcome="NOT_SENT")])
def test_only_not_sent_reservations_are_rejected(api, reservation):
    # Control positivo: solo la cadena exacta "not_sent" corta la ruta. Una reserva sin
    # atributo `outcome`, con otro valor (incluidos rejected/unknown, que son resultados
    # de publicacion, no de reserva) o con otra capitalizacion sigue el flujo normal.
    queue = set_queue(api, PublicationQueue())
    queue.reserve.return_value = reservation
    jobs_before, before = rows(api.db, "jobs"), ingest_jobs_total._value.get()

    response = post(api)

    assert response.status_code == 202, response.text
    [job] = [row for row in rows(api.db, "jobs") if row not in jobs_before]
    assert response.json() == {"job_id": job["id"], "status": "queued", "queue": queue.queue_name}
    assert job["status"] == "queued"
    assert queue.publish.call_count == 1
    assert queue.publish.call_args.kwargs["reservation"] is reservation
    queue.cancel.assert_called_once_with(reservation)
    assert ingest_jobs_total._value.get() == before + 1


@SQLITE
@pytest.mark.parametrize("invalid", ["bogus", "", None, "CONFIRMED", "Confirmed", 7, "leak-marker"])
def test_out_of_contract_publication_outcome_is_generic_500_and_never_accepted(api, invalid, monkeypatch,
                                                                              capsys, caplog):
    # Un `outcome` fuera de {confirmed, not_sent, rejected, unknown} (comparacion exacta:
    # sin normalizar mayusculas ni vacios) es un fallo interno: 500 generico sin el valor,
    # sin finalizar la publicacion, con la reserva cancelada una vez y sin contarse como
    # trabajo aceptado.
    queue = set_queue(api, PublicationQueue())
    queue.publish.return_value = OutcomeDouble(invalid, "leak-marker-code")
    finalize = []
    monkeypatch.setattr(api.db, "finalize_job_publication", lambda *a, **k: finalize.append(a), raising=False)
    jobs_before, counter = rows(api.db, "jobs"), ingest_jobs_total._value.get()

    response = post(api)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    captured = capsys.readouterr()
    visible = response.text + captured.out + captured.err + caplog.text
    # Subcadenas distintivas: el valor invalido no aparece en respuesta, cabeceras ni logs.
    headers_text = " ".join(f"{k}: {v}" for k, v in response.headers.items())
    for marker in ("leak-marker", "bogus", "CONFIRMED", "Confirmed"):
        assert marker not in visible + headers_text
    # Valores no distintivos ("", None, 7): no se detectan por texto. Se comprueba que todo lo
    # escrito en stdout/stderr es JSON (un `print` rompe el parseo), que ninguna CLAVE de
    # registro menciona `outcome`/`publication` y que la excepcion se registra solo por su tipo.
    # Superviviente conocido: un valor no distintivo en una cabecera o en un registro/`print`
    # que sea JSON valido sin esas claves no es observable sin fijar el conjunto exacto de
    # cabeceras/eventos; se prefiere no fijarlo para no atar el test a cambios legitimos del
    # middleware (nuevas cabeceras, eventos u otros loggers).
    records = [json.loads(line) for line in (captured.out + captured.err).splitlines() if line.strip()]
    assert all(isinstance(record, dict) for record in records)
    assert not [key for record in records for key in record if "outcome" in key or "publication" in key]
    [failure] = [r for r in records if r.get("event") == "http_request_failed" and r.get("logger") == "access"]
    assert failure["exception_type"] == "RuntimeError"
    assert finalize == []
    queue.cancel.assert_called_once_with(queue.reserve.return_value)
    assert ingest_jobs_total._value.get() == counter
    # El trabajo se crea antes de publicar y nunca queda aceptado (`queued`) ni con
    # el valor invalido como diagnostico persistido. El estado concreto es incidental.
    [created] = [row for row in rows(api.db, "jobs") if row not in jobs_before]
    assert created["status"] != "queued"
    # Tampoco se persiste el valor invalido (ni uno no distintivo como "bogus" o 7) como diagnostico.
    assert "leak-marker" not in json.dumps(created, default=str)
    if invalid != "":
        assert str(invalid) not in str(created["result"])
    assert queue.publish.call_count == 1
