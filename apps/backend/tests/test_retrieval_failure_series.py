"""JUP-121: las series de fallos de recuperación existen desde el arranque, con valor 0.

Defecto que se vigila: `backend_retrieval_failures_total` lleva la etiqueta `category`. Un contador
con etiqueta no expone ninguna serie hasta la primera llamada a `.labels(...)`, es decir, hasta el
primer fallo. Mientras todo va bien, `sum(rate(backend_retrieval_failures_total[5m]))` es un vector
vacío en Prometheus y las proporciones del dashboard de evaluación (búsquedas sin contexto y fallos
sobre consultas terminadas) salen en «Sin datos» aunque haya consultas. La práctica estándar de
Prometheus es inicializar a 0 una serie por cada categoría conocida al importar el módulo de rutas.

Metodología: los contadores son globales del proceso y otros tests los incrementan, así que el
caso «recién importada» (valor exactamente 0.0) se comprueba en un SUBPROCESO limpio de Python que
importa la aplicación sin haber provocado ningún fallo. Los casos en el proceso de pytest usan solo
comparaciones relativas (antes/después) o propiedades que no dependen del estado acumulado, de modo
que el resultado no depende del orden de ejecución.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from prometheus_client import generate_latest

from app.api.routes import assistant
from app.api.routes.assistant import FAILURE_CATEGORIES
from app.services.embedding_provider import PROVIDER_ERROR_CATEGORIES

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Coincidencia exacta con el nombre `_total`: excluye la serie auxiliar `_created`, que también
# lleva la etiqueta `category` pero no es el contador.
SERIES = re.compile(r'^backend_retrieval_failures_total\{category="([^"]*)"\} (\S+)$', re.MULTILINE)

# Entorno sintético equivalente al de conftest.py; el subproceso no hereda las fixtures.
SYNTHETIC_ENV = {
    "RUNTIME_ENVIRONMENT": "test",
    "AUTH_SECRET_KEY": "jup121-synthetic-jwt-key-0123456789abcdef",
    "DATABASE_URL": "cockroachdb+psycopg://unit:db-fixture-pass@127.0.0.1:26257/unit?sslmode=require",
    "RABBITMQ_URL": "amqp://unit:broker-fixture-pass@127.0.0.1:5672/%2F",
    "VECTOR_DATABASE_URL": "postgresql+psycopg://unit:vector-fixture-pass@127.0.0.1:5432/unit",
    "ALLOW_INSECURE_LOCAL_DATABASE": "false",
    "DEMO_SEED_ENABLED": "false",
    "AZURE_COST_API_BASE_URL": "http://127.0.0.1:9",
}

# Script del subproceso: importa la aplicación completa, vuelca la exposición de /metrics antes de
# provocar ningún fallo, vuelve a importar (reload) y crea un segundo cliente, y solo después
# provoca fallos controlados para observar qué series cambian.
CHILD_SCRIPT = r"""
import importlib, json, sys
sys.path.insert(0, sys.argv[1])
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import assistant

