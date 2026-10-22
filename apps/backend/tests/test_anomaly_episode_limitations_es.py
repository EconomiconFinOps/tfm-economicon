"""JUP-134 (tareas 2.1): las limitaciones de un episodio de anomalía se leen en español y son una sola lista.

Antes del cambio, `LIMITATIONS` (episodio, API y panel) estaba en inglés y el asistente mantenía su propia
traducción `LIMITATIONS_ES`. El contrato nuevo (design.md D2, spec `cost-anomaly-episodes`) es:
- el episodio devuelve cinco frases en español, con la redacción y el orden de la traducción anterior;
- ninguna de las cinco frases en inglés anteriores reaparece;
- el asistente lista exactamente las mismas frases (una única fuente de verdad, sin `LIMITATIONS_ES`).

Convenciones:
- Las dos redacciones (español esperado e inglés prohibido) están copiadas LITERALES en este archivo: el
  código de producción nunca actúa como oráculo de su propio texto.
- El montaje del episodio y de la explicación reutiliza el de `test_anomaly_explanations.py`
  (`make_snapshot` -> `episode_payload`; `explain` -> `explain_episode`), sin base de datos ni red.
"""
import re

import pytest

from app.services.anomaly_episodes import LIMITATIONS
from test_anomaly_explanations import explain, load, make_snapshot
from test_tenant_isolation_api import api, call, headers
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from billing_support import billing_schema

# Redacción esperada, en el orden del episodio. Es la misma que `LIMITATIONS_ES_LITERAL` del contrato de la
# explicación (JUP-038); se repite aquí a propósito para que esta prueba no dependa de otro archivo de pruebas.
FRASES_EN_ESPANOL = [
    "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.",
    "No se verifica que los datos de coste estén completos; un día puede evaluarse antes de que lleguen registros tardíos.",
    "Un servicio sin gasto previo no abre anomalía su primer día; desde el segundo la referencia es la media de 7 días, "
    "que incluye ese primer día, así que un gasto nuevo y estable puede abrir una anomalía y escalar hasta que alguien la cierre.",
    "Los ciclos semanales pueden dar candidatas falsas y un pico reciente sube la media de 7 días.",
    "Solo se vigila el servicio; solo se evalúan EUR y USD, con umbrales nominales.",
]

# Las cinco frases en inglés que mostraba el panel antes de JUP-134 (copia literal del código anterior).
FRASES_EN_INGLES_ANTERIORES = [
    "A candidate for investigation, not a demonstrated cause, saving or statistical confidence.",
    "Cost data completeness is not verified; a day may be evaluated before late records arrive.",
    "A service with no earlier spend does not open an episode on its first day; from its second day the reference is the seven-day mean that includes that first day, so steady new spend can open an episode and escalate until someone closes it.",
    "Weekly cycles may produce false candidates and a recent spike raises the seven-day mean.",
    "Only the service dimension is watched; only EUR and USD are evaluated, with nominal thresholds.",
]

# Palabras funcionales exclusivamente inglesas (no existen en español): red de seguridad para detectar una
# frase nueva que se añada sin traducir, aunque no figure en `FRASES_EN_INGLES_ANTERIORES`.
PALABRAS_INGLESAS = {"the", "and", "is", "are", "may", "does", "with", "only", "from", "that", "of", "not", "for"}


def limitaciones_del_episodio():
    """Lee las limitaciones tal como las devuelve `episode_payload` (lectura de un episodio guardado)."""
    return make_snapshot()["episode"]["limitations"]


def test_un_episodio_leido_devuelve_las_cinco_limitaciones_en_espanol_y_en_orden():
    # Caso principal: la lectura de cualquier episodio trae la redacción en español exacta y en el orden del
    # contrato. Es lo que pinta el panel tal cual, así que el idioma se decide en el origen.
    assert limitaciones_del_episodio() == FRASES_EN_ESPANOL


def test_la_constante_de_origen_es_una_lista_de_cinco_frases_en_espanol():
    # `episode_payload` devuelve `list(LIMITATIONS)`: la fuente debe ser la lista de cinco frases en español.
    # Se comprueba también el tipo para no romper a quien la copie con `list(...)`.
    assert isinstance(LIMITATIONS, list)
    assert LIMITATIONS == FRASES_EN_ESPANOL


def test_ninguna_limitacion_es_una_de_las_frases_en_ingles_anteriores():
    # Regresión del defecto: el panel mostraba estas frases en inglés. Ninguna puede reaparecer, ni en la
    # constante ni en el episodio leído, y tampoco como subcadena de una frase nueva.
    leidas = limitaciones_del_episodio()
    for anterior in FRASES_EN_INGLES_ANTERIORES:
        assert anterior not in leidas
        assert anterior not in LIMITATIONS
        assert all(anterior not in frase for frase in leidas)


