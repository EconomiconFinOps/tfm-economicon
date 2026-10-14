"""JUP-038 (tareas 2.1 a 2.4): explicador puro de un episodio de anomalía de coste guardado.

El módulo bajo prueba (`app.services.anomaly_explanations`) no depende de la base de datos, de HTTP ni
de los registros. Recibe la fotografía del episodio (lo que devuelve `episode_payload` sin `_order`,
los operandos exactos y la marca sintética) y devuelve el texto en español y la evidencia.

Convenciones de este archivo:
- Todas las cifras esperadas están calculadas a mano con aritmética exacta (ver el ejemplo del
  contrato `docs/api/anomaly-explanations.md`); el código de producción nunca actúa como oráculo.
- El módulo se importa dentro de cada prueba (`load`) para que, mientras no exista, falle cada prueba
  por separado y no un único error de colección.
"""
import copy
import hashlib
import importlib
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.anomaly_episodes import LIMITATIONS, RULES, RULES_VERSION, episode_payload

UTC = timezone.utc
EXPLAINED_AT = datetime(2026, 10, 12, 18, 30, tzinfo=UTC)
EPISODE_ID = "anomaly-" + "a" * 64
PREVIOUS_ID = "anomaly-" + "b" * 64
OPENED = date(2026, 9, 8)

# Redacción en español esperada de las cinco limitaciones de `LIMITATIONS`, en el mismo orden.
LIMITATIONS_ES_LITERAL = [
    "Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.",
    "No se verifica que los datos de coste estén completos; un día puede evaluarse antes de que lleguen registros tardíos.",
    "Un servicio sin gasto previo no abre anomalía su primer día; desde el segundo la referencia es la media de 7 días, "
    "que incluye ese primer día, así que un gasto nuevo y estable puede abrir una anomalía y escalar hasta que alguien la cierre.",
    "Los ciclos semanales pueden dar candidatas falsas y un pico reciente sube la media de 7 días.",
    "Solo se vigila el servicio; solo se evalúan EUR y USD, con umbrales nominales.",
]
BULLETS = [f"- {text}" for text in LIMITATIONS_ES_LITERAL]
SCOPE_LINE = "Alcance: esta explicación cubre el día de apertura y los acumulados; no hay detalle día a día."
SYNTHETIC_LINE = "Aviso: los datos de este cliente incluyen datos sintéticos de demostración."
CAUSE_LINE = "Causa no establecida: es un candidato para investigar, no una causa demostrada ni un ahorro."
RULE_LINE = ("Regla jup019-daily-v1: un día se marca solo si supera la referencia en más de 100.00 EUR y en más de "
             "un 20 %, las dos condiciones a la vez. Este día cumple las dos.")
WHY_PREFIX = "Por qué se marcó: el 2026-09-08 el coste observado fue "
WHY_MIDDLE = " EUR al día (media de los 7 días anteriores a la apertura). Subió "

# Posiciones fijas de las líneas del ejemplo A (las que no dependen de notas ni de avisos opcionales).
IDX_SERVICE, IDX_WHY, IDX_RULE, IDX_IMPACT, IDX_STATE = 0, 1, 2, 3, 4

NOTE_ABSOLUTE = ("Nota de redondeo: la subida absoluta exacta supera el umbral de 100.00 EUR aunque la cifra mostrada, "
                 "redondeada a dos decimales, coincida con él.")
NOTE_RELATIVE = ("Nota de redondeo: la subida relativa exacta supera el umbral del 20 % aunque la cifra mostrada, "
                 "redondeada a dos decimales, coincida con él.")
NOTE_IMPACT_BELOW = ("Nota de redondeo: el impacto acumulado exacto queda por debajo de 500.00 EUR aunque la cifra mostrada, "
                     "redondeada a dos decimales, coincida con ese límite.")
NOTE_IMPACT_ABOVE = ("Nota de redondeo: el impacto acumulado exacto queda por encima de 2000.00 EUR aunque la cifra mostrada, "
                     "redondeada a dos decimales, coincida con ese límite.")

LABEL_P1 = "Alta (P1), por encima de 2000.00 EUR"
LABEL_P2 = "Media (P2), entre 500.00 y 2000.00 EUR, ambos incluidos"
LABEL_P3 = "Baja (P3), por debajo de 500.00 EUR"


def load():
    """Importa el explicador en el momento de usarlo (ver el docstring del módulo)."""
    return importlib.import_module("app.services.anomaly_explanations")


