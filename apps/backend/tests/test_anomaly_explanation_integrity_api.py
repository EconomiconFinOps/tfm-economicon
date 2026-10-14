"""JUP-038 (cambios pedidos en la revisión de la PR #128): la ruta del asistente ante datos guardados incoherentes.

Qué se valida: `POST /assistant/conversations/{id}/messages` con `anomaly_query` debe responder
`409 {"detail":{"code":"anomaly_explanation_unavailable"}}` y NO guardar ningún mensaje cuando la fotografía del
episodio tiene datos que no pueden ser de un episodio real (observación desconocida, moneda no evaluada, impacto
menor que el exceso del día de apertura, días no válidos, cierre sin motivo, operandos no finitos o fuera de
rango). Hoy esos casos devuelven 201 con una explicación "ok" o un 500 por `decimal.InvalidOperation`.

Se usa el mismo montaje que `test_anomaly_explanation_api.py`: SQLite real para usuarios, conversaciones y
mensajes, y un DOBLE solo en la lectura de episodios (`fetch_anomaly_episode_snapshot`, que SQLite no tiene).
El explicador es el de producción: lo que se prueba es la traducción de `ExplanationUnavailable` a 409.

Como en el resto de pruebas de fallo, cada caso comprueba que el doble SÍ se llamó (la fotografía llegó al
explicador) y que no se guardó nada: ni filas en `messages`, ni llamadas a `append_message`, ni sube la
métrica `assistant_queries_total`.
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

# Los fixtures `tenant_database`, `populated_database`, `main_module`, `resource_mocks`, `restore_logging` y `api`
# se importan por nombre (como en `test_anomaly_explanation_api.py`) para que pytest los resuelva en este módulo.
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database  # noqa: F401
from test_anomaly_explanation_api import PATH, UNAVAILABLE, anomaly_body, queries, stored_messages, stub_store
from test_anomaly_explanations import OPENED, make_snapshot
from test_secret_boundaries import main_module, resource_mocks, restore_logging  # noqa: F401
from test_tenant_isolation_api import api, call, headers  # noqa: F401

CLOSED_AT = datetime(2026, 9, 21, 2, 30, tzinfo=timezone.utc)


def corrupt(**episode_changes):
    """Fotografía válida con campos del episodio sobrescritos tal cual, sin pasar por `episode_payload`."""
    snapshot = make_snapshot()
    snapshot["episode"].update(episode_changes)
    return snapshot


def with_numerator(value):
    snapshot = make_snapshot()
    snapshot["operands"]["impact_numerator"] = value
    return snapshot


def with_operand(name, value):
    snapshot = make_snapshot()
    snapshot["operands"][name] = value
    return snapshot


def with_operands(reference, observed, numerator):
    snapshot = make_snapshot()
    snapshot["operands"] = {"reference_week_cost": reference, "opening_observed_cost": observed,
                            "impact_numerator": numerator}
    return snapshot


def closed_without_reason(reason):
    snapshot = make_snapshot(status="resolved", closed_at=CLOSED_AT,
                             closure_reason="Hecho")
    snapshot["episode"]["closure_reason"] = reason
    return snapshot


# Cada caso es una categoría de incoherencia de la spec. Con R=2800.00 y O=550.00 el exceso de apertura es
# 1050.00: un numerador menor no puede ser de un episodio real.
INCOHERENT = [
    pytest.param(lambda: corrupt(observation="zzz"), id="observacion-zzz"),
    pytest.param(lambda: corrupt(observation=None), id="observacion-none"),
    pytest.param(lambda: corrupt(currency="JPY"), id="moneda-JPY"),
    pytest.param(lambda: corrupt(currency="eur"), id="moneda-minusculas"),
    pytest.param(lambda: with_numerator(Decimal("-1")), id="impacto-negativo"),
    pytest.param(lambda: with_numerator(Decimal("1049.99")), id="impacto-menor-que-el-exceso"),
    pytest.param(lambda: corrupt(impact_day_count=0), id="dias-cero"),
    pytest.param(lambda: corrupt(impact_day_count=-1), id="dias-negativos"),
    pytest.param(lambda: corrupt(impact_day_count=True), id="dias-bool"),
    pytest.param(lambda: corrupt(impact_through_date=OPENED.replace(day=7)), id="ultimo-dia-anterior-al-inicio"),
    pytest.param(lambda: closed_without_reason(""), id="cerrado-motivo-vacio"),
    pytest.param(lambda: closed_without_reason("   "), id="cerrado-motivo-espacios"),
    pytest.param(lambda: with_operand("impact_numerator", Decimal("NaN")), id="numerador-nan"),
    pytest.param(lambda: with_operand("reference_week_cost", Decimal("NaN")), id="referencia-nan"),
    pytest.param(lambda: with_operand("opening_observed_cost", Decimal("NaN")), id="observado-nan"),
    pytest.param(lambda: with_operand("impact_numerator", Decimal("Infinity")), id="numerador-infinito"),
    pytest.param(lambda: with_operand("opening_observed_cost", Decimal("Infinity")), id="observado-infinito"),
    pytest.param(lambda: with_operand("reference_week_cost", Decimal("Infinity")), id="referencia-infinito"),
    pytest.param(lambda: with_operands(Decimal("1e200"), Decimal("2e199"), Decimal("5e199")), id="operandos-1e200"),
    pytest.param(lambda: with_operand("impact_numerator", Decimal("1e200")), id="numerador-1e200"),
]


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("build", INCOHERENT)
def test_episodio_con_datos_incoherentes_da_409_sin_guardar_ningun_mensaje(api, monkeypatch, build):
    # Control previo: la misma petición con una fotografía válida SÍ da 201, así que el 409 de abajo no se debe
    # a un campo desconocido ni a un 422 del cuerpo, sino a la fotografía corrupta que se sirve después.
    stub_store(api, monkeypatch)
    control = call(api, "POST", PATH, headers=headers(), json=anomaly_body())
    assert control.status_code == 201, control.text
    double = stub_store(api, monkeypatch, build())
    before, counter = stored_messages(api.db), queries()
    appended = api.spies["append_pair"].call_count

    response = call(api, "POST", PATH, headers=headers(), json=anomaly_body())

    # 409 con el cuerpo EXACTO del contrato (no un 500 por InvalidOperation ni un 201 con evidencia "ok").
    assert response.status_code == 409, response.text
    assert response.json() == UNAVAILABLE
    assert double.call_count == 1
    # Ningún mensaje nuevo: ni el del usuario ni el del asistente (el segundo ya cuenta la métrica).
    assert api.spies["append_pair"].call_count == appended
    assert stored_messages(api.db) == before
    assert queries() == counter
    api.vector.search_chunks.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_control_la_fotografia_valida_sigue_dando_201(api, monkeypatch):
    # Control de las pruebas de este archivo: con una fotografía válida el flujo completo funciona y guarda los
    # dos mensajes; así el 409 de las demás no es un efecto de un montaje roto.
    stub_store(api, monkeypatch)
    before, counter = stored_messages(api.db), queries()
    response = call(api, "POST", PATH, headers=headers(), json=anomaly_body())
    assert response.status_code == 201, response.text
    assert response.json()["assistant_message"]["metadata"]["anomaly_evidence"]["status"] == "ok"
    assert len(stored_messages(api.db)) == len(before) + 2
    assert queries() == counter + 1


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("build", [
    pytest.param(lambda: make_snapshot(days=1, through=OPENED, numerator="1050.00"), id="un-dia-numerador-igual-al-exceso"),
    pytest.param(lambda: make_snapshot(status="resolved", closed_at=CLOSED_AT,
                                       closure_reason="x"), id="motivo-de-un-caracter"),
    pytest.param(lambda: with_operands(Decimal("9" * 26), Decimal("2e25"), Decimal("5e25")), id="frontera-del-rango"),
])
def test_control_fronteras_validas_siguen_dando_201(api, monkeypatch, build):
    # Frontera: lo que está justo del lado válido de cada invariante no se rechaza (evita una validación que
    # devuelva 409 a todo).
    stub_store(api, monkeypatch, build())
    response = call(api, "POST", PATH, headers=headers(), json=anomaly_body())
    assert response.status_code == 201, response.text
