"""JUP-038, tarea 2.6: casos nuevos que matan mutantes supervivientes del explicador.

Este archivo AMPLIA `test_anomaly_explanations.py` (que está commiteado y bloqueado): no repite sus casos,
solo añade los que faltaban. Reutiliza sus ayudantes (`make_snapshot`, `explain`, `recompute_id`...) para que
la fotografía se arme igual que en producción. Los tests se ejecutan con `apps/backend/tests` en el path.

Mutante equivalente aceptado y SIN prueba: `_PRECISION = 120 -> 121`. Una cifra más de precisión no cambia
ningún resultado observable porque el redondeo a dos decimales ya ocurre con margen de sobra.
"""
import copy
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction

import pytest

from test_anomaly_explanations import EXPLAINED_AT, UTC, explain, load, make_snapshot, recompute_id

CLOSED_AT = datetime(2026, 9, 21, 2, 30, tzinfo=UTC)


# --------------------------------------------------------------------------------------------------
# 1. Guardas de `_state_line` sin prueba
# --------------------------------------------------------------------------------------------------

def _assert_no_explicable(snapshot, caplog):
    # Ayudante común: debe lanzarse la excepción propia, no devolverse ningún texto, y no escribirse en
    # los registros (el servicio y el motivo de cierre son datos del cliente).
    module = load()
    result = None
    with pytest.raises(module.ExplanationUnavailable):
        result = module.explain_episode(snapshot, tenant_id="tenant-a", explained_at=EXPLAINED_AT)
    assert result is None
    assert caplog.records == []


@pytest.mark.parametrize("status", ["archived", "", "NEW", "closed"])
def test_estado_desconocido_no_se_explica(status, caplog):
    # Mata el mutante que borra la guarda `status not in STATUS_WORDS` (con `.get(status, ...)` se
    # devolvería texto con una palabra de estado inventada). El estado viene de la base de datos y un valor
    # nuevo no debe explicarse con una etiqueta que nadie ha definido.
    caplog.set_level(logging.DEBUG)
    _assert_no_explicable(make_snapshot(status=status), caplog)


@pytest.mark.parametrize("status", ["resolved", "false_positive"])
@pytest.mark.parametrize(
    "closed_at, closure_reason",
    [
        pytest.param(None, "Hecho", id="sin-fecha-de-cierre-pero-con-motivo"),
        pytest.param(CLOSED_AT, None, id="con-fecha-de-cierre-pero-sin-motivo"),
        pytest.param(None, None, id="sin-fecha-ni-motivo"),
    ],
)
def test_estado_cerrado_con_cierre_incompleto_no_se_explica(status, closed_at, closure_reason, caplog):
    # Mata el borrado de la guarda de cierre incompleto y el mutante `or -> and`: con `and` solo fallaría el
    # caso (None, None); los casos con UN solo dato ausente (fecha sin motivo y motivo sin fecha) obligan a
    # que la condición sea `or`. Un cierre sin fecha o sin motivo es un dato corrupto: no se inventa ninguno.
    caplog.set_level(logging.DEBUG)
    _assert_no_explicable(make_snapshot(status=status, closed_at=closed_at, closure_reason=closure_reason), caplog)


@pytest.mark.parametrize("status", ["new", "investigating"])
def test_no_observada_sin_fecha_en_estado_abierto_no_se_explica(status, caplog):
    # Mata el borrado de la guarda `no_longer_observed_on is None`: sin ella se llamaría a `.isoformat()`
    # sobre None (AttributeError) o se escribiría una fecha vacía; el contrato pide la excepción propia.
    caplog.set_level(logging.DEBUG)
    _assert_no_explicable(make_snapshot(status=status, observation="no_longer_observed",
                                        no_longer_observed_on=None), caplog)


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        pytest.param({"status": "new", "observation": "no_longer_observed", "no_longer_observed_on": date(2026, 9, 12)},
                     "Estado: Nueva. Ya no se observa desde 2026-09-12; sigue abierta hasta que una persona la cierre.",
                     id="nueva-no-observada-con-fecha"),
        pytest.param({"status": "investigating", "observation": "no_longer_observed",
                      "no_longer_observed_on": date(2026, 9, 12)},
                     "Estado: Investigando. Ya no se observa desde 2026-09-12; sigue abierta hasta que una persona la cierre.",
                     id="investigando-no-observada-con-fecha"),
        pytest.param({"status": "resolved", "closed_at": CLOSED_AT, "closure_reason": "Hecho"},
                     'Estado: Resuelta. Cerrada el 2026-09-21 (UTC) con el motivo "Hecho".',
                     id="resuelta-con-cierre-completo"),
        pytest.param({"status": "false_positive", "closed_at": CLOSED_AT, "closure_reason": "Hecho"},
                     'Estado: Falso positivo. Cerrada el 2026-09-21 (UTC) con el motivo "Hecho".',
                     id="falso-positivo-con-cierre-completo"),
    ],
)
def test_control_positivo_con_los_datos_completos_si_se_explica(kwargs, expected, caplog):
    # Control positivo de las guardas anteriores: con los datos completos la misma ruta SÍ explica. Evita que
    # los tests de rechazo pasen porque la función falle siempre, y de paso fija la línea de estado exacta.
    caplog.set_level(logging.DEBUG)
    result = explain(make_snapshot(**kwargs))
    assert expected in result["content"].split("\n")
    assert caplog.records == []