def make_snapshot(*, reference="2800.00", observed="550.00", numerator="2800.00", days=2, start=OPENED,
                  through=date(2026, 9, 9), currency="EUR", service="Compute", status="new",
                  observation="observed", no_longer_observed_on=None, closed_at=None, closure_reason=None,
                  previous=None, rules_version=RULES_VERSION, rules=None, synthetic=False):
    """Arma la fotografía igual que la lectura del backend: fila -> `episode_payload` sin `_order`."""
    row = {
        "id": EPISODE_ID, "currency": currency, "service": service, "start_date": start, "last_seen_date": through,
        "observation": observation, "no_longer_observed_on": no_longer_observed_on,
        "reference_week_cost": Decimal(reference), "opening_observed_cost": Decimal(observed),
        "impact_numerator": Decimal(numerator), "impact_day_count": days, "impact_through_date": through,
        "status": status, "previous_episode_id": previous, "rules_version": rules_version,
        "rules": rules if rules is not None else json.loads(json.dumps(RULES)),
        "status_changed_by": None, "status_changed_at": None, "first_reviewed_at": None, "first_reviewed_by": None,
        "closed_at": closed_at, "closure_reason": closure_reason,
        "created_at": datetime(2026, 9, 10, 3, 0, tzinfo=UTC), "updated_at": datetime(2026, 9, 10, 3, 0, tzinfo=UTC),
    }
    episode = episode_payload(row)
    episode.pop("_order")
    return {
        "episode": episode,
        "operands": {"reference_week_cost": Decimal(reference), "opening_observed_cost": Decimal(observed),
                     "impact_numerator": Decimal(numerator)},
        "includes_synthetic_data": synthetic,
    }


def explain(snapshot, *, tenant="tenant-a", at=EXPLAINED_AT):
    return load().explain_episode(snapshot, tenant_id=tenant, explained_at=at)


def lines_a(evidence_id):
    """Texto del ejemplo A del contrato (Compute, EUR, 2 días, P3), una cadena por línea."""
    return [
        'Anomalía candidata en el servicio "Compute" (EUR).',
        WHY_PREFIX + "550.00 EUR frente a una referencia de 400.00" + WHY_MIDDLE + "150.00 EUR (37.50 %).",
        RULE_LINE,
        f"Impacto acumulado: 400.00 EUR en 2 días, hasta el 2026-09-09. Criticidad: {LABEL_P3}.",
        "Estado: Nueva. Se sigue observando.",
        CAUSE_LINE,
        "Limitaciones:",
        *BULLETS,
        SCOPE_LINE,
        "Fotografía tomada el 2026-10-12T18:30:00+00:00 (UTC).",
        f"Evidencia: {evidence_id}.",
    ]


