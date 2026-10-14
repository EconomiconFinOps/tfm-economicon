"""JUP-038 (segunda ronda de la revisión de la PR #128): la ruta del asistente ante operandos con demasiados decimales.

Qué se valida: `POST /assistant/conversations/{id}/messages` con `anomaly_query` debe responder
`409 {"detail":{"code":"anomaly_explanation_unavailable"}}` y NO guardar ningún mensaje cuando un operando guardado
tiene más de 12 decimales. Los casos extremos importan porque hoy `Decimal("1e-999999")` hace saltar
`decimal.Overflow` (no capturado: un 500) y `Decimal("1e-150")` hace saltar `decimal.InvalidOperation` que solo
absorbe una red de seguridad; con 13 decimales o `1e-13` hoy la explicación sale como "ok" (201).

Mismo montaje que `test_anomaly_explanation_integrity_api.py`: SQLite real para usuarios, conversaciones y mensajes,
y un DOBLE solo en la lectura de episodios (`fetch_anomaly_episode_snapshot`, que SQLite no tiene). El explicador es
el de producción: lo que se prueba es que la excepción correcta llega a la ruta y se traduce a 409.

Las tripletas son coherentes entre sí (cumplen la regla de apertura y numerador >= exceso): el único motivo posible
del 409 son los decimales. Con R~0 y O=550.00 el exceso es ~3850.00, cubierto por el numerador 3850.00; con
R=2800.00 y O=550.00 el exceso es 1050.00.
"""
from decimal import Decimal

import pytest

# Los fixtures `tenant_database`, `populated_database`, `main_module`, `resource_mocks`, `restore_logging` y `api`
# se importan por nombre (como en `test_anomaly_explanation_integrity_api.py`) para que pytest los resuelva aquí.
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database  # noqa: F401
from test_anomaly_explanation_api import PATH, UNAVAILABLE, anomaly_body, queries, stub_store
from test_anomaly_explanations import make_snapshot
from test_secret_boundaries import main_module, resource_mocks, restore_logging  # noqa: F401
from test_tenant_isolation_api import api, call, headers  # noqa: F401


def with_operands(reference, observed, numerator):
    """Fotografía válida con los tres operandos sobrescritos tal cual (sin pasar por `make_snapshot`)."""
    snapshot = make_snapshot()
    snapshot["operands"] = {"reference_week_cost": reference, "opening_observed_cost": observed,
                            "impact_numerator": numerator}
    return snapshot


# Cada caso lleva un único operando con más de 12 decimales y los otros dos coherentes, para que solo la escala
# pueda causar el rechazo. La referencia admite cualquier escala; observado y numerador no pueden ser diminutos
# (deben ser >= 100 por día y >= el exceso), así que se prueban con 13 decimales.
TOO_MANY_DECIMALS = [
    pytest.param(lambda: with_operands(Decimal("1e-13"), Decimal("550.00"), Decimal("3850.00")), id="referencia-1e-13"),
    pytest.param(lambda: with_operands(Decimal("2800.0000000000001"), Decimal("550.00"), Decimal("3850.00")),
                 id="referencia-13-decimales"),
    pytest.param(lambda: with_operands(Decimal("1e-150"), Decimal("550.00"), Decimal("3850.00")), id="referencia-1e-150"),
    # Overflow sin capturar hoy: sin la validación de escala sería un 500.
    pytest.param(lambda: with_operands(Decimal("1e-999999"), Decimal("550.00"), Decimal("3850.00")),
                 id="referencia-1e-999999"),
    pytest.param(lambda: with_operands(Decimal("2800.00"), Decimal("550.0000000000001"), Decimal("2800.00")),
                 id="observado-13-decimales"),
    pytest.param(lambda: with_operands(Decimal("2800.00"), Decimal("550.00"), Decimal("2800.0000000000001")),
                 id="numerador-13-decimales"),
]


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("build", TOO_MANY_DECIMALS)
def test_operando_con_mas_de_12_decimales_da_409_sin_guardar_ningun_mensaje(api, monkeypatch, build):
    # Control previo: la misma petición con una fotografía válida SÍ da 201, así que el 409 de abajo no se debe a
    # un 422 del cuerpo ni a un montaje roto, sino a la fotografía con escala de más que se sirve después.
    stub_store(api, monkeypatch)
    control = call(api, "POST", PATH, headers=headers(), json=anomaly_body())
    assert control.status_code == 201, control.text
    double = stub_store(api, monkeypatch, build())
    before, counter = rows(api.db, "messages"), queries()
    appended = api.spies["append_message"].call_count

    response = call(api, "POST", PATH, headers=headers(), json=anomaly_body())

    # 409 con el cuerpo EXACTO del contrato (no un 500 por Overflow ni un 201 con evidencia "ok").
    assert response.status_code == 409, response.text
    assert response.json() == UNAVAILABLE
    # La fotografía SÍ llegó al explicador (se leyó una vez) y no se guardó nada: ni el mensaje del usuario ni el
    # del asistente (el segundo es el que cuenta la métrica).
    assert double.call_count == 1
    assert api.spies["append_message"].call_count == appended
    assert rows(api.db, "messages") == before
    assert queries() == counter
    api.vector.search_chunks.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("build", [
    pytest.param(lambda: with_operands(Decimal("2800.000000000001"), Decimal("550.000000000001"),
                                       Decimal("2800.000000000001")), id="tres-operandos-12-decimales"),
    pytest.param(lambda: with_operands(Decimal("1e-12"), Decimal("550.00"), Decimal("3850.00")),
                 id="referencia-1e-12"),
])
def test_control_operandos_con_exactamente_12_decimales_siguen_dando_201(api, monkeypatch, build):
    # Frontera: 12 decimales (la escala con la que la tabla guarda los importes) NO se rechaza; evita una
    # validación de escala con un error de uno que devolviera 409 a datos reales. Se comprueba además que se
    # guardan los dos mensajes y que la métrica sube, como en un flujo correcto.
    stub_store(api, monkeypatch, build())
    before, counter = rows(api.db, "messages"), queries()
    response = call(api, "POST", PATH, headers=headers(), json=anomaly_body())
    assert response.status_code == 201, response.text
    assert response.json()["assistant_message"]["metadata"]["anomaly_evidence"]["status"] == "ok"
    assert len(rows(api.db, "messages")) == len(before) + 2
    assert queries() == counter + 1
