"""JUP-038 (cambios pedidos en la revisión de la PR #128): integridad de los datos guardados del episodio.

Qué se valida: el explicador (`explain_episode`) no debe explicar un episodio cuyos datos guardados no
pueden ser de un episodio real (spec `anomaly-episode-explanation`, requisito «Explicación no disponible
sin inventar»: escenarios «Datos guardados que no pueden ser de un episodio real» y «Operandos no finitos o
fuera de rango»). Hoy esos datos se explican con evidencia "ok" (resultado engañoso) o revientan con
`decimal.InvalidOperation` (un 500); el comportamiento esperado es siempre `ExplanationUnavailable`.

Metodología:
- Se parte de una fotografía VÁLIDA (la del ejemplo A de `test_anomaly_explanations.make_snapshot`) y se
  corrompe UN solo dato cada vez, escribiendo directamente en el diccionario. No se pasa por
  `episode_payload` porque este calcularía con el dato corrupto (un NaN rompería al construir la
  fotografía y la prueba fallaría por el motivo equivocado).
- Cada invariante tiene sus casos de control (frontera VÁLIDA que debe seguir explicándose), para que una
  implementación demasiado estricta que rechace todo no pase por verde.
- Para los operandos se exige `ExplanationUnavailable` y NUNCA otra excepción (`InvalidOperation`,
  `ZeroDivisionError`, `TypeError`): una excepción distinta acabaría en un 500 en la ruta.
- Las cifras están calculadas a mano: con R=2800.00 y O=550.00 el exceso semanal del día de apertura es
  550.00 * 7 - 2800.00 = 1050.00.
"""
import copy
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.services.anomaly_explanations import ExplanationUnavailable, explain_episode
from test_anomaly_explanations import EXPLAINED_AT, OPENED, make_snapshot

CLOSED_AT = datetime(2026, 9, 21, 2, 30, tzinfo=timezone.utc)

def explain(snapshot):
    return explain_episode(snapshot, tenant_id="tenant-a", explained_at=EXPLAINED_AT)


def assert_unavailable(snapshot):
    """Exige `ExplanationUnavailable` y nada más.

    Se captura por separado cualquier otra excepción para dar un mensaje claro: la ruta solo traduce
    `ExplanationUnavailable` a 409, y cualquier otra acabaría en un 500.
    """
    try:
        result = explain(snapshot)
    except ExplanationUnavailable:
        return
    except Exception as error:  # noqa: BLE001 - se quiere distinguir exactamente qué excepción salió
        pytest.fail(f"se esperaba ExplanationUnavailable y salió {type(error).__name__}: {error}")
    pytest.fail(f"se explicó un episodio incoherente; evidencia {result['anomaly_evidence']['status']!r}")


def corrupt_episode(**changes):
    """Fotografía válida con campos del episodio sobrescritos tal cual (sin pasar por `episode_payload`)."""
    snapshot = make_snapshot()
    snapshot["episode"].update(changes)
    return snapshot


def with_operands(reference, observed, numerator, **snapshot_kwargs):
    """Fotografía válida con los tres operandos sobrescritos tal cual (pueden no ser Decimal)."""
    snapshot = make_snapshot(**snapshot_kwargs)
    snapshot["operands"] = {"reference_week_cost": reference, "opening_observed_cost": observed,
                            "impact_numerator": numerator}
    return snapshot


def closed_snapshot(status, closure_reason):
    snapshot = make_snapshot(status=status, closed_at=CLOSED_AT, closure_reason="Hecho")
    snapshot["episode"]["closure_reason"] = closure_reason
    return snapshot


# --------------------------------------------------------------------------------------------------
# Invariante 1: la observación solo puede ser "observed" o "no_longer_observed"
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("observation", ["zzz", None, "", "OBSERVED", "observed "])
def test_observacion_desconocida_no_se_explica(observation):
    # Hoy cualquier valor distinto de "no_longer_observed" se cuenta como "se sigue observando": un
    # "zzz" guardado produciría la frase falsa «Se sigue observando».
    assert_unavailable(corrupt_episode(observation=observation))


@pytest.mark.parametrize("observation", ["observed", "no_longer_observed"])
def test_control_las_dos_observaciones_validas_se_siguen_explicando(observation):
    # Control: los dos valores del contrato siguen funcionando; no se rechaza toda observación.
    extra = {"no_longer_observed_on": date(2026, 9, 20)} if observation == "no_longer_observed" else {}
    result = explain(make_snapshot(observation=observation, **extra))
    assert result["anomaly_evidence"]["status"] == "ok"


