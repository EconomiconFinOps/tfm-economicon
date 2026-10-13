"""JUP-054 (hueco H-01): contrato de error y de forma de las rutas de facturacion.

Cubre offline (CI) las ramas de `app/api/routes/billing.py` que hasta ahora solo
se ejercitaban con CockroachDB real:

* `GET /billing/tag-coverage`: la llamada a `database.fetch_tag_coverage`, el
  mapeo `AmbiguousCostSource` -> 409 y `TagCoverage(**result)` (filtrado por el
  `response_model`).
* `GET /billing/summary`: el mapeo `AmbiguousCostSource` -> 409.

Alcance: se prueba el CONTRATO DE LA RUTA con la base sustituida. App real,
autenticacion real (token firmado), pertenencia real y SQLite para el resto de
la aplicacion; el unico doble es `fetch_tag_coverage` / `fetch_billing_summary`.
El SQL REAL de esas consultas (`jsonb_typeof`, `->>`, `regexp_replace`, deteccion
de fuentes solapadas) NO se prueba aqui, porque no es ejecutable en SQLite: sigue
cubierto por las variantes CockroachDB de `test_tag_coverage.py` y
`test_billing_summary.py`.

No se duplica `test_budget_evaluation.py::test_api_overlap_never_returns_amounts`
(409 de `/billing/budget/evaluate`) ni los rechazos 422/401/403 previos al SQL ya
presentes en `test_tag_coverage.py` y `test_billing_summary.py`.
"""
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.schemas.billing import AmbiguousCostSource
from billing_support import summary
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging

SQLITE = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)

COVERAGE_PATH = "/billing/tag-coverage"
PERIOD_QUERY = "?start_date=2024-06-01&end_date=2024-07-01"
SUMMARY_PATH = "/billing/summary"
AMBIGUOUS_BODY = {"detail": {"code": "ambiguous_cost_source"}}
# Marcador que el doble incrusta en el mensaje de la excepcion: simula un
# importe o dato de la consulta que NUNCA debe llegar al cliente ni a los logs.
LEAK_MARKER = "importe-secreto-9999999.99-run-solapado"



def zero_counts(**overrides):
    return {**{key: 0 for key in ("owner", "environment", "application", "cost_center", "project")}, **overrides}


def currency_row(**changes):
    return {
        "currency": "EUR", "record_count": 3, "compliant_record_count": 2, "noncompliant_record_count": 1,
        "positive_cost": "100.00", "compliant_cost": "80.00", "noncompliant_cost": "20.00",
        "negative_adjustments": "-30.00", "compliant_negative_adjustments": "-30.00",
        "noncompliant_negative_adjustments": "0.00",
        "net_cost": "70.00", "compliant_net_cost": "50.00", "noncompliant_net_cost": "20.00",
        "compliant_percent": "80.00", "noncompliant_percent": "20.00",
        "no_positive_cost_reason": None,
        "missing_or_invalid_tag_counts": zero_counts(owner=1, application=1),
        **changes,
    }


def coverage(**changes):
    """Resultado sintetico valido de `fetch_tag_coverage` con varias monedas."""
    return {
        "contract_version": 1, "policy_version": "economicon-minimum-v1",
        "required_tags": ["owner", "environment", "application", "cost_center", "project"],
        "period": {"start_date": "2024-06-01", "end_date": "2024-07-01", "timezone": "UTC"},
        "data_status": "partial", "excluded_undated_count": 1,
        "currencies": [
            currency_row(),
            # Importe por encima de 2**53: si alguna capa lo convirtiera a float
            # o a int de JSON perderia los centimos.
            currency_row(currency="USD", record_count=1, compliant_record_count=1, noncompliant_record_count=0,
                         positive_cost="9007199254740993.01", compliant_cost="9007199254740993.01",
                         noncompliant_cost="0.00", negative_adjustments="0.00",
                         compliant_negative_adjustments="0.00", net_cost="9007199254740993.01",
                         compliant_net_cost="9007199254740993.01", noncompliant_net_cost="0.00",
                         compliant_percent="100.00", noncompliant_percent="0.00",
                         missing_or_invalid_tag_counts=zero_counts()),
            # Sin coste positivo: los porcentajes son null (no "0.00") y debe
            # haber una razon; el null se debe conservar tal cual.
            currency_row(currency="GBP", record_count=1, compliant_record_count=0, noncompliant_record_count=1,
                         positive_cost="0.00", compliant_cost="0.00", noncompliant_cost="0.00",
                         negative_adjustments="-20.00", compliant_negative_adjustments="0.00",
                         noncompliant_negative_adjustments="-20.00", net_cost="-20.00",
                         compliant_net_cost="0.00", noncompliant_net_cost="-20.00",
                         compliant_percent=None, noncompliant_percent=None,
                         no_positive_cost_reason="negative_adjustments_only",
                         missing_or_invalid_tag_counts=zero_counts(owner=1, application=1)),
        ],
        **changes,
    }


