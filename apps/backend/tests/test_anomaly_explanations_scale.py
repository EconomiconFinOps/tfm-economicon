"""JUP-038 (segunda ronda de la revisión de la PR #128): los operandos guardados con demasiados decimales.

Qué se valida: el explicador (`explain_episode`) debe rechazar con `ExplanationUnavailable` cualquier operando
(`reference_week_cost`, `opening_observed_cost`, `impact_numerator`) con MÁS de 12 decimales (exponente < -12), y
nunca con otra excepción. Los importes de la tabla se guardan con 12 decimales; más escala no puede salir de un
episodio real (spec `anomaly-episode-explanation`, escenario «Operandos no finitos o fuera de rango»).

El hueco: la validación acotaba dígitos (<= 38) y exponente ajustado (<= 25) pero no la escala. `Decimal("1e-150")`
cuenta como UN dígito y con exponente ajustado -150, así que pasaba ambos límites:
- en la referencia hacía saltar `decimal.InvalidOperation` en `money()` (hoy lo absorbe una red de seguridad), y
- `Decimal("1e-999999")` hace saltar `decimal.Overflow`, que NO está capturado y acabaría en un 500.

Metodología:
- Cada caso rechazado va en una tripleta COHERENTE (cumple la regla de apertura y numerador >= exceso) para que el
  ÚNICO motivo posible del rechazo sean los decimales. Cada caso aislado lleva un "gemelo" idéntico salvo que el
  operando tiene exactamente 12 decimales: el gemelo DEBE explicarse, lo que demuestra que el rechazo del caso
  se debe a los decimales y no a otra regla.
- Con magnitud >= 100 (observado) o >= exceso (numerador) y como mucho 38 dígitos, esos dos operandos no pueden
  tener una escala arbitrariamente pequeña, así que `1e-150` y `1e-999999` solo se pueden aislar en la referencia.
  Para los otros dos se prueban aparte, sin aislar (otra regla ya los rechaza hoy): lo que importa ahí es que la
  excepción sea siempre `ExplanationUnavailable`.
- Las cifras están calculadas a mano: con R=2800.00 y O=550.00 el exceso de apertura es 550.00 * 7 - 2800.00 = 1050.00,
  y con R~0 y O=550.00 es ~3850.00 (de ahí el numerador 3850.00 en los casos de referencia diminuta).
"""
from decimal import Decimal

import pytest

from test_anomaly_explanations_integrity import assert_unavailable, explain, with_operands

# Base coherente para cada operando bajo prueba: los otros dos operandos se fijan para que la tripleta cumpla la
# regla de apertura (exceso > 100 diarios y > 20 %) y numerador >= exceso aunque el operando bajo prueba cambie.
# - referencia diminuta: O=550.00 da exceso ~3850.00, y N=3850.00 lo cubre (el exceso es 3850.00 - R <= 3850.00).
# - observado y numerador con decimales: R=2800.00 y N=2800.00 (o O=550.00) como en el resto de archivos.
BASE_TRIPLE = {
    "reference_week_cost": {"observed": Decimal("550.00"), "numerator": Decimal("3850.00")},
    "opening_observed_cost": {"reference": Decimal("2800.00"), "numerator": Decimal("2800.00")},
    "impact_numerator": {"reference": Decimal("2800.00"), "observed": Decimal("550.00")},
}


def build(name, value):
    """Fotografía con `value` como operando `name` y los otros dos de la base coherente."""
    base = BASE_TRIPLE[name]
    operands = {
        "reference_week_cost": base.get("reference"),
        "opening_observed_cost": base.get("observed"),
        "impact_numerator": base.get("numerator"),
    }
    operands[name] = value
    return with_operands(operands["reference_week_cost"], operands["opening_observed_cost"],
                         operands["impact_numerator"])


# (operando, valor con más de 12 decimales, gemelo con exactamente 12 decimales que SÍ debe explicarse).
# Todos los valores cumplen <= 38 dígitos y exponente ajustado <= 25: solo la escala puede rechazarlos.
ISOLATED = [
    # Referencia: valores diminutos (1 dígito) con escala enorme. Gemelo: 1e-12 (12 decimales, sigue siendo > 0).
    pytest.param("reference_week_cost", Decimal("1e-13"), Decimal("1e-12"), id="referencia-1e-13"),
    pytest.param("reference_week_cost", Decimal("1e-30"), Decimal("1e-12"), id="referencia-1e-30"),
    pytest.param("reference_week_cost", Decimal("1e-150"), Decimal("1e-12"), id="referencia-1e-150"),
    # Overflow sin capturar hoy: `excess * 100 / R` desborda el exponente máximo del contexto.
    pytest.param("reference_week_cost", Decimal("1e-999999"), Decimal("1e-12"), id="referencia-1e-999999"),
    # 13 decimales con un 1e-13 de más y con solo ceros de más: los ceros finales también cuentan como escala.
    pytest.param("reference_week_cost", Decimal("2800.0000000000001"), Decimal("2800.000000000000"),
                 id="referencia-13-decimales-con-uno"),
    pytest.param("reference_week_cost", Decimal("2800.0000000000000"), Decimal("2800.000000000000"),
                 id="referencia-13-decimales-con-cero"),
    # Observado: no puede ser diminuto (>= 100 por día para abrir), así que la escala se consigue con dígitos de
    # más tras la coma; el último caso llega a 38 dígitos (el máximo permitido), con exponente -35.
    pytest.param("opening_observed_cost", Decimal("550.0000000000001"), Decimal("550.000000000000"),
                 id="observado-13-decimales-con-uno"),
    pytest.param("opening_observed_cost", Decimal("550.0000000000000"), Decimal("550.000000000000"),
                 id="observado-13-decimales-con-cero"),
    pytest.param("opening_observed_cost", Decimal("550." + "0" * 29 + "1"), Decimal("550.000000000000"),
                 id="observado-30-decimales"),
    pytest.param("opening_observed_cost", Decimal("550." + "0" * 34 + "1"), Decimal("550.000000000000"),
                 id="observado-35-decimales-38-digitos"),
    # Numerador: debe ser >= exceso (1050.00), con las mismas limitaciones de magnitud que el observado.
    pytest.param("impact_numerator", Decimal("2800.0000000000001"), Decimal("2800.000000000000"),
                 id="numerador-13-decimales-con-uno"),
    pytest.param("impact_numerator", Decimal("2800.0000000000000"), Decimal("2800.000000000000"),
                 id="numerador-13-decimales-con-cero"),
    pytest.param("impact_numerator", Decimal("2800." + "0" * 29 + "1"), Decimal("2800.000000000000"),
                 id="numerador-30-decimales"),
    pytest.param("impact_numerator", Decimal("2800." + "0" * 33 + "1"), Decimal("2800.000000000000"),
                 id="numerador-34-decimales-38-digitos"),
]