def scrape(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    return response.text

def provoke(category):
    try:
        assistant._retrieval_failed(category, {"tenant_id": "t"}, 0.0)
    except HTTPException:
        pass

out = {}
first = TestClient(app)
out["fresh"] = scrape(first)
# Segundo cliente y nueva importación del módulo de rutas: no deben duplicar series ni lanzar
# `ValueError: Duplicated timeseries`.
second = TestClient(app)
out["second_client"] = scrape(second)
importlib.import_module("app.api.routes.assistant")
importlib.reload(assistant)
out["after_reload"] = scrape(second)
provoke("rate_limit")
out["after_failure"] = scrape(second)
provoke("categoria-inventada-por-el-upstream")
out["after_unknown"] = scrape(second)
print("@@JSON@@" + json.dumps(out))
"""


def parse(exposition: str) -> dict:
    """Devuelve {categoria: valor} de las series `backend_retrieval_failures_total`."""
    return {category: float(value) for category, value in SERIES.findall(exposition)}


def lines_of(exposition: str, name: str) -> list:
    return [line for line in exposition.splitlines() if re.match(rf"^{name}(\{{| )", line)]


@pytest.fixture(scope="module")
def child():
    """Una sola ejecución del subproceso limpio compartida por los casos que la necesitan."""
    import os

    env = {**os.environ, **SYNTHETIC_ENV}
    for key in ("ECONOMICON_ENV_FILE", "LITELLM_API_KEY", "OPENROUTER_API_KEY", "LITELLM_MASTER_KEY"):
        env.pop(key, None)
    done = subprocess.run(
        [sys.executable, "-c", CHILD_SCRIPT, str(BACKEND_DIR)],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120,
    )
    assert done.returncode == 0, done.stderr[-2000:]
    payload = done.stdout.split("@@JSON@@", 1)[1]
    return json.loads(payload)


# --------------------------------------------------------------------------------------------
# Contrato del conjunto de categorías (no depende del estado de los contadores)
# --------------------------------------------------------------------------------------------

def test_the_known_categories_include_vector_store_and_the_provider_categories():
    # `vector_store` no es una categoría del proveedor: la añade la ruta del asistente.
    assert "vector_store" in FAILURE_CATEGORIES
    esperadas = {
        "timeout", "connection", "transport", "authentication", "request", "redirect",
        "rate_limit", "upstream", "invalid_response", "schema_validation",
    }
    # Solo se exigen las que el proveedor define hoy; `schema_validation` es opcional si no existe.
    exigidas = esperadas & (set(PROVIDER_ERROR_CATEGORIES) | {"vector_store"})
    assert exigidas <= FAILURE_CATEGORIES
    assert set(PROVIDER_ERROR_CATEGORIES) <= FAILURE_CATEGORIES
    assert FAILURE_CATEGORIES == set(PROVIDER_ERROR_CATEGORIES) | {"vector_store"}


# --------------------------------------------------------------------------------------------
# (1) y (2) Aplicación recién importada, sin fallos: subproceso limpio
# --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("category", sorted(FAILURE_CATEGORIES))
def test_every_known_category_is_exposed_at_zero_before_any_failure(child, category):
    # Sin esta serie, `sum(rate(...))` es un vector vacío y el panel sale en «Sin datos».
    exposed = child["fresh"]
    linea = f'backend_retrieval_failures_total{{category="{category}"}} 0.0'
    assert linea in exposed.splitlines()


def test_only_the_known_categories_are_exposed_on_a_fresh_app(child):
    series = parse(child["fresh"])
    # Exactamente el conjunto conocido: ni categorías de menos ni inventadas de más.
    assert set(series) == set(FAILURE_CATEGORIES)
    # Una línea por categoría: sin duplicados en la exposición.
    assert len(SERIES.findall(child["fresh"])) == len(FAILURE_CATEGORIES)


def test_the_failure_series_add_up_to_zero_on_a_fresh_app(child):
    series = parse(child["fresh"])
    assert series, "la exposición no trae ninguna serie con etiqueta: el vector sería vacío"
    assert all(value >= 0 for value in series.values())
    assert sum(series.values()) == 0.0


def test_the_other_domain_counters_stay_unlabelled(child):
    # Los contadores de consultas y de búsquedas vacías no llevan etiquetas: una línea sin `{`.
    for name in ("backend_assistant_queries_total", "backend_retrieval_empty_total"):
        lineas = lines_of(child["fresh"], name)
        assert lineas == [f"{name} 0.0"], lineas


# --------------------------------------------------------------------------------------------
# (4) Importación repetida y varios clientes
# --------------------------------------------------------------------------------------------

def test_a_second_client_and_a_module_reload_do_not_duplicate_or_change_series(child):
    # `after_reload` sale tras crear otro cliente e importar/recargar el módulo de rutas.
    assert parse(child["second_client"]) == parse(child["fresh"])
    for clave in ("second_client", "after_reload"):
        assert len(SERIES.findall(child[clave])) == len(FAILURE_CATEGORIES)
        # Recargar no debe sumar nada: la inicialización escribe 0 y no incrementa.
        assert sum(parse(child[clave]).values()) == 0.0


# --------------------------------------------------------------------------------------------
# (3) y (5) Un fallo sube solo su categoría; una desconocida se normaliza
# --------------------------------------------------------------------------------------------

def test_a_failure_raises_only_its_own_category_in_a_clean_process(child):
    antes = parse(child["after_reload"])
    despues = parse(child["after_failure"])
    # No se crean categorías nuevas al fallar.
    assert set(despues) == set(FAILURE_CATEGORIES) == set(antes)
    assert despues["rate_limit"] == 1.0
    assert {c: v for c, v in despues.items() if c != "rate_limit"} == {
        c: 0.0 for c in FAILURE_CATEGORIES if c != "rate_limit"
    }


def test_an_unknown_category_is_normalised_and_never_becomes_an_extra_series(child):
    despues = parse(child["after_unknown"])
    assert "categoria-inventada-por-el-upstream" not in despues
    assert set(despues) == set(FAILURE_CATEGORIES)
    # Se contabiliza como `transport` (normalización existente) y rate_limit conserva su 1.0.
    assert despues["transport"] == 1.0
    assert despues["rate_limit"] == 1.0
    assert sum(despues.values()) == 2.0


# --------------------------------------------------------------------------------------------
# Casos en el proceso de pytest: solo propiedades y deltas, independientes del orden
# --------------------------------------------------------------------------------------------

def _exposition() -> str:
    return generate_latest().decode()


def test_the_registry_exposes_exactly_the_known_categories_whatever_ran_before():
    series = parse(_exposition())
    # Otros tests pueden haber subido valores, pero el conjunto de etiquetas es fijo y completo.
    assert set(series) == set(FAILURE_CATEGORIES)
    assert all(value >= 0 for value in series.values())
    assert len(SERIES.findall(_exposition())) == len(FAILURE_CATEGORIES)


@pytest.mark.parametrize("category", sorted(FAILURE_CATEGORIES))
def test_a_failure_raises_only_its_category_by_one_in_the_shared_registry(category):
    from fastapi import HTTPException

    antes = parse(_exposition())
    with pytest.raises(HTTPException):
        assistant._retrieval_failed(category, {"tenant_id": "t"}, 0.0)
    despues = parse(_exposition())
    # Delta relativo: solo sube la categoría provocada y no aparecen categorías nuevas.
    assert set(despues) == set(antes) == set(FAILURE_CATEGORIES)
    assert despues[category] == antes[category] + 1
    assert {c: v for c, v in despues.items() if c != category} == {
        c: v for c, v in antes.items() if c != category
    }


def test_the_domain_counters_are_still_unlabelled_in_the_shared_registry():
    exposicion = _exposition()
    for name in ("backend_assistant_queries_total", "backend_retrieval_empty_total"):
        lineas = lines_of(exposicion, name)
        assert len(lineas) == 1 and "{" not in lineas[0]