# --------------------------------------------------------------------------------------------------
# Invariante 2: la moneda tiene que estar entre las de las reglas del propio episodio
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("currency", ["JPY", "eur", None, "", " EUR", "EUR "])
def test_moneda_fuera_de_las_reglas_no_se_explica(currency):
    # Una moneda que las reglas no evalúan (JPY), en minúsculas (el contrato guarda "EUR") o ausente no
    # puede ser de un episodio abierto por el detector; hoy se escribiría tal cual en el texto.
    assert_unavailable(corrupt_episode(currency=currency))


@pytest.mark.parametrize("currency", ["EUR", "USD"])
def test_control_las_dos_monedas_evaluadas_se_siguen_explicando(currency):
    assert explain(make_snapshot(currency=currency))["anomaly_evidence"]["episode"]["currency"] == currency


# --------------------------------------------------------------------------------------------------
# Invariante 3: el número de días de impacto es un entero real >= 1
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("days", [0, -1, -100])
def test_dias_de_impacto_menores_que_uno_no_se_explican(days):
    # El impacto incluye siempre el día de apertura: al menos 1 día. 0 o negativo escribiría «0 días».
    assert_unavailable(corrupt_episode(impact_day_count=days))


@pytest.mark.parametrize("days", [True, False, "2", 1.5, 2.0, None, Decimal("2")],
                         ids=["bool-true", "bool-false", "cadena", "float-fraccion", "float-entero", "none", "decimal"])
def test_dias_de_impacto_que_no_son_un_entero_no_se_explican(days):
    # `True` es un `int` para Python y pasaría un `isinstance(x, int)` ingenuo: el contrato lo rechaza
    # expresamente (bool no es un recuento de días). Una cadena o un float tampoco son un recuento.
    assert_unavailable(corrupt_episode(impact_day_count=days))


@pytest.mark.parametrize("days", [1, 2, 30])
def test_control_dias_de_impacto_enteros_positivos_se_siguen_explicando(days):
    snapshot = corrupt_episode(impact_day_count=days)
    assert explain(snapshot)["anomaly_evidence"]["impact"]["day_count"] == days


# --------------------------------------------------------------------------------------------------
# Invariante 4: el último día del impacto no puede ser anterior al de apertura
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("through", [date(2026, 9, 7), date(2026, 1, 1)])
def test_ultimo_dia_de_impacto_anterior_al_inicio_no_se_explica(through):
    # Inicio 2026-09-08: el impacto acumulado no puede terminar antes de empezar (un día antes, y meses antes).
    assert_unavailable(corrupt_episode(impact_through_date=through))


def test_control_ultimo_dia_igual_al_inicio_con_un_dia_se_sigue_explicando():
    # Frontera válida: el episodio se abrió hoy y solo tiene el día de apertura (1 día, mismo día).
    result = explain(make_snapshot(days=1, through=OPENED, numerator="1050.00"))
    assert result["anomaly_evidence"]["impact"]["through_date"] == OPENED.isoformat()


# --------------------------------------------------------------------------------------------------
# Invariante 5: el numerador del impacto no puede ser menor que el exceso del día de apertura
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("numerator", ["-1", "-0.01", "0", "1049.99", "1049.999999999999", "1000.00", "1.00"])
def test_numerador_menor_que_el_exceso_del_dia_de_apertura_no_se_explica(numerator):
    # Con R=2800.00 y O=550.00 el exceso de apertura es 1050.00: el impacto acumulado lo incluye, así que un
    # numerador menor (negativo, cero o 0.000000000001 por debajo) no puede ser de un episodio real.
    snapshot = make_snapshot()
    snapshot["operands"]["impact_numerator"] = Decimal(numerator)
    assert_unavailable(snapshot)


@pytest.mark.parametrize("numerator", ["1050.00", "1050.000000000000", "1050.000000000001", "2800.00"])
def test_control_numerador_igual_o_mayor_que_el_exceso_se_sigue_explicando(numerator):
    # Frontera: IGUAL al exceso es válido (un episodio de un solo día tiene numerador == exceso), y 1e-12
    # por encima también. Evita una implementación que use `<=` en lugar de `<`.
    snapshot = make_snapshot(days=1, through=OPENED)
    snapshot["operands"]["impact_numerator"] = Decimal(numerator)
    assert explain(snapshot)["anomaly_evidence"]["operands"]["accumulated_impact_times_seven"] == numerator