@pytest.fixture
def coverage_double(api, monkeypatch):
    """Sustituye `fetch_tag_coverage` (frontera de base de datos) por un doble."""
    double = MagicMock(return_value=coverage())
    monkeypatch.setattr(api.db, "fetch_tag_coverage", double)
    return double


def snapshot(api):
    """Estado persistente observable por SQLite: ninguna ruta de lectura debe cambiarlo."""
    return {table: rows(api.db, table) for table in ("jobs", "conversations", "messages")}


def assert_no_side_effects(api, before):
    assert snapshot(api) == before
    for name in ("create_job", "create_conversation", "append_message"):
        api.spies[name].assert_not_called()
    api.queue.publish.assert_not_called()
    api.queue.reserve.assert_not_called()


# --------------------------------------------------------------------------
# A. GET /billing/tag-coverage
# --------------------------------------------------------------------------

@SQLITE
def test_tag_coverage_returns_contract_with_exact_decimal_strings_and_nulls(api, coverage_double):
    # Camino feliz con el doble: la ruta no debe transformar los importes. Las
    # cadenas decimales (incluido el importe > 2**53) y los null llegan intactos.
    response = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"contract_version", "policy_version", "required_tags", "period",
                         "data_status", "excluded_undated_count", "currencies"}
    assert body["contract_version"] == 1
    assert body["policy_version"] == "economicon-minimum-v1"
    assert body["required_tags"] == ["owner", "environment", "application", "cost_center", "project"]
    assert body["period"] == {"start_date": "2024-06-01", "end_date": "2024-07-01", "timezone": "UTC"}
    assert body["data_status"] == "partial" and body["excluded_undated_count"] == 1
    # Igualdad exacta con lo que devolvio el doble: ningun campo se pierde ni se reescribe.
    assert body == coverage()

    by_currency = {row["currency"]: row for row in body["currencies"]}
    assert list(by_currency) == ["EUR", "USD", "GBP"]
    assert by_currency["USD"]["compliant_cost"] == "9007199254740993.01"
    assert by_currency["USD"]["net_cost"] == "9007199254740993.01"
    assert by_currency["GBP"]["compliant_percent"] is None
    assert by_currency["GBP"]["noncompliant_percent"] is None
    assert by_currency["GBP"]["no_positive_cost_reason"] == "negative_adjustments_only"
    assert by_currency["EUR"]["no_positive_cost_reason"] is None
    # Los importes son cadenas JSON, nunca numeros (un float perderia precision).
    money = ("positive_cost", "compliant_cost", "noncompliant_cost", "negative_adjustments", "net_cost",
             "compliant_net_cost", "noncompliant_net_cost", "compliant_negative_adjustments",
             "noncompliant_negative_adjustments")
    for row in body["currencies"]:
        assert all(isinstance(row[key], str) for key in money), row["currency"]
    # Los contadores sí son enteros y se conservan.
    assert by_currency["EUR"]["missing_or_invalid_tag_counts"] == zero_counts(owner=1, application=1)
    assert coverage_double.call_count == 1


@SQLITE
def test_tag_coverage_default_contract_version_is_one_when_database_omits_it(api, coverage_double):
    # La version del contrato la fija el esquema: si la consulta no la aporta,
    # la respuesta sigue declarando contract_version 1.
    result = coverage()
    del result["contract_version"]
    coverage_double.return_value = result
    response = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())
    assert response.status_code == 200, response.text
    assert response.json()["contract_version"] == 1


