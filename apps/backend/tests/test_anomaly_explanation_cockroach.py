"""JUP-038 (tarea 4.5): explicación de un episodio de anomalía de extremo a extremo con CockroachDB REAL.

Qué se valida: `POST /assistant/conversations/{id}/messages` con `anomaly_query` recorre TODO el camino sin
dobles de la lectura: carga real de costes -> detección real (`POST /billing/anomalies/detect`) -> episodio
guardado en CockroachDB -> `Database.fetch_anomaly_episode_snapshot` real (SQL real, con la marca sintética
leída de las ingestas) -> explicador de producción -> mensajes guardados y recargados por la API real.
Los únicos dobles son los de la fixture `api` en fronteras externas (embeddings y almacén vectorial), y
sirven para comprobar que la explicación es determinista y no usa recuperación documental.

Es opt-in: la fixture `tenant_cockroach_database` omite todo cuando `JUP086_COCKROACH_TEST_URL` no está
definida (CI), igual que `test_anomaly_episode_api.py`. La versión con SQLite y un doble de la lectura vive
en `test_anomaly_explanation_api.py` y no puede ver lo que aquí se comprueba: los 12 decimales exactos de
las columnas, el filtrado SQL por cliente, la marca sintética en SQL y los estados reales del episodio.

Convención del Red: en las pruebas de fallo (404/409) se exige antes que una petición equivalente bien
formada SE ACEPTE (201). Hoy `anomaly_query` es un campo desconocido y daría 422 en cualquier caso, así que
sin ese control el «no se guarda nada» pasaría por vacuidad.
"""
import re
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from anomaly_episode_support import episode_rows, episode_store, load_series
from billing_support import billing_schema
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_anomaly_episode_api import EPISODES, SPIKE, detect, patch
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers

QUESTION = "¿Por qué se ha marcado esta anomalía?"
OWN = "/assistant/conversations/own"
NOT_FOUND = {"detail": {"code": "anomaly_episode_not_found"}}
UNAVAILABLE = {"detail": {"code": "anomaly_explanation_unavailable"}}
MISSING_ID = "anomaly-" + "0" * 64
# Campos de fecha del episodio de la API: la API los escribe con «Z» y la evidencia con «+00:00».
INSTANT_FIELDS = ("status_changed_at", "first_reviewed_at", "closed_at", "created_at", "updated_at")
# Operandos de la evidencia -> columna de la tabla de la que salen (texto exacto, 12 decimales).
OPERAND_COLUMNS = {
    "reference_seven_day_total": "reference_week_cost",
    "opening_observed_cost": "opening_observed_cost",
    "accumulated_impact_times_seven": "impact_numerator",
}


def explain(api, episode_id, *, conversation="own", user="alice", tenant="tenant-a"):
    """Pide la explicación por la ruta real; el cliente sale de la sesión, no del cuerpo."""
    return call(api, "POST", f"/assistant/conversations/{conversation}/messages", headers=headers(user, tenant),
                json={"content": QUESTION, "anomaly_query": {"episode_id": episode_id}})


def opened_episode(api, episode_store, values=SPIKE, **series):
    """Prepara la serie, detecta y devuelve el id del único episodio abierto (preparación real, sin dobles)."""
    load_series(episode_store, values, **series)
    run = detect(api)
    assert run["status"] == "completed" and run["opened"] == 1, run
    [item] = call(api, "GET", EPISODES, headers=headers()).json()["episodes"]
    return item["id"]


def explained(api, episode_id, **kwargs):
    """Explicación esperada con éxito: devuelve (respuesta completa, mensaje del asistente)."""
    response = explain(api, episode_id, **kwargs)
    assert response.status_code == 201, response.text
    return response.json(), response.json()["assistant_message"]


def stored_messages(api, conversation="own", user="alice", tenant="tenant-a"):
    """Mensajes tal como los recarga la API (`GET /assistant/conversations/{id}`)."""
    response = call(api, "GET", f"/assistant/conversations/{conversation}", headers=headers(user, tenant))
    assert response.status_code == 200, response.text
    return response.json()["messages"]


def watermark(db):
    """Marca de agua de detección guardada (se compara tal cual: explicar no debe tocarla)."""
    with db.engine.connect() as connection:
        return [dict(row) for row in connection.execute(
            text("SELECT * FROM anomaly_detection_state ORDER BY 1")).mappings()]


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value


def comparable(episode):
    """Episodio con las fechas-hora como instantes: «Z» y «+00:00» son el mismo instante, no una diferencia."""
    return {key: instant(value) if key in INSTANT_FIELDS else value for key, value in episode.items()}