def test_control_numerador_igual_al_exceso_con_doce_decimales_se_sigue_explicando():
    # Exceso exacto con cifras como las guarda la tabla (12 decimales): 550.123456789012 * 7 - 2800.00
    # = 3850.864197523084 - 2800.00 = 1050.864197523084. Sin redondeos previos, la igualdad es exacta.
    snapshot = make_snapshot(reference="2800.00", observed="550.123456789012", numerator="1050.864197523084", days=1,
                             through=OPENED)
    assert explain(snapshot)["anomaly_evidence"]["operands"]["accumulated_impact_times_seven"] == "1050.864197523084"


def test_numerador_un_picometro_por_debajo_del_exceso_con_doce_decimales_no_se_explica():
    # Misma cifra que el control anterior, 1e-12 por debajo: debe rechazarse (no hay tolerancia).
    snapshot = make_snapshot(reference="2800.00", observed="550.123456789012", numerator="1050.864197523083", days=1,
                             through=OPENED)
    assert_unavailable(snapshot)


# --------------------------------------------------------------------------------------------------
# Invariante 6: un episodio cerrado tiene un motivo de cierre con texto
# --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["resolved", "false_positive"])
@pytest.mark.parametrize("reason", ["", " ", "   ", "\t\n", None, 5, b"x", ["Hecho"]],
                         ids=["vacio", "un-espacio", "espacios", "tabulador-y-salto", "none", "entero", "bytes", "lista"])
def test_cierre_sin_motivo_con_texto_no_se_explica(status, reason):
    # El cierre exige un motivo real (la API de estados lo exige al cerrar). Uno vacío, de solo espacios o que
    # no es texto no puede salir de un cierre auténtico y se imprimiría como «con el motivo "".».
    assert_unavailable(closed_snapshot(status, reason))


@pytest.mark.parametrize("status", ["resolved", "false_positive"])
@pytest.mark.parametrize("reason", ["x", "Hecho", " con espacios dentro "])
def test_control_cierre_con_motivo_no_vacio_se_sigue_explicando(status, reason):
    # Frontera: un motivo de UN carácter es válido; un motivo con espacios alrededor pero con contenido
    # también (solo se rechaza el que no tiene nada que no sea espacio).
    result = explain(closed_snapshot(status, reason))
    assert result["anomaly_evidence"]["episode"]["closure_reason"] == reason


def test_motivo_vacio_en_un_episodio_abierto_no_se_rechaza():
    # El motivo de cierre solo es obligatorio al cerrar: un episodio abierto con motivo "" (dato irrelevante)
    # no debe volverse no explicable por esta regla.
    snapshot = make_snapshot()
    snapshot["episode"]["closure_reason"] = ""
    assert explain(snapshot)["anomaly_evidence"]["status"] == "ok"


# --------------------------------------------------------------------------------------------------
# Invariante 7: operandos Decimal, finitos, no negativos, con <= 38 dígitos y exponente ajustado <= 25
# --------------------------------------------------------------------------------------------------

OPERANDS = ("reference_week_cost", "opening_observed_cost", "impact_numerator")
BASE = {"reference_week_cost": Decimal("2800.00"), "opening_observed_cost": Decimal("550.00"),
        "impact_numerator": Decimal("2800.00")}

# Tripletas (referencia, observado, numerador) con 38 cifras significativas en UN operando (frontera válida) y con 39
# (primer valor rechazable). La columna es NUMERIC(38,12): 38 cifras con a lo sumo 12 decimales son 26 enteras, así que
# el operando grande ya no puede mezclarse con los pequeños de base (2800 y 550) sin dejar de cumplir la regla de
# apertura; por eso cada tripleta es coherente por sí sola (el observado cumple la regla y el numerador no baja del
# exceso). Dígitos distintos de cero (sin ceros finales) para no depender de cómo se cuentan.
ELEVEN_26 = "1" * 26
DIGITS_38 = {
    # R = 1.11e25; O = 3e24: exceso = 2.1e25 - 1.11e25 = 9.9e24 > 20 % de R y <= N = 2e25.
    "reference_week_cost": (Decimal(ELEVEN_26 + "." + "1" * 12), Decimal("3000000000000000000000000"),
                            Decimal("20000000000000000000000000")),
    # O = 1.11e25; R = 1e25: exceso = 7.78e25 - 1e25 = 6.78e25 <= N = 7e25 (exponente ajustado 25).
    "opening_observed_cost": (Decimal("1e25"), Decimal(ELEVEN_26 + "." + "1" * 12),
                              Decimal("70000000000000000000000000")),
    # R y O pequeños de base (exceso 1050 <= N); solo el numerador tiene las 38 cifras.
    "impact_numerator": (Decimal("2800.00"), Decimal("550.00"), Decimal(ELEVEN_26 + "." + "1" * 12)),
}
DIGITS_39 = {
    "reference_week_cost": (Decimal(ELEVEN_26 + "." + "1" * 13), DIGITS_38["reference_week_cost"][1],
                            DIGITS_38["reference_week_cost"][2]),
    "opening_observed_cost": (DIGITS_38["opening_observed_cost"][0], Decimal(ELEVEN_26 + "." + "1" * 13),
                              DIGITS_38["opening_observed_cost"][2]),
    "impact_numerator": (Decimal("2800.00"), Decimal("550.00"), Decimal(ELEVEN_26 + "." + "1" * 13)),
}