@SQLITE
@pytest.mark.parametrize("user,tenant", [("alice", "tenant-a"), ("bob", "tenant-b"),
                                         ("multi", "tenant-a"), ("multi", "tenant-b")])
def test_tag_coverage_forwards_active_tenant_and_parsed_period(api, coverage_double, user, tenant):
    # El tenant llega SIEMPRE desde el contexto autenticado (cabecera validada
    # contra la pertenencia), incluido el usuario multi-tenant, y las fechas
    # llegan ya parseadas como `date` en el orden (inicio, fin).
    response = call(api, "GET", COVERAGE_PATH + "?start_date=2024-06-01&end_date=2024-07-15",
                    headers=headers(user, tenant))
    assert response.status_code == 200, response.text
    coverage_double.assert_called_once_with(tenant, start_date=date(2024, 6, 1), end_date=date(2024, 7, 15))
    kwargs = coverage_double.call_args.kwargs
    assert type(kwargs["start_date"]) is date and type(kwargs["end_date"]) is date


@SQLITE
def test_tag_coverage_without_dates_uses_current_utc_calendar_month(api, coverage_double):
    # Sin fechas se usa el mes calendario UTC en curso. No se compara con el
    # reloj real (fallaria en el cambio de mes): se asierta la forma del periodo.
    response = call(api, "GET", COVERAGE_PATH, headers=headers())
    assert response.status_code == 200, response.text
    coverage_double.assert_called_once()
    start, end = coverage_double.call_args.kwargs["start_date"], coverage_double.call_args.kwargs["end_date"]
    assert type(start) is date and type(end) is date
    assert start.day == 1 and end.day == 1 and end > start
    expected_end = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    assert (end.year, end.month) == expected_end
    assert 28 <= (end - start).days <= 31


def freeze_clock(monkeypatch, instant):
    """Reloj congelado: sustituye solo la fuente de tiempo del servicio de fecha de referencia."""
    monkeypatch.setattr("app.services.reference_date._utc_now", lambda: instant.astimezone(timezone.utc))


@SQLITE
@pytest.mark.parametrize("instant,start,end", [
    # Mitad de mes, cambio de año, año bisiesto y limites del mes (UTC).
    (datetime(2024, 6, 15, 12, tzinfo=timezone.utc), date(2024, 6, 1), date(2024, 7, 1)),
    (datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc), date(2024, 12, 1), date(2025, 1, 1)),
    (datetime(2024, 2, 29, tzinfo=timezone.utc), date(2024, 2, 1), date(2024, 3, 1)),
    (datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc), date(2025, 1, 1), date(2025, 2, 1)),
    (datetime(2024, 6, 30, 23, 59, 59, tzinfo=timezone.utc), date(2024, 6, 1), date(2024, 7, 1)),
])
def test_tag_coverage_default_period_is_exactly_the_current_month(api, coverage_double, monkeypatch,
                                                                  instant, start, end):
    # Con el reloj congelado (frontera de tiempo) el periodo por defecto es
    # exactamente [primer dia del mes en curso, primer dia del mes siguiente),
    # incluida la vuelta de año; un mes anterior o un solo dia serian detectados.
    freeze_clock(monkeypatch, instant)
    response = call(api, "GET", COVERAGE_PATH, headers=headers())
    assert response.status_code == 200, response.text
    coverage_double.assert_called_once_with("tenant-a", start_date=start, end_date=end)


@SQLITE
def test_tag_coverage_explicit_dates_win_over_current_month(api, coverage_double, monkeypatch):
    # Con fechas explicitas el reloj no interviene: ni siquiera se consulta.
    def boom():
        raise AssertionError("El reloj no debe leerse si hay fechas explicitas")
    monkeypatch.setattr("app.services.reference_date._utc_now", boom)
    response = call(api, "GET", COVERAGE_PATH + "?start_date=2023-01-10&end_date=2023-03-05", headers=headers())
    assert response.status_code == 200, response.text
    coverage_double.assert_called_once_with("tenant-a", start_date=date(2023, 1, 10), end_date=date(2023, 3, 5))