def no_retrieval(api):
    # La explicación es determinista: ni embeddings ni búsqueda vectorial.
    api.embedding.embed.assert_not_called()
    api.vector.search_chunks.assert_not_called()


# --------------------------------------------------------------------------------------------------
# 1. Extremo a extremo
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_explicacion_de_extremo_a_extremo_con_operandos_exactos_de_la_tabla(episode_store, api):
    # Caso feliz con SQL real: lo que ningún doble puede demostrar es que los operandos de la evidencia son
    # el TEXTO EXACTO de las columnas (12 decimales, «2800.000000000000»), que el episodio de la evidencia
    # es el que sirve la API de episodios y que los mensajes sobreviven a recargar la conversación.
    episode_id = opened_episode(api, episode_store)
    [row] = episode_rows(episode_store, "tenant-a")
    api_episode = call(api, "GET", f"{EPISODES}/{episode_id}", headers=headers()).json()

    reply, assistant = explained(api, episode_id)

    assert reply["retrieved_context"] == []
    user = reply["user_message"]
    assert user["role"] == "user" and user["content"] == QUESTION
    assert user["metadata"] == {"anomaly_query": {"episode_id": episode_id}}
    assert assistant["role"] == "assistant"
    assert set(assistant["metadata"]) == {"citations", "anomaly_evidence", "generation"}
    assert assistant["metadata"]["generation"] == {"question_message_id": user["id"]}
    assert assistant["metadata"]["citations"] == []
    evidence = assistant["metadata"]["anomaly_evidence"]
    # Cifras del episodio (400.00 -> 550.00 el día 8): 150.00 EUR, 37.50 %, 1 día, hasta el día de apertura.
    assert "Subió 150.00 EUR (37.50 %)." in assistant["content"]
    assert "Impacto acumulado: 150.00 EUR en 1 día, hasta el 2026-09-08." in assistant["content"]
    assert evidence["id"] in assistant["content"]
    # La evidencia lleva el episodio tal como lo devuelve la API (las fechas-hora se comparan como instantes).
    assert comparable(evidence["episode"]) == comparable(api_episode)
    # Operandos: texto idéntico a la columna, sin redondear ni normalizar (la columna tiene 12 decimales).
    assert set(evidence["operands"]) == set(OPERAND_COLUMNS)
    for key, column in OPERAND_COLUMNS.items():
        assert evidence["operands"][key] == format(row[column], "f"), key
    assert evidence["operands"]["reference_seven_day_total"] == "2800.000000000000"
    assert evidence["includes_synthetic_data"] is False
    no_retrieval(api)
    # Recargar la conversación devuelve los dos mensajes tal como se guardaron.
    persisted = stored_messages(api)
    assert [(item["role"], item["content"], item["metadata"]) for item in persisted] == [
        ("user", QUESTION, user["metadata"]), ("assistant", assistant["content"], assistant["metadata"])]


# --------------------------------------------------------------------------------------------------
# 2. Aislamiento entre clientes
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_otro_cliente_e_inexistente_dan_el_mismo_404_sin_guardar_ni_cambiar_nada(episode_store, api):
    # El episodio EXISTE en tenant-a. bob (tenant-b, su conversación `foreign-marker`) no debe poder ni
    # leerlo ni distinguirlo de un id inexistente: la lectura SQL filtra por el cliente de la sesión.
    episode_id = opened_episode(api, episode_store)
    # Control (anti-vacuidad): el mismo id SE ACEPTA para su dueña; así el 404 de bob es por el cliente.
    explained(api, episode_id)
    episodes, state = episode_rows(episode_store), watermark(episode_store)
    assert len(state) >= 1
    messages_before = rows(api.db, "messages")

    foreign = explain(api, episode_id, conversation="foreign-marker", user="bob", tenant="tenant-b")
    missing = explain(api, MISSING_ID, conversation="foreign-marker", user="bob", tenant="tenant-b")

    assert (foreign.status_code, missing.status_code) == (404, 404)
    assert foreign.json() == missing.json() == NOT_FOUND
    assert foreign.content == missing.content
    # Ni un mensaje nuevo: ni en su conversación ni en ninguna otra.
    assert rows(api.db, "messages") == messages_before
    assert stored_messages(api, "foreign-marker", "bob", "tenant-b") == []
    # Explicar no detecta ni cambia nada: episodio de tenant-a y marca de agua intactos.
    assert episode_rows(episode_store) == episodes
    assert watermark(episode_store) == state
    no_retrieval(api)