NOT_DECIMAL = [
    pytest.param("2800.00", id="cadena"),
    pytest.param(2800.0, id="float"),
    pytest.param(2800, id="int"),
    pytest.param(True, id="bool"),
    pytest.param(None, id="none"),
]
NOT_FINITE = [
    pytest.param(Decimal("NaN"), id="nan"),
    pytest.param(Decimal("sNaN"), id="snan"),
    pytest.param(Decimal("Infinity"), id="infinito"),
    pytest.param(Decimal("-Infinity"), id="menos-infinito"),
]


def _snapshot_with(name, value):
    operands = dict(BASE)
    operands[name] = value
    return with_operands(operands["reference_week_cost"], operands["opening_observed_cost"],
                         operands["impact_numerator"])


@pytest.mark.parametrize("name", OPERANDS)
@pytest.mark.parametrize("value", NOT_DECIMAL)
def test_operando_que_no_es_decimal_no_se_explica(name, value):
    # Un importe guardado tiene que llegar como `Decimal`. Un `int` o `float` no tienen la exactitud contractual
    # y un `str` o `None` harían saltar `TypeError` (un 500) en vez de un 409.
    assert_unavailable(_snapshot_with(name, value))


@pytest.mark.parametrize("name", OPERANDS)
@pytest.mark.parametrize("value", NOT_FINITE)
def test_operando_no_finito_no_se_explica_sin_otra_excepcion(name, value):
    # NaN, sNaN e infinitos: hoy saltan `decimal.InvalidOperation` al comparar o redondear (un 500). El nuevo
    # comportamiento es la excepción propia; `assert_unavailable` falla si sale cualquier otra.
    assert_unavailable(_snapshot_with(name, value))


@pytest.mark.parametrize("name", OPERANDS)
def test_operando_negativo_no_se_explica(name):
    # Un coste acumulado negativo no es un episodio real (hoy el referencia/observado negativo ya se rechazaba
    # por la regla de apertura, pero un numerador negativo se explicaba).
    assert_unavailable(_snapshot_with(name, Decimal("-1")))


@pytest.mark.parametrize("name", OPERANDS)
def test_operando_con_mas_de_38_digitos_significativos_no_se_explica(name):
    # El límite de 38 dígitos acota el coste de la aritmética exacta. Con a lo sumo 12 decimales, una cifra más
    # solo cabe como un decimal 13 (o como un entero 27, que rechaza el exponente): la tripleta es coherente.
    assert len(DIGITS_39[name][OPERANDS.index(name)].as_tuple().digits) == 39
    assert_unavailable(with_operands(*DIGITS_39[name]))


@pytest.mark.parametrize("name", OPERANDS)
def test_control_operando_con_38_digitos_se_sigue_explicando(name):
    # Frontera: justo 38 cifras significativas es válido (evita un límite fuera de uno: `>= 38`).
    assert len(DIGITS_38[name][OPERANDS.index(name)].as_tuple().digits) == 38
    assert explain(with_operands(*DIGITS_38[name]))["anomaly_evidence"]["status"] == "ok"


# Triples (referencia, observado, numerador) COHERENTES entre sí (el observado cumple la regla de apertura y el
# numerador no baja del exceso) en los que un único operando se sale del rango de exponente: así el rechazo solo
# puede deberse al rango y no al resto de invariantes.
OUT_OF_RANGE = [
    pytest.param(Decimal("1e26"), Decimal("2e25"), Decimal("5e25"), id="referencia-1e26"),
    pytest.param(Decimal("1e25"), Decimal("2e26"), Decimal("1.4e27"), id="observado-2e26"),
    pytest.param(Decimal("1e25"), Decimal("3e24"), Decimal("1e26"), id="numerador-1e26"),
    pytest.param(Decimal("1e200"), Decimal("2e199"), Decimal("5e199"), id="los-tres-1e200"),
    pytest.param(Decimal(int("1" * 130)), Decimal(int("1" * 130)), Decimal(int("1" * 130) * 6), id="los-tres-130-digitos"),
]