@SQLITE
def test_tag_coverage_response_model_drops_unexpected_keys(api, coverage_double):
    # El `response_model` actua de filtro: una clave extra del repositorio
    # (p. ej. SQL de depuracion) no debe filtrarse al cliente, ni a nivel raiz
    # ni dentro de cada moneda ni dentro del periodo.
    leaky = coverage(debug_sql="SELECT * FROM azure_cost_records WHERE tenant_id = 'tenant-b'")
    leaky["currencies"][0]["internal_cost_id"] = "run-solapado-1"
    leaky["period"]["debug_tenant"] = "tenant-b"
    coverage_double.return_value = leaky
    response = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())
    assert response.status_code == 200, response.text
    assert response.json() == coverage()
    for marker in ("debug_sql", "SELECT", "internal_cost_id", "run-solapado-1", "debug_tenant"):
        assert marker not in response.text


@SQLITE
def test_tag_coverage_ambiguous_source_is_409_with_exact_body_and_no_data(api, coverage_double, capsys, caplog):
    # Fuentes de coste solapadas: 409 con un cuerpo cerrado. El mensaje de la
    # excepcion (que en un mal diseño podria llevar importes) no se propaga.
    coverage_double.side_effect = AmbiguousCostSource(LEAK_MARKER)
    before = snapshot(api)

    response = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())

    assert response.status_code == 409
    assert response.json() == AMBIGUOUS_BODY
    assert response.text.replace(" ", "") == '{"detail":{"code":"ambiguous_cost_source"}}'
    captured = capsys.readouterr()
    assert LEAK_MARKER not in response.text + captured.out + captured.err + caplog.text
    coverage_double.assert_called_once_with("tenant-a", start_date=date(2024, 6, 1), end_date=date(2024, 7, 1))
    assert_no_side_effects(api, before)


@SQLITE
def test_tag_coverage_ambiguous_source_with_default_period_and_other_tenant(api, coverage_double):
    # El mismo 409 se produce sin fechas y para otro tenant: el mapeo no depende
    # de la rama del periodo ni del tenant.
    coverage_double.side_effect = AmbiguousCostSource()
    response = call(api, "GET", COVERAGE_PATH, headers=headers("bob", "tenant-b"))
    assert response.status_code == 409
    assert response.json() == AMBIGUOUS_BODY
    assert coverage_double.call_args.args == ("tenant-b",)


@SQLITE
@pytest.mark.parametrize("error", [RuntimeError, ValueError])
def test_tag_coverage_unexpected_error_is_not_mapped_to_409(api, coverage_double, capsys, caplog, error):
    # Solo `AmbiguousCostSource` es un 409 de negocio. Cualquier otro fallo del
    # repositorio es un error interno: la app real (ASGI sin re-lanzar) lo
    # responde como 500 generico, sin filtrar el mensaje. Se incluye un
    # `ValueError` plano porque `AmbiguousCostSource` HEREDA de `ValueError`:
    # el mapeo no debe ser tan ancho como para capturar a su clase base.
    coverage_double.side_effect = error(LEAK_MARKER)
    response = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())
    assert response.status_code == 500
    captured = capsys.readouterr()
    assert LEAK_MARKER not in response.text + captured.out + captured.err + caplog.text
    assert "ambiguous_cost_source" not in response.text


@SQLITE
def test_tag_coverage_malformed_result_is_internal_error_not_partial_payload(api, coverage_double):
    # `TagCoverage(**result)` valida lo que devuelve el repositorio: un importe
    # que no es una cadena decimal de dos decimales (float) no se emite como 200.
    broken = coverage()
    broken["currencies"][0]["positive_cost"] = 100.0
    coverage_double.return_value = broken
    response = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())
    assert response.status_code == 500
    assert "positive_cost" not in response.text and "100.0" not in response.text


# --------------------------------------------------------------------------
# B. GET /billing/summary
# --------------------------------------------------------------------------

