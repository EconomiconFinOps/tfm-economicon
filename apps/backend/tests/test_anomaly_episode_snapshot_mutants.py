"""JUP-038 (tarea 3.x, remediación de mutación): marca de datos sintéticos de `fetch_anomaly_episode_snapshot`.

Mutante que matan estas pruebas: sustituir en la consulta
`COALESCE(request->'synthetic' = 'true'::JSONB, false)` por `(request->'synthetic' IS NOT NULL)`.
Con el mutante, cualquier ingesta cuyo `request` tenga la CLAVE `synthetic` (aunque valga `false`, una cadena,
`null` o un número) contaría como sintética y el explicador avisaría de «datos sintéticos de demostración» que no
lo son. Las pruebas existentes solo usaban `true`, así que no distinguían ambas condiciones.

Se ejecutan contra CockroachDB real (mismo patrón y fixtures que `test_anomaly_episode_snapshot.py`).
"""
import json
from datetime import date

import pytest
from sqlalchemy import text

from anomaly_episode_support import episode_store, load_series
from billing_support import billing_schema, insert_run
from tenant_isolation_support import tenant_cockroach_database


TODAY = date(2026, 10, 12)
SPIKE = ["400.00"] * 7 + ["550.00", "400.00"]


def open_episode(db):
    """Carga la serie base, corre la detección y devuelve el id del único episodio abierto de `tenant-a`."""
    load_series(db, SPIKE)
    db.run_anomaly_detection("tenant-a", today=TODAY)
    [item] = db.fetch_anomaly_episodes("tenant-a")
    return item["id"]


def set_request(db, run_id, request_json):
    """Fija el `request` (JSON como texto, parametrizado) de una ingesta por SQL directo."""
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE azure_cost_ingestion_runs SET request = CAST(:request AS JSONB) "
                                "WHERE id = :id"), {"request": request_json, "id": run_id})


def includes_synthetic(db, episode_id):
    return db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["includes_synthetic_data"]


# Valores del campo que NO son el booleano JSON `true`. Con el mutante `IS NOT NULL`, los cinco primeros
# (la clave existe) darían True; los dos últimos (sin clave) también darían False con el mutante, pero fijan que
# la ausencia del campo nunca se interpreta como sintética.
NOT_SYNTHETIC_REQUESTS = [
    '{"synthetic": false}',
    '{"synthetic": "true"}',
    '{"synthetic": null}',
    '{"synthetic": 1}',
    '{"synthetic": "yes"}',
    '{"other": true}',
    '{}',
]


@pytest.mark.parametrize("request_json", NOT_SYNTHETIC_REQUESTS)
def test_snapshot_does_not_flag_a_completed_run_whose_synthetic_field_is_not_boolean_true(
        episode_store, request_json):
    # Mata el mutante `IS NOT NULL`: solo el booleano JSON `true` es sintético. `false`, la CADENA "true", `null`,
    # un número u otra cadena no lo son, y avisar de «datos sintéticos» sin serlo engañaría al usuario.
    db = episode_store
    episode_id = open_episode(db)
    set_request(db, "run-a", request_json)
    assert includes_synthetic(db, episode_id) is False, request_json


def test_snapshot_positive_control_flags_boolean_true(episode_store):
    # Control positivo: sin esta prueba las anteriores podrían pasar aunque el campo diera siempre False.
    # Con el mismo montaje, `{"synthetic": true}` en una ingesta completada sí debe marcar True.
    db = episode_store
    episode_id = open_episode(db)
    set_request(db, "run-a", '{"synthetic": false}')
    assert includes_synthetic(db, episode_id) is False
    set_request(db, "run-a", json.dumps({"synthetic": True}))
    assert includes_synthetic(db, episode_id) is True


def test_snapshot_flags_when_any_completed_run_is_synthetic_even_if_another_is_not(episode_store):
    # Caso mixto: una ingesta con `synthetic: false` y otra con `synthetic: true`, ambas completadas del mismo
    # cliente. Basta una sintética para avisar (EXISTS); la no sintética no debe anularla.
    db = episode_store
    episode_id = open_episode(db)
    with db.engine.begin() as connection:
        insert_run(connection, "run-extra")
    set_request(db, "run-a", '{"synthetic": false}')
    set_request(db, "run-extra", '{"synthetic": true}')
    assert includes_synthetic(db, episode_id) is True