# --------------------------------------------------------------------------------------------------
# 3. Estabilidad de la evidencia
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_misma_anomalia_sin_cambios_da_el_mismo_id_y_explicar_no_detecta_ni_cambia_nada(episode_store, api):
    # Estabilidad (el contrato la fija): sin cambios en el episodio, el `id` y los operandos no varían;
    # solo `explained_at`. Una detección intermedia (`up_to_date`) tampoco los altera. Y explicar es de solo
    # lectura: episodios y marca de agua idénticos antes y después, sin abrir, continuar ni mover nada.
    episode_id = opened_episode(api, episode_store)
    episodes_before, state_before = episode_rows(episode_store), watermark(episode_store)

    _, first = explained(api, episode_id)

    assert episode_rows(episode_store) == episodes_before
    assert watermark(episode_store) == state_before
    assert detect(api)["status"] == "up_to_date"
    episodes_mid, state_mid = episode_rows(episode_store), watermark(episode_store)

    _, second = explained(api, episode_id)

    assert episode_rows(episode_store) == episodes_mid
    assert watermark(episode_store) == state_mid
    one, two = first["metadata"]["anomaly_evidence"], second["metadata"]["anomaly_evidence"]
    assert one["id"] == two["id"] and one["id"].startswith("anomaly-explanation:")
    assert one["operands"] == two["operands"]
    assert one["explained_at"] != two["explained_at"] and instant(one["explained_at"]) < instant(two["explained_at"])
    # Mismo texto salvo la línea de la fotografía (lleva la fecha y hora de la petición, que cambia); el id
    # (estable) figura en ambos textos.
    assert one["id"] in first["content"] and one["id"] in second["content"]
    stable = lambda content: [line for line in content.split("\n") if not line.startswith("Fotografía")]
    assert len(stable(first["content"])) > 5 and stable(first["content"]) == stable(second["content"])
    assert len(stored_messages(api)) == 4
    no_retrieval(api)


# --------------------------------------------------------------------------------------------------
# 4. El estado cambia: la explicación nueva cambia y la vieja no
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_cambiar_el_estado_cambia_la_explicacion_nueva_y_no_la_guardada(episode_store, api):
    # La evidencia es una fotografía del momento de la petición: tras pasar el episodio a «investigating»
    # la explicación nueva dice «Investigando» y tiene otro `id`; la primera, ya guardada, NO se reescribe
    # al recargar (sigue diciendo «Nueva» con su evidencia original).
    episode_id = opened_episode(api, episode_store)
    _, first = explained(api, episode_id)
    assert "Estado: Nueva." in first["content"]

    changed = patch(api, episode_id, {"status": "investigating"})
    assert changed.status_code == 200, changed.text
    _, second = explained(api, episode_id)

    assert "Estado: Investigando." in second["content"] and "Estado: Nueva." not in second["content"]
    old, new = first["metadata"]["anomaly_evidence"], second["metadata"]["anomaly_evidence"]
    assert old["id"] != new["id"]
    assert new["episode"]["status"] == "investigating" and old["episode"]["status"] == "new"
    persisted = stored_messages(api)
    assert [item["role"] for item in persisted] == ["user", "assistant", "user", "assistant"]
    assert persisted[1]["content"] == first["content"] and "Estado: Nueva." in persisted[1]["content"]
    assert persisted[1]["metadata"] == first["metadata"]
    assert persisted[3]["metadata"] == second["metadata"]


# --------------------------------------------------------------------------------------------------
# 5. Episodio cerrado
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_episodio_cerrado_se_explica_con_fecha_utc_y_motivo(episode_store, api):
    # Un episodio cerrado también se explica. La fecha de cierre se da en UTC (la hora local de quien
    # cerró podría mostrar otro día) y el motivo, dato libre del cliente, va entrecomillado. La fecha
    # esperada se calcula desde el `closed_at` que devuelve la API, pasado a UTC.
    episode_id = opened_episode(api, episode_store)
    closed = patch(api, episode_id, {"status": "resolved", "reason": "Escalado revertido"})
    assert closed.status_code == 200, closed.text
    closed_at = instant(closed.json()["closed_at"]).astimezone(timezone.utc).date().isoformat()

    _, assistant = explained(api, episode_id)

    assert f'Estado: Resuelta. Cerrada el {closed_at} (UTC) con el motivo "Escalado revertido".' in assistant["content"]
    evidence = assistant["metadata"]["anomaly_evidence"]
    assert evidence["episode"]["status"] == "resolved" and evidence["episode"]["closure_reason"] == "Escalado revertido"