@SQLITE
@pytest.mark.parametrize("user,tenant,query,group_by,tag_key", [
    ("alice", "tenant-a", "group_by=service", "service", None),
    ("multi", "tenant-b", "group_by=tag&tag_key=Org", "tag", "organization"),
])
def test_summary_success_queries_the_repository_exactly_once(api, user, tenant, query, group_by, tag_key):
    # Camino feliz de la ruta con el doble: una sola consulta de costes por
    # peticion (una consulta duplicada seria coste y riesgo de lecturas
    # inconsistentes) y con los argumentos canonicos y el tenant activo.
    expected = summary(group_by=group_by, tag_key=tag_key)
    api.spies["fetch_billing_summary"].side_effect = None
    api.spies["fetch_billing_summary"].return_value = expected
    response = call(api, "GET", SUMMARY_PATH + PERIOD_QUERY + "&" + query, headers=headers(user, tenant))
    assert response.status_code == 200, response.text
    assert response.json() == expected
    api.spies["fetch_billing_summary"].assert_called_once_with(
        tenant, start_date=date(2024, 6, 1), end_date=date(2024, 7, 1), group_by=group_by, tag_key=tag_key,
    )


@SQLITE
@pytest.mark.parametrize("query,group_by,tag_key", [
    ("group_by=subscription", "subscription", None),
    ("group_by=resource_group", "resource_group", None),
    ("group_by=service", "service", None),
    ("group_by=project", "project", None),
    # La clave se canoniza antes de llegar a la base: "Env" -> "environment".
    ("group_by=tag&tag_key=Env", "tag", "environment"),
    ("group_by=tag&tag_key=%20Cost-Centre%20", "tag", "cost_center"),
])
def test_summary_ambiguous_source_is_409_for_every_grouping(api, query, group_by, tag_key, capsys, caplog):
    # El mapeo 409 debe aplicarse a TODAS las agrupaciones (incluida `tag`,
    # que tiene una rama de validacion propia) y con los argumentos canonicos.
    api.spies["fetch_billing_summary"].side_effect = AmbiguousCostSource(LEAK_MARKER)
    before = snapshot(api)

    response = call(api, "GET", SUMMARY_PATH + "?start_date=2024-06-01&end_date=2024-07-01&" + query,
                    headers=headers())

    assert response.status_code == 409
    assert response.json() == AMBIGUOUS_BODY
    captured = capsys.readouterr()
    assert LEAK_MARKER not in response.text + captured.out + captured.err + caplog.text
    api.spies["fetch_billing_summary"].assert_called_once_with(
        "tenant-a", start_date=date(2024, 6, 1), end_date=date(2024, 7, 1),
        group_by=group_by, tag_key=tag_key,
    )
    # Ningun dato de coste ni clave del resumen en el cuerpo de error.
    assert not {"totals", "groups", "monthly_spend", "period"}.intersection(response.json())
    api.spies["fetch_billing_summary"].reset_mock()
    assert_no_side_effects(api, before)


@SQLITE
def test_summary_ambiguous_source_uses_active_tenant_and_default_period(api):
    # Sin fechas y con el tenant-b del usuario multi-tenant: el 409 sigue
    # siendo el mismo y el doble recibe el tenant activo.
    api.spies["fetch_billing_summary"].side_effect = AmbiguousCostSource()
    response = call(api, "GET", SUMMARY_PATH, headers=headers("multi", "tenant-b"))
    assert response.status_code == 409
    assert response.json() == AMBIGUOUS_BODY
    [call_] = api.spies["fetch_billing_summary"].call_args_list
    assert call_.args == ("tenant-b",)
    assert call_.kwargs["group_by"] == "subscription" and call_.kwargs["tag_key"] is None
    start, end = call_.kwargs["start_date"], call_.kwargs["end_date"]
    assert start.day == 1 and end.day == 1 and end > start