def test_no_queda_ninguna_frase_en_ingles_conocida():
    # Red de seguridad frente a una frase nueva sin traducir: ninguna limitación contiene como palabra completa
    # una palabra funcional inglesa. Complementa la lista cerrada de frases anteriores, que no detectaría una
    # frase inglesa distinta.
    for frase in limitaciones_del_episodio():
        palabras = set(re.findall(r"[a-záéíóúñ]+", frase.lower()))
        assert not (palabras & PALABRAS_INGLESAS), frase


def test_son_cinco_sin_duplicados_y_la_causa_sigue_sin_establecer():
    # Cardinalidad: exactamente cinco frases distintas y no vacías (el cambio de idioma no puede fusionar ni
    # perder ninguna). Se conserva `cause_status == "not_established"`: el episodio no afirma una causa.
    episode = make_snapshot()["episode"]
    assert len(episode["limitations"]) == 5
    assert len(set(episode["limitations"])) == 5
    assert all(frase.strip() for frase in episode["limitations"])
    assert episode["cause_status"] == "not_established"


def test_cada_lectura_devuelve_una_copia_y_no_la_lista_compartida():
    # Una lectura no debe poder alterar la fuente única: si el consumidor añade o cambia una frase en su
    # copia, la siguiente lectura (y el asistente) siguen viendo las cinco frases originales.
    primera = limitaciones_del_episodio()
    primera.append("intrusa")
    primera[0] = "alterada"
    assert limitaciones_del_episodio() == FRASES_EN_ESPANOL
    assert LIMITATIONS == FRASES_EN_ESPANOL


def test_el_asistente_lista_las_mismas_frases_que_el_episodio_y_en_el_mismo_orden():
    # Escenario «Mismas limitaciones en el panel y en el asistente»: se lee un episodio y se explica el mismo.
    # El texto (`- frase`, tras «Limitaciones:») y `anomaly_evidence.limitations` deben ser exactamente las
    # limitaciones del episodio, en su orden, para que el panel y el asistente no digan cosas distintas.
    snapshot = make_snapshot()
    del_episodio = snapshot["episode"]["limitations"]
    resultado = explain(snapshot)
    lineas = resultado["content"].split("\n")
    inicio = lineas.index("Limitaciones:")
    viñetas = [linea for linea in lineas if linea.startswith("- ")]
    assert viñetas == [f"- {frase}" for frase in del_episodio]
    assert lineas[inicio + 1:inicio + 1 + len(viñetas)] == viñetas
    assert resultado["anomaly_evidence"]["limitations"] == del_episodio
    assert del_episodio == FRASES_EN_ESPANOL
    assert resultado["anomaly_evidence"]["cause_status"] == "not_established"


def test_la_evidencia_conserva_las_limitaciones_en_espanol_dentro_de_la_fotografia_del_episodio():
    # La fotografía del episodio incluida en la evidencia lleva las mismas frases en español: ya no hay una
    # versión en inglés dentro y otra en español fuera (design.md, «Riesgos»: el identificador cambia una vez).
    evidencia = explain(make_snapshot())["anomaly_evidence"]
    assert evidencia["episode"]["limitations"] == FRASES_EN_ESPANOL
    assert evidencia["limitations"] == evidencia["episode"]["limitations"]


def test_el_modulo_de_explicaciones_ya_no_define_su_propia_lista():
    # Fuente única de verdad (design.md D2): `LIMITATIONS_ES` desaparece del módulo del asistente, que usa
    # `LIMITATIONS` del episodio. Si reaparece, habría de nuevo dos listas que podrían divergir sin que
    # nada fallara.
    modulo = load()
    assert not hasattr(modulo, "LIMITATIONS_ES")
    assert modulo.LIMITATIONS is LIMITATIONS


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_la_api_de_lectura_de_un_episodio_devuelve_las_limitaciones_en_espanol(api, monkeypatch):
    # Camino HTTP: GET /billing/anomalies/episodes/{id} serializa el episodio con el esquema de respuesta.
    # El almacén (frontera de I/O) se sustituye por el payload real de `episode_payload`; así se comprueba que
    # el texto en español llega intacto al cliente que lo pinta (el panel), sin traducción posterior.
    episodio = make_snapshot()["episode"]
    monkeypatch.setattr(api.db, "fetch_anomaly_episode", lambda tenant_id, episode_id: episodio)
    respuesta = call(api, "GET", f"/billing/anomalies/episodes/{episodio['id']}", headers=headers())
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["limitations"] == FRASES_EN_ESPANOL
    assert cuerpo["cause_status"] == "not_established"
    assert not set(FRASES_EN_INGLES_ANTERIORES) & set(cuerpo["limitations"])
