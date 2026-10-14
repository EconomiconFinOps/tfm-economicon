"""JUP-038 (defecto de la validación del PR #128): la procedencia sintética debe leerse igual en la lista y en la explicación.

Tras integrar JUP-119 hay DOS recorridos que deciden si un cliente tiene datos sintéticos de demostración:

* `Database.fetch_anomaly_episode_list` (panel): una ingesta COMPLETADA del cliente cuenta como sintética si
  `request->'synthetic'` es `true` O si `subscription_id` EMPIEZA por `synthetic-`.
* `Database.fetch_anomaly_episode_snapshot` (explicación): solo miraba `request->'synthetic'`.

El cargador de la demo (`scripts/demo_data.py`) deja una ingesta completada con
`subscription_id = 'synthetic-anomalies'` y `request = {}`: el panel avisaba de datos sintéticos y la explicación
no. Estas pruebas fijan que ambos recorridos aplican la MISMA regla y que el aviso se conserva en el mensaje
guardado. Son opt-in (CockroachDB real vía `JUP086_COCKROACH_TEST_URL`): lo que importa es el comportamiento
del `LIKE` y del operador JSONB del motor, que un doble en memoria no reproduce.

Convención de las ingestas extra: se insertan por SQL sin costes asociados. La detección y el episodio salen
de la ingesta `run-a` (cliente `tenant-a`, suscripción `sub-a`, `request = {}`), que por sí sola NO es
sintética; así cada caso aísla la contribución de la ingesta que se añade.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from anomaly_episode_support import episode_store
from billing_support import billing_schema
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_anomaly_episode_api import EPISODES
from test_anomaly_episode_snapshot import open_episode
from test_anomaly_explanation_cockroach import explained, opened_episode, stored_messages
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers

AVISO = "Aviso: los datos de este cliente incluyen datos sintéticos de demostración."
MARKED = '{"synthetic": true}'


def add_run(db, run_id, *, subscription, request="{}", tenant="tenant-a", status="completed"):
    """Inserta una ingesta con la suscripción, el `request` JSON, el cliente y el estado indicados."""
    with db.engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO azure_cost_ingestion_runs (id, tenant_id, subscription_id, request, status, started_at) "
            "VALUES (:id, :tenant, :subscription, CAST(:request AS JSONB), :status, :now)"
        ), {"id": run_id, "tenant": tenant, "subscription": subscription, "request": request,
            "status": status, "now": datetime.now(timezone.utc)})


# Tabla de configuraciones: (identificador, suscripción de la ingesta base del episodio, ingestas extra, esperado).
# Cada ingesta extra es (suscripción, request JSON, cliente, estado). La base es siempre del cliente
# `tenant-a`, completada y con `request = {}`.
CASES = [
    # --- Deben dar True ---
    # El defecto: es lo que deja `scripts/demo_data.py`. Hoy el snapshot devuelve False (Red).
    pytest.param("sub-a", [("synthetic-anomalies", "{}", "tenant-a", "completed")], True, id="demo-prefijo-synthetic-anomalies"),
    # Mismo prefijo con otro sufijo: la regla es el prefijo, no el nombre concreto de la demo.
    pytest.param("sub-a", [("synthetic-core", "{}", "tenant-a", "completed")], True, id="prefijo-con-otro-sufijo"),
    # Borde: el prefijo exacto con sufijo vacío también casa con `LIKE 'synthetic-%'` (`%` admite cero caracteres).
    pytest.param("sub-a", [("synthetic-", "{}", "tenant-a", "completed")], True, id="prefijo-sin-sufijo"),
    # La ingesta base del propio episodio es la sintética (el cargador carga costes y episodio en ella).
    pytest.param("synthetic-anomalies", [], True, id="la-ingesta-base-es-la-demo"),
    # Regresión: la marca explícita en `request` con suscripción normal ya funcionaba en ambos recorridos.
    pytest.param("sub-a", [("sub-a", MARKED, "tenant-a", "completed")], True, id="request-synthetic-true"),
    # Ambas señales a la vez no deben anularse ni duplicar nada.
    pytest.param("sub-a", [("synthetic-anomalies", MARKED, "tenant-a", "completed")], True, id="ambas-senales"),
    # --- Deben dar False ---
    # Control base: suscripción normal y `request` vacío.
    pytest.param("sub-a", [("sub-a", "{}", "tenant-a", "completed")], False, id="ingesta-normal"),
    # El prefijo solo vale al principio: contenerlo en medio o con una letra delante NO es sintético.
    pytest.param("sub-a", [("my-synthetic-x", "{}", "tenant-a", "completed")], False, id="contiene-pero-no-empieza"),
    pytest.param("sub-a", [("xsynthetic-core", "{}", "tenant-a", "completed")], False, id="letra-antes-del-prefijo"),
    # Sin el guion no es el prefijo `synthetic-`.
    pytest.param("sub-a", [("syntheticcore", "{}", "tenant-a", "completed")], False, id="sin-guion"),
    # AMBIGÜEDAD documentada: el `LIKE` de la lista distingue mayúsculas, así que `SYNTHETIC-x` NO es sintética
    # hoy en la lista. El snapshot debe reflejar lo mismo (coherencia), no decidir una regla distinta.
    pytest.param("sub-a", [("SYNTHETIC-x", "{}", "tenant-a", "completed")], False, id="prefijo-en-mayusculas-distingue-caso"),
    # `request.synthetic` solo cuenta si es el booleano `true` de JSON: el texto "true" o `false` no lo son.
    pytest.param("sub-a", [("sub-a", '{"synthetic": "true"}', "tenant-a", "completed")], False, id="request-synthetic-texto"),
    pytest.param("sub-a", [("sub-a", '{"synthetic": false}', "tenant-a", "completed")], False, id="request-synthetic-false"),
    # Aislamiento: una ingesta sintética de OTRO cliente no contamina a `tenant-a` (ni por prefijo ni por marca).
    pytest.param("sub-a", [("synthetic-anomalies", "{}", "tenant-b", "completed")], False, id="prefijo-de-otro-cliente"),
    pytest.param("sub-a", [("sub-b", MARKED, "tenant-b", "completed")], False, id="marca-de-otro-cliente"),
    # Solo cuentan las ingestas COMPLETADAS: una en curso o fallida no aportó datos al episodio.
    pytest.param("sub-a", [("synthetic-anomalies", "{}", "tenant-a", "running")], False, id="prefijo-en-curso"),
    pytest.param("sub-a", [("synthetic-anomalies", "{}", "tenant-a", "failed")], False, id="prefijo-fallida"),
    pytest.param("sub-a", [("sub-a", MARKED, "tenant-a", "failed")], False, id="marca-fallida"),
]


def prepare(db, base_subscription, extra_runs):
    """Abre el episodio de `tenant-a` y añade las ingestas extra; devuelve el id del episodio."""
    episode_id = open_episode(db, subscription=base_subscription)
    for index, (subscription, request, tenant, status) in enumerate(extra_runs):
        add_run(db, f"run-extra-{index}", subscription=subscription, request=request, tenant=tenant, status=status)
    return episode_id


# --------------------------------------------------------------------------------------------------
# 1. La lectura de la explicación (snapshot) reconoce la procedencia sintética
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("base_subscription, extra_runs, expected", CASES)
def test_snapshot_reconoce_la_procedencia_sintetica_con_la_regla_de_la_lista(
        episode_store, base_subscription, extra_runs, expected):
    # Valida la regla completa en la lectura de la explicación: marca `request.synthetic = true` O prefijo
    # `synthetic-` en la suscripción, solo de ingestas completadas del propio cliente. Los casos True con
    # prefijo son el defecto (hoy el snapshot devuelve False); el resto son controles y regresiones.
    db = episode_store
    episode_id = prepare(db, base_subscription, extra_runs)
    assert db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["includes_synthetic_data"] is expected


# --------------------------------------------------------------------------------------------------
# 2. Coherencia lista / snapshot: no pueden volver a divergir
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("base_subscription, extra_runs, expected", CASES)
def test_lista_y_snapshot_coinciden_en_la_procedencia_sintetica(
        episode_store, base_subscription, extra_runs, expected):
    # Para cada configuración de ingestas, el panel y la explicación dan el MISMO valor y es el esperado.
    # Comparar los dos entre sí (además de con el valor esperado) es lo que impide que una futura regla
    # nueva en uno de los recorridos se olvide en el otro, que fue exactamente el defecto.
    db = episode_store
    episode_id = prepare(db, base_subscription, extra_runs)
    in_list = db.fetch_anomaly_episode_list("tenant-a")["includes_synthetic_data"]
    in_snapshot = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["includes_synthetic_data"]
    assert (in_list, in_snapshot) == (expected, expected)


# --------------------------------------------------------------------------------------------------
# 3. Extremo a extremo por HTTP con la ingesta de la demo
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_explicacion_sin_ingesta_sintetica_no_lleva_aviso_control(episode_store, api):
    # Control: sin la ingesta de la demo, el contenido NO contiene la línea de aviso y la evidencia es False.
    # Sin este control, un aviso que apareciera siempre haría pasar el caso positivo por vacuidad.
    episode_id = opened_episode(api, episode_store)

    _, assistant = explained(api, episode_id)

    assert AVISO not in assistant["content"]
    assert assistant["metadata"]["anomaly_evidence"]["includes_synthetic_data"] is False
    assert AVISO not in stored_messages(api)[-1]["content"]


@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_explicacion_con_la_ingesta_de_la_demo_lleva_el_aviso_y_lo_conserva_al_recargar(episode_store, api):
    # Reproduce el escenario real del defecto: ingesta completada con `subscription_id = 'synthetic-anomalies'`
    # y sin `request.synthetic`. El panel ya avisaba; la explicación debe avisar igual, en el texto y en la
    # evidencia, y el aviso debe seguir ahí al recuperar la conversación (lo guardado no se reescribe).
    episode_id = opened_episode(api, episode_store)
    add_run(episode_store, "run-demo", subscription="synthetic-anomalies")
    # El panel (lista por HTTP) ya reconoce la procedencia: confirma que el escenario es el del defecto.
    panel = call(api, "GET", EPISODES, headers=headers()).json()
    assert panel["includes_synthetic_data"] is True

    reply, assistant = explained(api, episode_id)

    assert AVISO in assistant["content"]
    evidence = assistant["metadata"]["anomaly_evidence"]
    assert evidence["includes_synthetic_data"] is True
    # Se conserva al recuperar: el mensaje guardado conserva el aviso en el texto y la marca en la metadata,
    # idénticos a los que devolvió la petición.
    stored = stored_messages(api)[-1]
    assert stored["role"] == "assistant"
    assert AVISO in stored["content"] and stored["content"] == assistant["content"]
    assert stored["metadata"]["anomaly_evidence"]["includes_synthetic_data"] is True
    assert stored["metadata"] == assistant["metadata"]
    assert reply["retrieved_context"] == []
