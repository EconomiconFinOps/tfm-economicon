"""JUP-113 (RF-086-004): la admision de `POST /jobs/ingest` aplica la misma regla de `source` que el processor.

Hasta ahora el backend solo rechazaba un `source` vacio; un valor como
`Azure Cost Management` daba 202 y fallaba siempre despues en el processor
(`normalize_source`). La regla compartida (normalizar con `strip().lower()` y exigir
`^[a-z0-9][a-z0-9._-]{0,63}$` con fullmatch) vive como tabla de casos en
`docs/api/ingest-source-contract-cases.json`; el processor recorre la MISMA tabla en
`apps/processor/tests/test_ingest_source_contract.py`, de modo que ambos servicios no
pueden discrepar sin que falle una de las dos pruebas.

Ruta real, autenticacion y SQLite reales; solo la cola es doble (fixture `api`).
"""
import json
from pathlib import Path

import pytest

from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers, no_effects

# Raiz del repo calculada desde este archivo (apps/backend/tests/<archivo>): no depende del cwd.
CASES_PATH = Path(__file__).resolve().parents[3] / "docs" / "api" / "ingest-source-contract-cases.json"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))

SQLITE = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
REJECTION = {"detail": [{"type": "validation_error", "msg": "Invalid request value"}]}


def body(source):
    return {"tenant_id": "tenant-a", "source": source, "text_content": "ok"}


def visible_forms(source):
    # Formas en que el valor podria filtrarse: crudo, recortado y escapado como JSON
    # (con y sin ASCII forzado), porque un registro estructurado lo escaparia.
    forms = {source, source.strip(), json.dumps(source)[1:-1], json.dumps(source, ensure_ascii=False)[1:-1]}
    return {form for form in forms if form.strip()}


@SQLITE
@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES["rejected"]])
def test_ingest_rejects_source_the_processor_would_refuse(api, case, capsys, caplog):
    # Cada origen que el processor rechazaria debe cortarse en la admision con 422 y el
    # cuerpo cerrado genérico: sin job, sin reserva en la cola, sin publicacion y sin
    # eco del valor (ni en la respuesta ni en los registros). `empty` y `whitespace-only`
    # ya se rechazaban antes del change, asi que pasan tambien en Red.
    source = case["source"]
    jobs_before = rows(api.db, "jobs")

    response = call(api, "POST", "/jobs/ingest", headers=headers(), json=body(source))

    assert response.status_code == 422, response.text
    assert response.json() == REJECTION
    no_effects(api)
    assert rows(api.db, "jobs") == jobs_before
    captured = capsys.readouterr()
    visible = response.text + captured.out + captured.err + caplog.text
    # Valores vacios o solo espacios no son distintivos: no se pueden buscar como texto.
    for form in visible_forms(source):
        assert form not in visible


@SQLITE
@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES["accepted"]])
def test_ingest_accepts_valid_source_and_stores_it_verbatim(api, case):
    # Un origen valido se admite con 202 y se guarda y publica TAL COMO SE ENVIO: la
    # normalizacion (minusculas, recorte) solo sirve para decidir, no reescribe el valor
    # (el processor vuelve a normalizar por su cuenta). Cubre bordes de 64 caracteres,
    # relleno con tabulador/salto/NBSP y mayusculas.
    source = case["source"]

    response = call(api, "POST", "/jobs/ingest", headers=headers(), json=body(source))

    assert response.status_code == 202, response.text
    [job] = rows(api.db, "jobs")
    assert job["id"] == response.json()["job_id"]
    assert job["source"] == source
    assert json.loads(job["payload"])["source"] == source
    api.queue.publish.assert_called_once()
    published = api.queue.publish.call_args.args[0]
    assert published["id"] == job["id"]
    assert published["source"] == source
    assert published["payload"]["source"] == source


def test_contract_table_guard_keeps_the_boundary_cases():
    # Guardian de la tabla compartida: si alguien la vacia o le quita los limites, las
    # pruebas parametrizadas pasarian en vacio. Se exige contenido minimo y ids unicos.
    accepted, rejected = CASES["accepted"], CASES["rejected"]
    assert accepted and rejected
    ids = [c["id"] for c in accepted + rejected]
    assert len(ids) == len(set(ids))
    accepted_sources = {c["source"] for c in accepted}
    rejected_sources = {c["source"] for c in rejected}
    assert any(len(s) == 64 and s == s.strip() for s in accepted_sources)
    assert any(len(s) == 65 and s == s.strip() for s in rejected_sources)
    assert "Azure Cost Management" in rejected_sources
    # Ningun valor puede estar a la vez en ambas listas.
    assert not accepted_sources & rejected_sources