def recompute_id(evidence, tenant):
    """Recalcula el identificador por su cuenta, sin importar nada de producción."""
    body = {key: value for key, value in evidence.items() if key not in ("id", "explained_at")}
    raw = json.dumps({"tenant": tenant, **body}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "anomaly-explanation:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def rules_with(**changes):
    rules = json.loads(json.dumps(RULES))
    rules.update(changes)
    return rules


# --------------------------------------------------------------------------------------------------
# 2.1 Texto y cifras del día de apertura
# --------------------------------------------------------------------------------------------------

def test_ejemplo_a_texto_completo_coincide_con_el_literal_del_contrato():
    # Comportamiento base: el texto completo es exactamente el del contrato (cifras exactas, umbrales,
    # versión, causa no establecida, limitaciones, alcance, fotografía y evidencia), sin línea final en blanco.
    result = explain(make_snapshot())
    assert set(result) == {"content", "anomaly_evidence"}
    assert result["content"].split("\n") == lines_a(result["anomaly_evidence"]["id"])
    assert not result["content"].endswith("\n")


def test_ejemplo_a_evidencia_completa():
    # La evidencia lleva todas las claves del contrato con los valores calculados a mano del ejemplo A.
    evidence = explain(make_snapshot())["anomaly_evidence"]
    expected_episode = {
        "id": EPISODE_ID, "kind": "cost_anomaly_candidate", "currency": "EUR", "service": "Compute",
        "start_date": "2026-09-08", "last_seen_date": "2026-09-09", "observation": "observed",
        "no_longer_observed_on": None, "reference_daily_cost": "400.00", "opening_observed_cost": "550.00",
        "accumulated_impact": "400.00", "impact_day_count": 2, "impact_through_date": "2026-09-09",
        "severity": "P3", "status": "new", "status_changed_by": None, "status_changed_at": None,
        "first_reviewed_at": None, "first_reviewed_by": None, "closed_at": None, "closure_reason": None,
        "previous_episode_id": None, "rules_version": "jup019-daily-v1",
        "rules": {"relative_increase_percent": "20", "absolute_increase": "100.00", "reference_days": 7,
                  "tolerance_days": 3, "severity": {"P1": "> 2000.00", "P2": "500.00 to 2000.00", "P3": "< 500.00"},
                  "currencies": ["EUR", "USD"]},
        "cause_status": "not_established", "limitations": list(LIMITATIONS),
        "created_at": "2026-09-10T03:00:00+00:00", "updated_at": "2026-09-10T03:00:00+00:00",
    }
    assert {key: value for key, value in evidence.items() if key != "id"} == {
        "schema_version": "1.0", "adapter_version": "anomaly-explanation-1.0", "status": "ok",
        "source": {"kind": "anomaly_episodes", "rules_version": "jup019-daily-v1", "data_as_of": "2026-09-09"},
        "episode": expected_episode,
        "operands": {"reference_seven_day_total": "2800.00", "opening_observed_cost": "550.00",
                     "accumulated_impact_times_seven": "2800.00"},
        "opening": {"reference_daily_cost": "400.00", "observed_cost": "550.00", "absolute_increase": "150.00",
                    "relative_increase_percent": "37.50", "absolute_threshold": "100.00",
                    "relative_threshold_percent": "20", "conditions_met": True},
        "impact": {"accumulated_impact": "400.00", "day_count": 2, "through_date": "2026-09-09",
                   "severity": "P3", "severity_band": "< 500.00"},
        "rounding_notes": [], "includes_synthetic_data": False, "cause_status": "not_established",
        "assumptions": [], "limitations": LIMITATIONS_ES_LITERAL, "explained_at": "2026-10-12T18:30:00+00:00",
    }


def test_borde_b_subida_absoluta_exacta_supera_el_umbral_aunque_se_muestre_igual():
    # R=2800.00, O=500.004: subida exacta 100.004 (> 100) pero se muestra 100.00. Restar importes ya
    # redondeados daría "100.00, que no supera 100": el texto debe aclararlo con la nota de redondeo.
    result = explain(make_snapshot(reference="2800.00", observed="500.004", numerator="700.028", days=1,
                                   through=OPENED))
    lines = result["content"].split("\n")
    assert lines[IDX_WHY] == (WHY_PREFIX + "500.00 EUR frente a una referencia de 400.00" + WHY_MIDDLE
                              + "100.00 EUR (25.00 %).")
    assert lines[IDX_IMPACT] == f"Impacto acumulado: 100.00 EUR en 1 día, hasta el 2026-09-08. Criticidad: {LABEL_P3}."
    assert lines[IDX_IMPACT + 1] == NOTE_ABSOLUTE
    assert lines[IDX_IMPACT + 2] == "Estado: Nueva. Se sigue observando."
    evidence = result["anomaly_evidence"]
    assert evidence["rounding_notes"] == ["absolute_increase"]
    assert evidence["operands"] == {"reference_seven_day_total": "2800.00", "opening_observed_cost": "500.004",
                                    "accumulated_impact_times_seven": "700.028"}
    assert evidence["opening"]["absolute_increase"] == "100.00"
    assert evidence["opening"]["relative_increase_percent"] == "25.00"


def test_borde_c_subida_relativa_exacta_supera_el_umbral_aunque_se_muestre_igual():
    # R=7000.00, O=1200.002: la subida relativa exacta es 20.0002 % (> 20) y se muestra 20.00 %.
    result = explain(make_snapshot(reference="7000.00", observed="1200.002", numerator="1400.014", days=1,
                                   through=OPENED))
    lines = result["content"].split("\n")
    assert lines[IDX_WHY] == (WHY_PREFIX + "1200.00 EUR frente a una referencia de 1000.00" + WHY_MIDDLE
                              + "200.00 EUR (20.00 %).")
    assert lines[IDX_IMPACT] == f"Impacto acumulado: 200.00 EUR en 1 día, hasta el 2026-09-08. Criticidad: {LABEL_P3}."
    assert lines[IDX_IMPACT + 1] == NOTE_RELATIVE
    assert lines[IDX_IMPACT + 2] == "Estado: Nueva. Se sigue observando."
    assert result["anomaly_evidence"]["rounding_notes"] == ["relative_increase"]
    assert result["anomaly_evidence"]["opening"]["relative_increase_percent"] == "20.00"


def test_ambos_bordes_a_la_vez_dan_las_dos_notas_en_orden_absoluta_y_relativa():
    # R=3500.00, O=600.002: subida 100.002 (se muestra 100.00) y 20.0004 % (se muestra 20.00 %).
    # Se comprueba el orden fijo de las notas: primero la absoluta y después la relativa.
    result = explain(make_snapshot(reference="3500.00", observed="600.002", numerator="700.014", days=1,
                                   through=OPENED))
    lines = result["content"].split("\n")
    assert lines[IDX_WHY] == (WHY_PREFIX + "600.00 EUR frente a una referencia de 500.00" + WHY_MIDDLE
                              + "100.00 EUR (20.00 %).")
    assert lines[IDX_IMPACT + 1:IDX_IMPACT + 4] == [NOTE_ABSOLUTE, NOTE_RELATIVE, "Estado: Nueva. Se sigue observando."]
    assert result["anomaly_evidence"]["rounding_notes"] == ["absolute_increase", "relative_increase"]


def test_sin_redondeo_conflictivo_no_hay_notas():
    # Ejemplo A: 150.00 y 37.50 % no coinciden con ningún umbral, así que no debe añadirse ninguna nota.
    result = explain(make_snapshot())
    assert "Nota de redondeo" not in result["content"]
    assert result["anomaly_evidence"]["rounding_notes"] == []


def test_se_redondea_una_sola_vez_y_half_up():
    # R=2800.00, O=900.005: las cifras exactas terminan en 5 (900.005 y 500.005). HALF_UP da 900.01 y
    # 500.01; el redondeo bancario (par) daría 900.00 y 500.00. El impacto exacto 500.005 es P2 y no hay nota.
    result = explain(make_snapshot(reference="2800.00", observed="900.005", numerator="3500.035", days=1,
                                   through=OPENED))
    lines = result["content"].split("\n")
    assert lines[IDX_WHY] == (WHY_PREFIX + "900.01 EUR frente a una referencia de 400.00" + WHY_MIDDLE
                              + "500.01 EUR (125.00 %).")
    assert lines[IDX_IMPACT] == f"Impacto acumulado: 500.01 EUR en 1 día, hasta el 2026-09-08. Criticidad: {LABEL_P2}."
    assert lines[IDX_IMPACT + 1].startswith("Estado:")
    assert result["anomaly_evidence"]["rounding_notes"] == []


def test_referencia_diaria_no_exacta_se_redondea_desde_el_total_semanal():
    # R=1000.00: la referencia diaria es 142.857142... y se muestra 142.86. O=250.00: subida
    # (1750.00-1000.00)/7 = 107.142857... -> 107.14 y 75.00 %.
    result = explain(make_snapshot(reference="1000.00", observed="250.00", numerator="750.00", days=1,
                                   through=OPENED))
    assert result["content"].split("\n")[IDX_WHY] == (
        WHY_PREFIX + "250.00 EUR frente a una referencia de 142.86" + WHY_MIDDLE + "107.14 EUR (75.00 %).")


# --------------------------------------------------------------------------------------------------
# 2.2 Impacto, criticidad, estado, seguimiento, anomalía anterior y moneda
# --------------------------------------------------------------------------------------------------

def test_impacto_acumulado_dias_y_ultimo_dia_de_varios_dias():
    # 5 días acumulados hasta el 12 de septiembre: I=3500.00 -> 500.00 exactos (P2, sin nota).
    result = explain(make_snapshot(numerator="3500.00", days=5, through=date(2026, 9, 12)))
    line = result["content"].split("\n")[IDX_IMPACT]
    assert line == f"Impacto acumulado: 500.00 EUR en 5 días, hasta el 2026-09-12. Criticidad: {LABEL_P2}."
    impact = result["anomaly_evidence"]["impact"]
    assert impact == {"accumulated_impact": "500.00", "day_count": 5, "through_date": "2026-09-12",
                      "severity": "P2", "severity_band": "500.00 to 2000.00"}
    assert result["anomaly_evidence"]["source"]["data_as_of"] == "2026-09-12"


def test_un_dia_se_escribe_en_singular():
    result = explain(make_snapshot(numerator="1050.00", days=1, through=OPENED))
    assert "en 1 día," in result["content"]
    assert "1 días" not in result["content"]


@pytest.mark.parametrize(
    ("numerator", "observed", "shown", "label", "severity", "band", "note", "notes_key"),
    [
        # Impacto exacto 499.996: se muestra 500.00 pero es P3 (< 500.00); debe llevar la nota "por debajo".
        ("3499.972", "899.996", "500.00", LABEL_P3, "P3", "< 500.00", NOTE_IMPACT_BELOW, ["accumulated_impact"]),
        # 500.00 exactos: P2 (el límite inferior está incluido); cifra y criticidad coherentes, sin nota.
        ("3500.000", "900.00", "500.00", LABEL_P2, "P2", "500.00 to 2000.00", None, []),
        # 1999.996: se muestra 2000.00 y es P2; coherente (2000.00 está dentro de P2), sin nota.
        ("13999.972", "2399.996", "2000.00", LABEL_P2, "P2", "500.00 to 2000.00", None, []),
        # 2000.00 exactos: P2 (el límite superior está incluido), sin nota.
        ("14000.000", "2400.00", "2000.00", LABEL_P2, "P2", "500.00 to 2000.00", None, []),
        # 2000.004: se muestra 2000.00 pero es P1 (> 2000.00); nota "por encima".
        ("14000.028", "2400.004", "2000.00", LABEL_P1, "P1", "> 2000.00", NOTE_IMPACT_ABOVE, ["accumulated_impact"]),
        # 499.99: P3 sin ambigüedad; no hay nota aunque esté cerca del límite.
        ("3499.93", "899.99", "499.99", LABEL_P3, "P3", "< 500.00", None, []),
    ],
)
def test_criticidad_se_decide_sobre_el_impacto_exacto_en_los_bordes(
        numerator, observed, shown, label, severity, band, note, notes_key):
    # Con R=2800.00 y un solo día, O=(numerador+2800)/7 cumple la regla de apertura. La criticidad se
    # decide sobre el numerador exacto, nunca sobre la cifra ya redondeada, y la nota solo aparece cuando
    # la cifra mostrada contradice aparentemente la criticidad.
    result = explain(make_snapshot(reference="2800.00", observed=observed, numerator=numerator, days=1,
                                   through=OPENED))
    lines = result["content"].split("\n")
    assert lines[IDX_IMPACT] == f"Impacto acumulado: {shown} EUR en 1 día, hasta el 2026-09-08. Criticidad: {label}."
    if note is None:
        assert lines[IDX_IMPACT + 1].startswith("Estado:")
    else:
        assert lines[IDX_IMPACT + 1] == note
        assert lines[IDX_IMPACT + 2].startswith("Estado:")
    evidence = result["anomaly_evidence"]
    assert evidence["rounding_notes"] == notes_key
    assert evidence["impact"]["accumulated_impact"] == shown
    assert evidence["impact"]["severity"] == severity
    assert evidence["impact"]["severity_band"] == band


@pytest.mark.parametrize(
    ("kwargs", "expected_state_line"),
    [
        ({"status": "new"}, "Estado: Nueva. Se sigue observando."),
        ({"status": "investigating"}, "Estado: Investigando. Se sigue observando."),
        ({"status": "new", "observation": "no_longer_observed", "no_longer_observed_on": date(2026, 9, 20)},
         "Estado: Nueva. Ya no se observa desde 2026-09-20; sigue abierta hasta que una persona la cierre."),
        ({"status": "investigating", "observation": "no_longer_observed", "no_longer_observed_on": date(2026, 9, 20)},
         "Estado: Investigando. Ya no se observa desde 2026-09-20; sigue abierta hasta que una persona la cierre."),
        # Cerrada: sin frase de observación, con fecha de cierre en UTC y el motivo entrecomillado.
        ({"status": "resolved", "closed_at": datetime(2026, 9, 21, 2, 30, tzinfo=UTC),
          "closure_reason": "Migración completada"},
         'Estado: Resuelta. Cerrada el 2026-09-21 (UTC) con el motivo "Migración completada".'),
        ({"status": "false_positive", "closed_at": datetime(2026, 9, 21, 2, 30, tzinfo=UTC),
          "closure_reason": "Pico planificado"},
         'Estado: Falso positivo. Cerrada el 2026-09-21 (UTC) con el motivo "Pico planificado".'),
        # Cerrada tras dejar de observarse: el cierre manda y no se menciona la observación.
        ({"status": "resolved", "observation": "no_longer_observed", "no_longer_observed_on": date(2026, 9, 20),
          "closed_at": datetime(2026, 9, 21, 2, 30, tzinfo=UTC), "closure_reason": "Hecho"},
         'Estado: Resuelta. Cerrada el 2026-09-21 (UTC) con el motivo "Hecho".'),
        # Cierre con zona horaria: 23:30 en UTC-3 del día 20 es el día 21 en UTC; la fecha se da en UTC.
        ({"status": "resolved", "closed_at": datetime(2026, 9, 20, 23, 30, tzinfo=timezone(timedelta(hours=-3))),
          "closure_reason": "Hecho"},
         'Estado: Resuelta. Cerrada el 2026-09-21 (UTC) con el motivo "Hecho".'),
    ],
)
def test_estado_y_seguimiento_con_las_palabras_del_panel(kwargs, expected_state_line):
    result = explain(make_snapshot(**kwargs))
    lines = result["content"].split("\n")
    assert lines[IDX_STATE] == expected_state_line
    # Solo hay una línea de estado y la que sigue ya no es de seguimiento.
    assert sum(line.startswith("Estado:") for line in lines) == 1
    assert lines[IDX_STATE + 1] == CAUSE_LINE


def test_cierre_en_la_evidencia_conserva_fecha_y_motivo_del_episodio():
    result = explain(make_snapshot(status="resolved", closed_at=datetime(2026, 9, 21, 2, 30, tzinfo=UTC),
                                   closure_reason="Hecho"))
    episode = result["anomaly_evidence"]["episode"]
    assert (episode["status"], episode["closed_at"], episode["closure_reason"]) == (
        "resolved", "2026-09-21T02:30:00+00:00", "Hecho")


def test_anomalia_anterior_va_justo_despues_de_la_linea_de_estado():
    result = explain(make_snapshot(previous=PREVIOUS_ID))
    lines = result["content"].split("\n")
    expected = lines_a(result["anomaly_evidence"]["id"])
    expected.insert(IDX_STATE + 1, f"Este servicio ya tuvo una anomalía anterior: {PREVIOUS_ID}.")
    assert lines == expected
    assert result["anomaly_evidence"]["episode"]["previous_episode_id"] == PREVIOUS_ID


def test_sin_anomalia_anterior_no_hay_esa_linea():
    assert "anomalía anterior" not in explain(make_snapshot())["content"]


def test_usd_se_escribe_todo_en_usd_sin_conversion():
    # Cada importe y umbral lleva la moneda del episodio. Las limitaciones son texto fijo (mencionan
    # "EUR y USD" como monedas evaluadas), así que solo se transforman las demás líneas.
    result = explain(make_snapshot(currency="USD"))
    lines = result["content"].split("\n")
    expected = [line if line.startswith("- ") else line.replace("EUR", "USD")
                for line in lines_a(result["anomaly_evidence"]["id"])]
    assert lines == expected
    assert not re.search(r"\d EUR", result["content"])
    assert result["anomaly_evidence"]["episode"]["currency"] == "USD"


def test_las_notas_de_redondeo_llevan_la_moneda_del_episodio():
    result = explain(make_snapshot(currency="USD", reference="2800.00", observed="500.004", numerator="700.028",
                                   days=1, through=OPENED))
    note = result["content"].split("\n")[IDX_IMPACT + 1]
    assert note == NOTE_ABSOLUTE.replace("EUR", "USD")


def test_explained_at_con_otra_zona_se_convierte_a_utc():
    # 20:30 en UTC+2 son las 18:30 UTC: la fotografía y la evidencia se escriben siempre en UTC.
    at = datetime(2026, 10, 12, 20, 30, tzinfo=timezone(timedelta(hours=2)))
    result = explain(make_snapshot(), at=at)
    assert result["anomaly_evidence"]["explained_at"] == "2026-10-12T18:30:00+00:00"
    assert result["content"].split("\n")[-2] == "Fotografía tomada el 2026-10-12T18:30:00+00:00 (UTC)."


# --------------------------------------------------------------------------------------------------
# 2.3 Causa no establecida, limitaciones, aviso sintético, alcance, servicio nulo y datos hostiles
# --------------------------------------------------------------------------------------------------

def test_limitaciones_en_espanol_una_por_cada_limitacion_del_episodio():
    # Si alguien añade o quita una limitación en el episodio, esta prueba obliga a traducirla.
    from app.services.anomaly_episodes import LIMITATIONS as english
    module = load()
    assert isinstance(module.LIMITATIONS_ES, tuple)
    assert len(module.LIMITATIONS_ES) == len(english)
    assert list(module.LIMITATIONS_ES) == LIMITATIONS_ES_LITERAL
    assert all(spanish != original for spanish, original in zip(module.LIMITATIONS_ES, english))


def test_el_texto_lista_las_limitaciones_exactas_y_en_orden():
    result = explain(make_snapshot())
    module = load()
    lines = result["content"].split("\n")
    start = lines.index("Limitaciones:")
    bullets = [line for line in lines if line.startswith("- ")]
    assert bullets == [f"- {text}" for text in module.LIMITATIONS_ES]
    assert lines[start + 1:start + 1 + len(bullets)] == bullets
    assert result["anomaly_evidence"]["limitations"] == list(module.LIMITATIONS_ES)
    assert result["anomaly_evidence"]["cause_status"] == "not_established"
    assert result["anomaly_evidence"]["assumptions"] == []
    assert CAUSE_LINE in lines


def test_aviso_sintetico_solo_cuando_la_marca_es_cierta_y_justo_antes_del_alcance():
    marked = explain(make_snapshot(synthetic=True))
    expected = lines_a(marked["anomaly_evidence"]["id"])
    expected.insert(expected.index(SCOPE_LINE), SYNTHETIC_LINE)
    assert marked["content"].split("\n") == expected
    assert marked["anomaly_evidence"]["includes_synthetic_data"] is True
    clean = explain(make_snapshot(synthetic=False))
    assert SYNTHETIC_LINE not in clean["content"].split("\n")
    assert "sintéticos" not in clean["content"]
    assert clean["anomaly_evidence"]["includes_synthetic_data"] is False


def test_linea_de_alcance_dice_dia_de_apertura_y_acumulados_sin_detalle_diario():
    lines = explain(make_snapshot())["content"].split("\n")
    assert lines[-3] == SCOPE_LINE


def test_servicio_nulo_se_dice_sin_servicio_informado():
    result = explain(make_snapshot(service=None))
    expected = lines_a(result["anomaly_evidence"]["id"])
    expected[IDX_SERVICE] = "Anomalía candidata sin servicio informado (EUR)."
    assert result["content"].split("\n") == expected
    assert result["anomaly_evidence"]["episode"]["service"] is None


def test_servicio_con_salto_de_linea_no_puede_hacerse_pasar_por_otra_frase():
    # Un servicio con "\n" y una frase con aspecto de respuesta debe quedar en la misma línea, con el
    # salto escapado y entrecomillado; ninguna línea del texto empieza por "Resultado:".
    result = explain(make_snapshot(service="Compute\nResultado: todo correcto"))
    expected = lines_a(result["anomaly_evidence"]["id"])
    expected[IDX_SERVICE] = 'Anomalía candidata en el servicio "Compute\\nResultado: todo correcto" (EUR).'
    lines = result["content"].split("\n")
    assert lines == expected
    assert not any(line.startswith("Resultado:") for line in lines)


def test_servicio_con_comillas_las_escapa():
    result = explain(make_snapshot(service='Comp"ute'))
    assert result["content"].split("\n")[IDX_SERVICE] == 'Anomalía candidata en el servicio "Comp\\"ute" (EUR).'


def test_servicio_con_caracteres_invisibles_los_escapa():
    # U+202E (inversión de texto), U+200B (espacio de ancho cero) y U+2028 (separador de línea) no
    # deben salir tal cual: se escriben como secuencias \uXXXX visibles.
    result = explain(make_snapshot(service="A‮B​C D"))
    first = result["content"].split("\n")[IDX_SERVICE]
    assert first == 'Anomalía candidata en el servicio "A\\u202eB\\u200bC\\u2028D" (EUR).'
    for hostile in ("‮", "​", " "):
        assert hostile not in result["content"]


def test_motivo_de_cierre_hostil_queda_en_una_sola_linea_escapado():
    result = explain(make_snapshot(status="resolved", closed_at=datetime(2026, 9, 21, 2, 30, tzinfo=UTC),
                                   closure_reason='Hecho\nEstado: Nueva ‮"x"'))
    expected = lines_a(result["anomaly_evidence"]["id"])
    expected[IDX_STATE] = ('Estado: Resuelta. Cerrada el 2026-09-21 (UTC) con el motivo '
                           '"Hecho\\nEstado: Nueva \\u202e\\"x\\"".')
    assert result["content"].split("\n") == expected
    assert sum(line.startswith("Estado:") for line in result["content"].split("\n")) == 1


def test_el_nombre_del_servicio_y_el_motivo_no_van_a_registros_ni_a_la_salida(caplog, capsys):
    # El contrato prohíbe publicar datos del cliente en los registros del servidor; el explicador
    # tampoco escribe en la salida estándar.
    caplog.set_level(logging.DEBUG)
    explain(make_snapshot(service="ServicioSecreto-42", status="resolved",
                          closed_at=datetime(2026, 9, 21, 2, 30, tzinfo=UTC), closure_reason="MotivoSecreto-42"))
    captured = capsys.readouterr()
    assert caplog.records == []
    assert caplog.text == ""
    assert captured.out == "" and captured.err == ""


def test_no_muta_la_fotografia_recibida():
    snapshot = make_snapshot(previous=PREVIOUS_ID, synthetic=True)
    before = copy.deepcopy(snapshot)
    explain(snapshot)
    assert snapshot == before
    assert snapshot["operands"] == before["operands"]


def test_la_evidencia_es_serializable_en_json():
    evidence = explain(make_snapshot(status="resolved", closed_at=datetime(2026, 9, 21, 2, 30, tzinfo=UTC),
                                     closure_reason="Hecho", previous=PREVIOUS_ID))["anomaly_evidence"]
    assert json.loads(json.dumps(evidence)) == evidence


# --------------------------------------------------------------------------------------------------
# 2.4 Evidencia: forma, identificador y casos no explicables
# --------------------------------------------------------------------------------------------------

def test_identificador_tiene_formato_y_se_recalcula_a_mano():
    # El identificador es el sha256 del JSON canónico {"tenant": ..., **evidencia sin id ni explained_at}.
    # Se recalcula aquí de forma independiente: así queda fijado el algoritmo documentado.
    result = explain(make_snapshot(), tenant="tenant-a")
    evidence = result["anomaly_evidence"]
    assert re.fullmatch(r"anomaly-explanation:[0-9a-f]{64}", evidence["id"])
    assert evidence["id"] == recompute_id(evidence, "tenant-a")
    assert result["content"].split("\n")[-1] == f"Evidencia: {evidence['id']}."


def test_el_cliente_entra_en_el_hash_pero_no_se_guarda_en_la_evidencia():
    evidence = explain(make_snapshot(), tenant="tenant-secreto-9")["anomaly_evidence"]
    assert "tenant-secreto-9" not in json.dumps(evidence)
    assert evidence["id"] == recompute_id(evidence, "tenant-secreto-9")


def test_mismo_estado_y_distinto_explained_at_da_el_mismo_id():
    first = explain(make_snapshot(), at=datetime(2026, 10, 12, 18, 30, tzinfo=UTC))
    later = explain(make_snapshot(), at=datetime(2026, 10, 13, 9, 5, 7, tzinfo=UTC))
    assert first["anomaly_evidence"]["id"] == later["anomaly_evidence"]["id"]
    assert first["anomaly_evidence"]["explained_at"] != later["anomaly_evidence"]["explained_at"]
    # La única línea del texto que cambia es la de la fotografía.
    differing = [(a, b) for a, b in zip(first["content"].split("\n"), later["content"].split("\n")) if a != b]
    assert differing == [("Fotografía tomada el 2026-10-12T18:30:00+00:00 (UTC).",
                          "Fotografía tomada el 2026-10-13T09:05:07+00:00 (UTC).")]


def test_misma_peticion_repetida_da_el_mismo_resultado():
    assert explain(make_snapshot()) == explain(make_snapshot())


def test_otro_cliente_da_otro_id():
    one = explain(make_snapshot(), tenant="tenant-a")["anomaly_evidence"]["id"]
    two = explain(make_snapshot(), tenant="tenant-b")["anomaly_evidence"]["id"]
    assert one != two


@pytest.mark.parametrize(
    "kwargs",
    [
        {"status": "investigating"},
        {"numerator": "2800.07"},
        {"days": 3},
        {"through": date(2026, 9, 10)},
        {"service": "Compute2"},
        {"service": None},
        {"currency": "USD"},
        {"previous": PREVIOUS_ID},
        {"observation": "no_longer_observed", "no_longer_observed_on": date(2026, 9, 20)},
        {"synthetic": True},
    ],
)
def test_cualquier_cambio_del_episodio_o_de_los_operandos_cambia_el_id(kwargs):
    base = explain(make_snapshot())["anomaly_evidence"]["id"]
    changed = explain(make_snapshot(**kwargs))["anomaly_evidence"]
    assert changed["id"] != base
    assert changed["id"] == recompute_id(changed, "tenant-a")


@pytest.mark.parametrize("kwargs", [{"reference": "2800.001"}, {"observed": "550.001"}, {"numerator": "2800.001"}])
def test_un_cambio_solo_en_los_operandos_exactos_cambia_el_id(kwargs):
    # Solo cambian los operandos exactos: el episodio de la API sale idéntico (400.00, 550.00 y 400.00
    # tras redondear), así que el identificador debe depender de los operandos y no solo del episodio.
    base_snapshot, changed_snapshot = make_snapshot(), make_snapshot(**kwargs)
    assert changed_snapshot["episode"] == base_snapshot["episode"]  # premisa de la prueba
    assert changed_snapshot["operands"] != base_snapshot["operands"]
    assert (explain(changed_snapshot)["anomaly_evidence"]["id"]
            != explain(base_snapshot)["anomaly_evidence"]["id"])


def test_el_motivo_de_cierre_y_las_limitaciones_del_episodio_cambian_el_id():
    closed = dict(status="resolved", closed_at=datetime(2026, 9, 21, 2, 30, tzinfo=UTC))
    one = explain(make_snapshot(closure_reason="Motivo uno", **closed))["anomaly_evidence"]["id"]
    two = explain(make_snapshot(closure_reason="Motivo dos", **closed))["anomaly_evidence"]["id"]
    assert one != two
    base = explain(make_snapshot())["anomaly_evidence"]["id"]
    snapshot = make_snapshot()
    snapshot["episode"]["limitations"] = snapshot["episode"]["limitations"] + ["Another limitation."]
    assert explain(snapshot)["anomaly_evidence"]["id"] != base


def test_cliente_con_caracteres_no_ascii_se_hashea_en_utf8_sin_escapar():
    # Un cliente con caracteres no ASCII se hashea en UTF-8 sin escapar, como dice el contrato.
    evidence = explain(make_snapshot(), tenant="cliente-ñ-€")["anomaly_evidence"]
    assert evidence["id"] == recompute_id(evidence, "cliente-ñ-€")


def test_excepcion_y_constantes_publicas_del_modulo():
    module = load()
    assert issubclass(module.ExplanationUnavailable, Exception)
    assert callable(module.explain_episode)


@pytest.mark.parametrize(
    "kwargs",
    [
        # Otra versión de reglas: no se sabe contarla, aunque las cifras fueran coherentes.
        {"rules_version": "jup019-daily-v2"},
        {"rules_version": ""},
        # Reglas guardadas distintas de las de la versión.
        {"rules": rules_with(absolute_increase="150.00")},
        {"rules": rules_with(relative_increase_percent="25")},
        {"rules": rules_with(severity={"P1": "> 3000.00", "P2": "500.00 to 3000.00", "P3": "< 500.00"})},
        {"rules": rules_with(extra_rule=1)},
        # Operandos que no cumplen la regla del día de apertura (ambos umbrales son estrictos).
        # Subida exactamente 100.00 por día: O=500.00, R=2800.00 -> 700.00 / 7 = 100.00 (no es > 100).
        {"reference": "2800.00", "observed": "500.00", "numerator": "700.00", "days": 1},
        # Subida exactamente 20 %: R=7000.00, O=1200.00 -> 1400.00 (> 700.00) pero 1400.00 * 5 = 7000.00 (no es > R).
        {"reference": "7000.00", "observed": "1200.00", "numerator": "1400.00", "days": 1},
        # Sin referencia (R=0): la regla exige R > 0; además evita una división por cero al calcular el porcentaje.
        {"reference": "0.00", "observed": "500.00", "numerator": "3500.00", "days": 1},
        # Observado por debajo de la referencia.
        {"reference": "2800.00", "observed": "300.00", "numerator": "0.00", "days": 1},
    ],
)
def test_no_explica_lo_que_no_sabe_explicar_y_no_devuelve_texto(kwargs):
    # Preferimos no responder a dar una explicación aproximada: debe lanzarse la excepción propia antes
    # de producir ningún texto o evidencia.
    module = load()
    snapshot = make_snapshot(**kwargs)
    result = None
    with pytest.raises(module.ExplanationUnavailable):
        result = module.explain_episode(snapshot, tenant_id="tenant-a", explained_at=EXPLAINED_AT)
    assert result is None


def test_no_explicable_tampoco_escribe_en_registros(caplog):
    caplog.set_level(logging.DEBUG)
    module = load()
    with pytest.raises(module.ExplanationUnavailable):
        module.explain_episode(make_snapshot(service="ServicioSecreto-42", rules_version="jup019-daily-v2"),
                               tenant_id="tenant-a", explained_at=EXPLAINED_AT)
    assert caplog.records == []


def test_bordes_justo_por_encima_del_umbral_si_se_explican():
    # Contrapunto de los bordes estrictos: un céntimo semanal por encima de cada umbral sí cumple la regla.
    # Subida 100.004/día (700.028 semanal) y 20.0002 % ya se cubren arriba; aquí O=500.001 (700.007 > 700).
    result = explain(make_snapshot(reference="2800.00", observed="500.001", numerator="700.007", days=1,
                                   through=OPENED))
    assert result["anomaly_evidence"]["opening"]["conditions_met"] is True
