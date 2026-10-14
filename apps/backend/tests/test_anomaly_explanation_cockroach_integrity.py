"""JUP-038 (revisión de la PR #128): episodios guardados incoherentes o con operandos no válidos, con CockroachDB REAL.

Qué se valida: si la fila de `anomaly_episodes` es incoherente (operandos NaN/Infinity/enormes/diminutos, impacto
menor que el exceso, contador de días no positivo, fecha de impacto anterior al inicio, cierre sin motivo o
moneda que el explicador no evalúa), `POST /assistant/conversations/{id}/messages` con `anomaly_query` responde
409 `anomaly_explanation_unavailable` y NO guarda ningún mensaje. Se recorre el camino completo por HTTP:
`Database.fetch_anomaly_episode_snapshot` real (que construye el episodio con `rules.episode_payload`, que
redondea con `money()`), explicador de producción y almacén de mensajes.

Por qué con CockroachDB y no con la base doblada en SQLite: las columnas `reference_week_cost`,
`opening_observed_cost` e `impact_numerator` son `DECIMAL` SIN precisión y CockroachDB admite en ellas 'NaN',
'Infinity', '1E+200' y muchos decimales. La lectura puede fallar (p. ej. `InvalidOperation` en `money()`) ANTES
de que el explicador vea los datos, y eso solo se observa con esa columna real: un fallo ahí sería un 500 en vez
del 409 que exigen los revisores.

Restricciones de la tabla que descartan casos (no se incluyen porque no son alcanzables con SQL válido):
- `observation` solo admite 'observed' y 'no_longer_observed' (CHECK), `severity` solo P1/P2/P3 y `status` solo
  new/investigating/resolved/false_positive: no se puede guardar un valor desconocido de esas columnas.
- `rules_version` ya está cubierto por `test_anomaly_explanation_cockroach.py`.

Convención del Red: antes de corromper la fila se exige que una petición equivalente SE ACEPTE (201); sin ese
control, «no se guarda nada» pasaría por vacuidad. Es opt-in: `tenant_cockroach_database` omite todo cuando
`JUP086_COCKROACH_TEST_URL` no está definida (CI).
"""
import pytest
from sqlalchemy import text

from anomaly_episode_support import episode_rows, episode_store, load_series
from billing_support import billing_schema
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_anomaly_explanation_cockroach import UNAVAILABLE, explain, explained, opened_episode, stored_messages
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers


# Cada caso es (identificador legible, sentencia SET fija, parámetros). Los valores DECIMAL se pasan como texto y
# se convierten en SQL con CAST para que CockroachDB los guarde tal cual (incluidos 'NaN' e 'Infinity').
def decimal_case(column, value):
    return pytest.param(f"{column} = CAST(:value AS DECIMAL)", {"value": value}, id=f"{column}={value}")


CORRUPTIONS = [
    # impact_numerator: no finito, negativo, fuera de rango (enorme y diminuto) y menor que el exceso.
    # El episodio real de la fixture tiene exceso 1050 (550 * 7 - 2800), así que «1» es incoherente.
    decimal_case("impact_numerator", "NaN"),
    decimal_case("impact_numerator", "Infinity"),
    decimal_case("impact_numerator", "-5"),
    decimal_case("impact_numerator", "1E+200"),
    decimal_case("impact_numerator", "1E-150"),
    decimal_case("impact_numerator", "1"),
    # reference_week_cost: no finito y fuera de rango.
    decimal_case("reference_week_cost", "NaN"),
    decimal_case("reference_week_cost", "Infinity"),
    decimal_case("reference_week_cost", "1E+200"),
    # opening_observed_cost: no finito.
    decimal_case("opening_observed_cost", "NaN"),
    decimal_case("opening_observed_cost", "Infinity"),
    # Contador de días de impacto no positivo.
    pytest.param("impact_day_count = 0", {}, id="impact_day_count=0"),
    pytest.param("impact_day_count = -1", {}, id="impact_day_count=-1"),
    # La fecha hasta la que se acumula el impacto no puede ser anterior al inicio del episodio.
    pytest.param("impact_through_date = start_date - 1", {}, id="impact_through_date<start_date"),
    # Cierre sin motivo: un episodio resuelto con `closed_at` pero motivo vacío no es coherente con la API de
    # estados (que exige motivo al cerrar). Pasa a «resolved», así que no choca con el índice de seguimiento.
    pytest.param("status = 'resolved', closed_at = now(), closure_reason = ''", {}, id="resolved-sin-motivo"),
    # Moneda que el explicador no evalúa (solo EUR y USD).
    pytest.param("currency = 'JPY'", {}, id="currency=JPY"),
]


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
@pytest.mark.parametrize("assignments, params", CORRUPTIONS)
def test_episodio_guardado_incoherente_da_409_y_no_guarda_mensajes(episode_store, api, assignments, params):
    episode_id = opened_episode(api, episode_store)
    # Control (anti-vacuidad): antes de corromper la fila el MISMO episodio SÍ se explica (201) y deja 2 mensajes.
    explained(api, episode_id)
    assert len(stored_messages(api)) == 2
    [before] = episode_rows(episode_store, "tenant-a")

    # Corrupción con SQL real sobre la única fila; el resto de columnas queda como estaba. `assignments` es una
    # constante de esta prueba (no entrada externa), por eso se compone en la sentencia.
    with episode_store.engine.begin() as connection:
        updated = connection.execute(
            text(f"UPDATE anomaly_episodes SET {assignments} WHERE id = :id"), {"id": episode_id, **params})
    assert updated.rowcount == 1
    [after] = episode_rows(episode_store, "tenant-a")
    # La corrupción cambió algo de verdad (si no, el 409 no demostraría nada).
    assert after != before
    messages_before = rows(api.db, "messages")

    response = explain(api, episode_id)

    # 409 con cuerpo exacto: ni 500 (excepción de lectura sin capturar) ni 201 (explicación inventada).
    assert response.status_code == 409, response.text
    assert response.json() == UNAVAILABLE
    # No se guardó ningún mensaje nuevo: siguen los 2 del control.
    assert rows(api.db, "messages") == messages_before
    assert len(stored_messages(api)) == 2
