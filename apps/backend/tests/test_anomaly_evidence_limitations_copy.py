"""JUP-134 (remediación de mutación): la evidencia del asistente no comparte la lista global de limitaciones.

Contexto del mutante superviviente: en `anomaly_explanations.py` la evidencia se arma con
`"limitations": list(LIMITATIONS)`. Si se cambia por `"limitations": LIMITATIONS`, la evidencia devuelta es
el MISMO objeto que la fuente única (`app.services.anomaly_episodes.LIMITATIONS`). Entonces quien mute la
evidencia (`append`, asignación por índice) alteraría la fuente para todas las explicaciones y episodios
siguientes. Antes del cambio de idioma la fuente era una tupla (inmutable); ahora es una lista, y `list()` es
lo único que evita el alias.

Convenciones:
- Las cinco frases esperadas se repiten LITERALES aquí para que el archivo sea autónomo y el código de
  producción no actúe como oráculo de su propio texto.
- Montaje reutilizado de `test_anomaly_explanations.py` (`make_snapshot`, `explain`), sin base de datos ni red.
"""
from app.services.anomaly_episodes import LIMITATIONS
from test_anomaly_explanations import explain, make_snapshot

FRASES_EN_ESPANOL = [
    "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.",
    "No se verifica que los datos de coste estén completos; un día puede evaluarse antes de que lleguen registros tardíos.",
    "Un servicio sin gasto previo no abre anomalía su primer día; desde el segundo la referencia es la media de 7 días, "
    "que incluye ese primer día, así que un gasto nuevo y estable puede abrir una anomalía y escalar hasta que alguien la cierre.",
    "Los ciclos semanales pueden dar candidatas falsas y un pico reciente sube la media de 7 días.",
    "Solo se vigila el servicio; solo se evalúan EUR y USD, con umbrales nominales.",
]


def test_la_evidencia_lleva_una_copia_de_las_cinco_frases_y_no_la_lista_global():
    # Identidad y valor a la vez: la evidencia debe valer lo mismo que la fuente única (cinco frases en
    # español) pero ser otro objeto. Comprobar solo la igualdad dejaría pasar el alias compartido.
    limitaciones = explain(make_snapshot())["anomaly_evidence"]["limitations"]
    assert limitaciones is not LIMITATIONS
    assert limitaciones == FRASES_EN_ESPANOL


def test_mutar_la_lista_de_la_evidencia_no_altera_la_fuente_ni_otras_explicaciones():
    # Si la evidencia compartiera la lista global, añadir o reasignar una frase en la copia del consumidor
    # contaminaría la fuente única y, con ella, cualquier explicación posterior del mismo snapshot (tanto la
    # evidencia como el texto en viñetas que se genera a partir de la misma fuente).
    snapshot = make_snapshot()
    primera = explain(snapshot)
    primera["anomaly_evidence"]["limitations"].append("intrusa")
    primera["anomaly_evidence"]["limitations"][0] = "alterada"

    assert LIMITATIONS == FRASES_EN_ESPANOL
    segunda = explain(snapshot)
    assert segunda["anomaly_evidence"]["limitations"] == FRASES_EN_ESPANOL
    assert "intrusa" not in segunda["content"]
    assert "alterada" not in segunda["content"]
    viñetas = [linea for linea in segunda["content"].split("\n") if linea.startswith("- ")]
    assert viñetas == [f"- {frase}" for frase in FRASES_EN_ESPANOL]


def test_mutar_las_limitaciones_de_la_fotografia_del_episodio_no_altera_la_fuente():
    # Mismo riesgo en el segundo nivel: `anomaly_evidence["episode"]["limitations"]` es la fotografía del
    # episodio. Mutarla no puede alterar `LIMITATIONS` ni la fotografía de una explicación posterior.
    snapshot = make_snapshot()
    fotografia = explain(snapshot)["anomaly_evidence"]["episode"]["limitations"]
    assert fotografia is not LIMITATIONS
    fotografia.append("intrusa")
    fotografia[0] = "alterada"

    assert LIMITATIONS == FRASES_EN_ESPANOL
    assert explain(snapshot)["anomaly_evidence"]["episode"]["limitations"] == FRASES_EN_ESPANOL