@pytest.mark.parametrize(("name", "value", "twin"), ISOLATED)
def test_operando_con_mas_de_12_decimales_no_se_explica_sin_otra_excepcion(name, value, twin):
    # Precondiciones del aislamiento: el valor respeta los límites de dígitos y de exponente ajustado, y SÍ tiene
    # más de 12 decimales. Si alguna fallara, la prueba no estaría aislando la escala.
    assert len(value.as_tuple().digits) <= 38 and value.adjusted() <= 25
    assert value.as_tuple().exponent < -12
    # `assert_unavailable` falla si sale `InvalidOperation`, `Overflow` o cualquier `ArithmeticError`: la ruta
    # solo traduce `ExplanationUnavailable` a 409 y lo demás sería un 500.
    assert_unavailable(build(name, value))


@pytest.mark.parametrize(("name", "value", "twin"), ISOLATED)
def test_control_el_gemelo_con_12_decimales_exactos_si_se_explica(name, value, twin):
    # Demuestra el aislamiento: la MISMA tripleta con el operando a 12 decimales exactos se explica, así que el
    # rechazo del caso anterior solo puede deberse a la escala y no a la regla de apertura ni al numerador.
    assert twin.as_tuple().exponent == -12
    result = explain(build(name, twin))
    assert result["anomaly_evidence"]["status"] == "ok"


# Sin aislar: con otra regla que ya los rechaza (el observado diminuto no abre; el numerador diminuto es menor
# que el exceso) lo que se exige es que el resultado sea SIEMPRE `ExplanationUnavailable`, también para escalas
# extremas como 1e-999999. Pasan hoy y protegen contra un cambio de orden de validaciones que dejara salir un
# `Overflow` o un `InvalidOperation`.
@pytest.mark.parametrize("name", ["opening_observed_cost", "impact_numerator"])
@pytest.mark.parametrize("tiny", ["1e-13", "1e-30", "1e-150", "1e-999999"])
def test_operando_diminuto_nunca_sale_con_otra_excepcion(name, tiny):
    assert_unavailable(build(name, Decimal(tiny)))


# --------------------------------------------------------------------------------------------------
# Controles: lo que está del lado válido de la frontera de 12 decimales se sigue explicando
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name, value", [
    pytest.param("reference_week_cost", Decimal("2800.000000000001"), id="referencia-12-decimales"),
    pytest.param("opening_observed_cost", Decimal("550.000000000001"), id="observado-12-decimales"),
    pytest.param("impact_numerator", Decimal("2800.000000000001"), id="numerador-12-decimales"),
])
def test_control_un_operando_con_12_decimales_y_ultimo_digito_distinto_de_cero_se_explica(name, value):
    # Frontera exacta: 12 decimales NO se rechazan (evita un `<= -12` o un `exponent < -11` por error de uno), y
    # con el último dígito significativo (no solo ceros) para que no dependa de cómo se cuenten los ceros finales.
    assert value.as_tuple().exponent == -12
    assert explain(build(name, value))["anomaly_evidence"]["status"] == "ok"


def test_control_los_tres_operandos_con_12_decimales_se_explican_y_se_devuelven_exactos():
    # Como los guarda la tabla: tres importes a 12 decimales a la vez; la evidencia los devuelve tal cual, sin
    # redondear (la cifra exacta es la que permite recalcular la explicación a mano).
    snapshot = with_operands(Decimal("2800.000000000001"), Decimal("550.000000000001"), Decimal("2800.000000000001"))
    assert explain(snapshot)["anomaly_evidence"]["operands"] == {
        "reference_seven_day_total": "2800.000000000001", "opening_observed_cost": "550.000000000001",
        "accumulated_impact_times_seven": "2800.000000000001"}


def test_control_operandos_enteros_con_exponente_cero_se_explican():
    # Un importe entero (exponente 0, sin decimales) es el caso más simple de escala válida.
    snapshot = with_operands(Decimal("2800"), Decimal("550"), Decimal("2800"))
    assert explain(snapshot)["anomaly_evidence"]["status"] == "ok"


def test_control_operandos_con_exponente_positivo_se_explican():
    # Exponente POSITIVO (2.8E+3 == 2800 con exponente 1): una implementación que comparara el valor absoluto del
    # exponente, o que lo tomara con el signo cambiado, rechazaría un importe válido.
    reference, observed, numerator = Decimal("2.8E+3"), Decimal("5.5E+2"), Decimal("2.8E+3")
    assert reference.as_tuple().exponent > 0 and observed.as_tuple().exponent > 0
    assert explain(with_operands(reference, observed, numerator))["anomaly_evidence"]["status"] == "ok"