@pytest.mark.parametrize(("reference", "observed", "numerator"), OUT_OF_RANGE)
def test_operandos_fuera_de_rango_no_se_explican_sin_otra_excepcion(reference, observed, numerator):
    # Magnitudes enormes (1e200, 130 dígitos): hoy `money()` salta `decimal.InvalidOperation` al redondear.
    assert_unavailable(with_operands(reference, observed, numerator))


# Triples en la frontera EXACTA del rango: exponente ajustado 25 (26 dígitos enteros) es válido. Cada triple cumple
# la regla de apertura y numerador >= exceso, para que solo el rango pudiera rechazarlos.
IN_RANGE_BOUNDARY = [
    # R = 99999999999999999999999999 (26 nueves), O = 2e25, exceso = 1.4e26 - R = 40000000000000000000000001 <= 5e25.
    pytest.param(Decimal("9" * 26), Decimal("2e25"), Decimal("5e25"), id="referencia-26-nueves"),
    # R = 1e25 (exponente ajustado 25), O = 3e24, exceso = 2.1e25 - 1e25 = 1.1e25 <= 2e25.
    pytest.param(Decimal("1e25"), Decimal("3e24"), Decimal("2e25"), id="referencia-1e25"),
    # Observado y numerador en la frontera: O = 9...9 (26 dígitos), R = 9e25, exceso = 7*O - R ~= 6.1e26 > 1e26,
    # no cabe en el rango; por eso la frontera del numerador se prueba con un O pequeño.
    pytest.param(Decimal("1e25"), Decimal("3e24"), Decimal("9" * 26), id="numerador-26-nueves"),
    # O = 1.8e24: exceso = 1.26e25 - 1e25 = 2.6e24 > 20 % de R (2e24) y <= N = 1e25. Con O = 3e24 el exceso (1.1e25)
    # superaría a N y lo rechazaría la invariante 5, no el rango.
    pytest.param(Decimal("1e25"), Decimal("1.8e24"), Decimal("1e25"), id="numerador-1e25"),
]


@pytest.mark.parametrize(("reference", "observed", "numerator"), IN_RANGE_BOUNDARY)
def test_control_operandos_en_la_frontera_del_rango_se_siguen_explicando(reference, observed, numerator):
    # Frontera: 26 nueves y 1e25 caben en el rango (exponente ajustado 25), no deben rechazarse; evita una
    # implementación que corte en 1e25 o en 1e24 por error de uno.
    assert explain(with_operands(reference, observed, numerator))["anomaly_evidence"]["status"] == "ok"


def test_control_doce_decimales_como_los_guarda_la_tabla_se_sigue_explicando():
    # Los importes de la tabla se guardan con 12 decimales: Decimal("2800.000000000000") no debe rechazarse por
    # sus ceros finales (16 dígitos, muy por debajo del límite).
    snapshot = with_operands(Decimal("2800.000000000000"), Decimal("550.000000000000"), Decimal("2800.000000000000"))
    result = explain(snapshot)
    assert result["anomaly_evidence"]["operands"] == {
        "reference_seven_day_total": "2800.000000000000", "opening_observed_cost": "550.000000000000",
        "accumulated_impact_times_seven": "2800.000000000000"}


# --------------------------------------------------------------------------------------------------
# Controles generales: lo que ya se explicaba se sigue explicando
# --------------------------------------------------------------------------------------------------

def test_control_el_snapshot_valido_se_explica_y_no_se_muta():
    # Línea base de todas las pruebas de este archivo: si fallara, el resto no probaría nada.
    snapshot = make_snapshot()
    before = copy.deepcopy(snapshot)
    result = explain(snapshot)
    assert result["anomaly_evidence"]["status"] == "ok"
    assert snapshot == before


def test_control_no_observado_desde_una_fecha_con_cierre_abierto_se_sigue_explicando():
    result = explain(make_snapshot(observation="no_longer_observed", no_longer_observed_on=date(2026, 9, 20)))
    assert "Ya no se observa desde 2026-09-20" in result["content"]


def test_control_usd_con_numerador_en_el_exceso_se_sigue_explicando():
    result = explain(make_snapshot(currency="USD", days=1, through=OPENED, numerator="1050.00"))
    assert result["anomaly_evidence"]["episode"]["currency"] == "USD"