# --------------------------------------------------------------------------------------------------
# 2. La evidencia no comparte estructuras mutables con la fotografía
# --------------------------------------------------------------------------------------------------

def test_mutar_la_evidencia_no_cambia_la_fotografia():
    # Mata el mutante `copy.deepcopy -> copy.copy` en `_iso`: `copy.copy` de un dict copia solo el primer
    # nivel, así que `rules["severity"]` y `rules["currencies"]` seguirían siendo los mismos objetos que los
    # de la fotografía. Quien reciba la evidencia y la edite no debe poder corromper el episodio guardado.
    snapshot = make_snapshot()
    before = copy.deepcopy(snapshot)
    evidence = explain(snapshot)["anomaly_evidence"]

    evidence["episode"]["limitations"].append("intrusa")
    evidence["episode"]["rules"]["severity"]["P1"] = "> 1.00"
    evidence["episode"]["rules"]["currencies"].append("XXX")
    evidence["episode"]["rules"]["relative_increase_percent"] = "99"

    assert snapshot == before
    assert snapshot["episode"]["rules"]["severity"]["P1"] == "> 2000.00"
    assert "XXX" not in snapshot["episode"]["rules"]["currencies"]
    assert "intrusa" not in snapshot["episode"]["limitations"]


def test_mutar_la_fotografia_despues_no_cambia_la_evidencia_ya_devuelta():
    # Sentido inverso del mismo mutante: la evidencia devuelta es una copia profunda, así que editar la
    # fotografía después de explicar (p. ej. al reutilizarla en otra petición) no altera lo ya entregado.
    snapshot = make_snapshot()
    evidence = explain(snapshot)["anomaly_evidence"]
    before = copy.deepcopy(evidence)

    snapshot["episode"]["limitations"].append("intrusa")
    snapshot["episode"]["rules"]["severity"]["P1"] = "> 1.00"
    snapshot["episode"]["rules"]["currencies"].append("XXX")

    assert evidence == before
    assert evidence["episode"]["rules"]["severity"]["P1"] == "> 2000.00"


# --------------------------------------------------------------------------------------------------
# 3. Operandos con exponente: texto plano, nunca notación científica
# --------------------------------------------------------------------------------------------------

def test_operandos_con_exponente_se_escriben_sin_notacion_cientifica():
    # Mata el mutante `format(value, "f") -> str(value)`: `str(Decimal("2.8E+3"))` es "2.8E+3" y la
    # evidencia debe poder recalcularse a mano con cifras planas. Comprobación aritmética: R=2800 (diaria
    # 400), O=550, O*7=3850, exceso 3850-2800=1050 > 100*7 y 1050*5=5250 > 2800, luego cumple `triggers`;
    # subida 1050/7=150 por día (37.50 %); impacto 2800/7=400.
    exponent = make_snapshot(reference="2.8E+3", observed="5.5E+2", numerator="2.8E+3")
    # Los mismos valores numéricos escritos sin exponente (y con 2 decimales, como en el ejemplo A).
    plain = make_snapshot(reference="2800.00", observed="550.00", numerator="2800.00")

    result = explain(exponent)
    evidence = result["anomaly_evidence"]

    assert evidence["operands"] == {
        "reference_seven_day_total": "2800", "opening_observed_cost": "550", "accumulated_impact_times_seven": "2800",
    }
    assert "E+" not in json.dumps(evidence["operands"])

    # El texto no depende de cómo se escribió el Decimal: solo cambia la última línea (el identificador).
    plain_result = explain(plain)
    assert result["content"].split("\n")[:-1] == plain_result["content"].split("\n")[:-1]
    assert "150.00 EUR (37.50 %)" in result["content"]

    # El identificador se recalcula a mano sobre la evidencia con esos operandos planos, y el texto lo cita.
    assert evidence["id"] == recompute_id(evidence, "tenant-a")
    assert result["content"].split("\n")[-1] == f"Evidencia: {evidence['id']}."
    # Y es distinto del de la fotografía con "2800.00": el texto exacto de los operandos entra en el hash.
    assert evidence["id"] != plain_result["anomaly_evidence"]["id"]
    # El resto de la evidencia (cifras mostradas, episodio, límites) es idéntico entre ambas escrituras.
    keep = lambda ev: {key: value for key, value in ev.items() if key not in ("id", "operands")}  # noqa: E731
    assert keep(evidence) == keep(plain_result["anomaly_evidence"])