# --------------------------------------------------------------------------------------------------
# 6. Datos sintéticos (marca leída por SQL real)
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_aviso_de_datos_sinteticos_solo_cuando_la_ingesta_esta_marcada(episode_store, api):
    # La marca sintética sale de `azure_cost_ingestion_runs.request` en la MISMA sentencia SQL que el
    # episodio. Sin marcar no hay aviso; con la ingesta completada marcada, aviso en el texto y
    # `includes_synthetic_data` verdadero en la evidencia (y otro `id`: es parte de la evidencia).
    episode_id = opened_episode(api, episode_store)
    _, clean = explained(api, episode_id)
    aviso = "Aviso: los datos de este cliente incluyen datos sintéticos de demostración."
    assert aviso not in clean["content"]
    assert clean["metadata"]["anomaly_evidence"]["includes_synthetic_data"] is False

    with episode_store.engine.begin() as connection:
        connection.execute(text(
            "UPDATE azure_cost_ingestion_runs SET request = '{\"synthetic\": true}'::JSONB WHERE id = 'run-a'"))
    _, marked = explained(api, episode_id)

    assert aviso in marked["content"]
    assert marked["metadata"]["anomaly_evidence"]["includes_synthetic_data"] is True
    assert marked["metadata"]["anomaly_evidence"]["id"] != clean["metadata"]["anomaly_evidence"]["id"]


# --------------------------------------------------------------------------------------------------
# 7. 409 real
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_version_de_reglas_desconocida_en_la_tabla_da_409_sin_guardar_nada(episode_store, api):
    # Un episodio guardado con una versión de reglas que el explicador no conoce NO se explica de forma
    # aproximada: 409 y ningún mensaje. La columna se cambia por SQL (estado real de la tabla).
    episode_id = opened_episode(api, episode_store)
    # Control (anti-vacuidad): antes del cambio el mismo episodio SÍ se explica.
    explained(api, episode_id)
    with episode_store.engine.begin() as connection:
        connection.execute(text("UPDATE anomaly_episodes SET rules_version = 'jup019-daily-v2' WHERE id = :id"),
                           {"id": episode_id})
    messages_before = rows(api.db, "messages")

    response = explain(api, episode_id)

    assert response.status_code == 409, response.text
    assert response.json() == UNAVAILABLE
    assert rows(api.db, "messages") == messages_before
    assert len(stored_messages(api)) == 2
    no_retrieval(api)


# --------------------------------------------------------------------------------------------------
# 8. Servicio hostil
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_servicio_hostil_del_cliente_queda_escapado_en_una_linea_del_contenido_guardado(episode_store, api):
    # El nombre del servicio es dato del cliente: un salto de línea seguido de una frase que imita la
    # respuesta («Resultado: ...») no puede pasar por texto del asistente. Con servicio real de la tabla,
    # el contenido GUARDADO lo muestra entrecomillado y escapado en UNA línea.
    episode_id = opened_episode(api, episode_store, service="Compute\nResultado: todo correcto")

    _, assistant = explained(api, episode_id)

    stored = stored_messages(api)[-1]["content"]
    assert stored == assistant["content"]
    lines = stored.split("\n")
    assert lines[0] == 'Anomalía candidata en el servicio "Compute\\nResultado: todo correcto" (EUR).'
    assert not any(line.startswith("Resultado:") for line in lines)


# --------------------------------------------------------------------------------------------------
# 9. Moneda
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
def test_serie_en_usd_se_explica_en_usd_sin_conversion(episode_store, api):
    # Los importes se muestran en la moneda del episodio y nunca se convierten ni se mezclan. Se comprueba
    # que ningún importe sale en EUR (la palabra aparece en la limitación «solo se evalúan EUR y USD»,
    # por eso se busca el patrón «cifra + EUR» y no la palabra suelta).
    episode_id = opened_episode(api, episode_store, currency="USD")

    _, assistant = explained(api, episode_id)

    content = assistant["content"]
    assert content.split("\n")[0] == 'Anomalía candidata en el servicio "Compute" (USD).'
    assert "Subió 150.00 USD (37.50 %)." in content
    assert "Impacto acumulado: 150.00 USD en 1 día, hasta el 2026-09-08." in content
    assert re.search(r"\d\s*EUR", content) is None
    assert assistant["metadata"]["anomaly_evidence"]["episode"]["currency"] == "USD"