@SQLITE
@pytest.mark.parametrize("error", [RuntimeError, ValueError])
@pytest.mark.parametrize("query", ["group_by=subscription", "group_by=tag&tag_key=owner"])
def test_summary_unexpected_error_is_not_mapped_to_409(api, query, error, capsys, caplog):
    # Un fallo que no es `AmbiguousCostSource` no se disfraza de conflicto de
    # negocio: respuesta 500 generica sin el mensaje interno. `ValueError`
    # plano incluido, porque `AmbiguousCostSource` hereda de el.
    api.spies["fetch_billing_summary"].side_effect = error(LEAK_MARKER)
    response = call(api, "GET", SUMMARY_PATH + "?start_date=2024-06-01&end_date=2024-07-01&" + query,
                    headers=headers())
    assert response.status_code == 500
    captured = capsys.readouterr()
    assert LEAK_MARKER not in response.text + captured.out + captured.err + caplog.text
    assert "ambiguous_cost_source" not in response.text
    api.spies["fetch_billing_summary"].assert_called_once()


# --------------------------------------------------------------------------
# C. Un 409 no afecta a otras rutas ni escribe nada
# --------------------------------------------------------------------------

@SQLITE
def test_conflict_is_stateless_and_does_not_affect_other_routes(api, coverage_double):
    # Tras un 409 en ambas rutas de facturacion: (1) el doble se llamo una vez
    # por peticion, (2) nada se escribio, (3) otras rutas y la propia ruta
    # (con el doble ya sano) responden con normalidad, es decir el conflicto no
    # deja estado residual ni cachea el error.
    before = snapshot(api)
    coverage_double.side_effect = AmbiguousCostSource(LEAK_MARKER)
    api.spies["fetch_billing_summary"].side_effect = AmbiguousCostSource(LEAK_MARKER)

    first = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())
    second = call(api, "GET", SUMMARY_PATH + PERIOD_QUERY + "&group_by=service", headers=headers())
    assert (first.status_code, second.status_code) == (409, 409)
    assert first.json() == second.json() == AMBIGUOUS_BODY
    assert coverage_double.call_count == 1
    assert api.spies["fetch_billing_summary"].call_count == 1
    assert_no_side_effects(api, before)

    # Otra ruta autenticada, sin relacion con costes, sigue funcionando.
    listing = call(api, "GET", "/assistant/conversations", headers=headers())
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == ["own"]

    # El conflicto de una ruta no contamina a la otra: cada una se recupera
    # sola cuando su repositorio deja de reportar solapes.
    coverage_double.side_effect = None
    recovered = call(api, "GET", COVERAGE_PATH + PERIOD_QUERY, headers=headers())
    assert recovered.status_code == 200 and recovered.json() == coverage()
    # El resumen sigue en conflicto mientras su doble lo siga lanzando.
    still = call(api, "GET", SUMMARY_PATH + PERIOD_QUERY + "&group_by=service", headers=headers())
    assert still.status_code == 409 and still.json() == AMBIGUOUS_BODY
    api.spies["fetch_billing_summary"].side_effect = None
    api.spies["fetch_billing_summary"].return_value = summary()
    healthy = call(api, "GET", SUMMARY_PATH + PERIOD_QUERY + "&group_by=service", headers=headers())
    assert healthy.status_code == 200 and healthy.json() == summary()
    assert_no_side_effects(api, before)


@SQLITE
@pytest.mark.parametrize("path", [COVERAGE_PATH + PERIOD_QUERY, SUMMARY_PATH + PERIOD_QUERY])
@pytest.mark.parametrize("authorization,tenant,status", [(False, "tenant-a", 401), (True, "tenant-b", 403)])
def test_conflict_mapping_never_masks_auth_or_membership_errors(api, coverage_double, path, authorization,
                                                                tenant, status):
    # Aunque los repositorios lanzarian `AmbiguousCostSource`, la autenticacion
    # y la pertenencia se resuelven antes: el 409 nunca sustituye a un 401/403
    # ni se llega a consultar costes de un tenant ajeno.
    coverage_double.side_effect = AmbiguousCostSource()
    api.spies["fetch_billing_summary"].side_effect = AmbiguousCostSource()
    response = call(api, "GET", path, headers=headers(tenant=tenant) if authorization else [])
    assert response.status_code == status
    coverage_double.assert_not_called()
    api.spies["fetch_billing_summary"].assert_not_called()