# --------------------------------------------------------------------------------------------------
# 4. Precisión alta: importes de ~31 cifras
# --------------------------------------------------------------------------------------------------

def _two_decimals_half_up(value: Fraction) -> str:
    # Redondeo HALF_UP a dos decimales hecho a mano con enteros (valores positivos): cuenta de céntimos
    # = floor(value * 100 + 1/2). Independiente de `money` del producto y de la precisión de `Decimal`.
    cents = (2 * value.numerator * 100 + value.denominator) // (2 * value.denominator)
    return f"{cents // 100}.{cents % 100:02d}"


def test_importes_de_treinta_cifras_se_calculan_con_aritmetica_exacta():
    # Mata `_PRECISION = 28` (la precisión por defecto de Decimal). Con 28 cifras significativas los importes
    # de 31-32 cifras pierden dígitos en `reference/7`, en `observed*7`, en `exceso/7`, en `exceso*100/ref` y
    # en `numerador/7`, y el texto mostraría cifras falsas.
    #
    # Valores diseñados (mismas cifras de antes, desplazadas 6 posiciones para caber en NUMERIC(38,12): 25 cifras
    # enteras y 8 decimales; s = 5000000000000000000000000007):
    #   R = 140000*s  -> 7000000000000000000000000.00980000   (diaria exacta 1000000000000000000000000.0014)
    #   O =  30001*s  -> 1500050000000000000000000.00210007
    # El exceso semanal (7*O - R, ~3.5e24) supera de sobra los 100 por día y el 20 % de la referencia, y la
    # subida relativa vale EXACTAMENTE 50.005 % (10001/200): justo en el medio del redondeo, con lo que
    # HALF_UP da 50.01 y cualquier pérdida de cifras (con 28 sale 50.00499999...) da 50.00. Es el caso que
    # delata la precisión. El numerador es el exceso de apertura más un tramo posterior (un episodio de 3 días
    # nunca acumula menos que su día de apertura) y su séptima parte no es exacta, para ejercitar también esa
    # división. Los valores esperados se calculan abajo con `Fraction`, sin usar el módulo.
    reference = "7000000000000000000000000.00980000"
    observed = "1500050000000000000000000.00210007"
    numerator = "4000350000000000000000000.00490149"  # impacto 571478571428571428571428.57 (P1)

    ref_f, obs_f, num_f = Fraction(reference), Fraction(observed), Fraction(numerator)
    excess = obs_f * 7 - ref_f
    # Comprobación previa de que la fotografía cumple `triggers` (exceso diario > 100 y > 20 % de la referencia).
    assert excess > 700 and excess * 5 > ref_f
    expected = {
        "reference": _two_decimals_half_up(ref_f / 7),
        "observed": _two_decimals_half_up(obs_f),
        "absolute": _two_decimals_half_up(excess / 7),
        "relative": _two_decimals_half_up(excess * 100 / ref_f),
        "impact": _two_decimals_half_up(num_f / 7),
    }
    # Anclas literales, para que un error del helper no valide un resultado erróneo a la vez.
    assert expected["reference"] == "1000000000000000000000000.00"
    assert expected["relative"] == "50.01"
    assert expected["impact"] == "571478571428571428571428.57"

    result = explain(make_snapshot(reference=reference, observed=observed, numerator=numerator, days=3,
                                   through=date(2026, 9, 10)))
    lines = result["content"].split("\n")
    evidence = result["anomaly_evidence"]

    assert evidence["opening"]["reference_daily_cost"] == expected["reference"]
    assert evidence["opening"]["observed_cost"] == expected["observed"]
    assert evidence["opening"]["absolute_increase"] == expected["absolute"]
    assert evidence["opening"]["relative_increase_percent"] == expected["relative"]
    assert evidence["impact"]["accumulated_impact"] == expected["impact"]
    assert evidence["impact"]["severity"] == "P1"

    # El texto es coherente con la evidencia: mismas cifras, en las mismas frases.
    assert lines[1].startswith("Por qué se marcó: el 2026-09-08 el coste observado fue "
                               f"{expected['observed']} EUR frente a una referencia de {expected['reference']} EUR al día")
    assert lines[1].endswith(f"Subió {expected['absolute']} EUR ({expected['relative']} %).")
    assert lines[3] == (f"Impacto acumulado: {expected['impact']} EUR en 3 días, hasta el 2026-09-10. "
                        "Criticidad: Alta (P1), por encima de 2000.00 EUR.")

    # Los operandos exactos no se redondean ni se acortan.
    assert evidence["operands"] == {
        "reference_seven_day_total": reference, "opening_observed_cost": observed,
        "accumulated_impact_times_seven": numerator,
    }
    assert evidence["id"] == recompute_id(evidence, "tenant-a")
