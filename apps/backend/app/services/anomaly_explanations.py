"""JUP-038: explicador puro de un episodio de anomalía de coste guardado.

Decisiones de diseño (change `jup-038-explain-anomaly-episodes`, design.md decisiones 2, 4, 5, 6 y 7):

- Módulo PURO: no abre conexiones, no lee configuración, no registra nada y no conoce FastAPI. Así se
  prueba sin base de datos y una futura herramienta del agente puede llamarlo tal cual. Tampoco usa
  `logging` ni `print`: el servicio y el motivo de cierre son datos del cliente y no deben salir del
  texto de la respuesta.
- El texto es una plantilla fija en español armada por código, sin modelo generativo: una explicación
  financiera tiene que poder recalcularse a mano y no puede inventar causas ni cifras.
- Solo se explica lo que se sabe explicar: ante una versión o unas reglas distintas, o unos operandos
  que no cumplen la regla, se lanza `ExplanationUnavailable` en lugar de aproximar.
"""
import copy
import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal, localcontext

# `display_label` se importa y no se copia: es el escape ya probado en JUP-037 y duplicarlo dejaría dos
# versiones del mismo saneamiento que podrían divergir. No se mueve a un módulo común para no tocar el
# archivo de JUP-037 ni sus pruebas (design.md, decisión 6).
from app.services.anomaly_episodes import LIMITATIONS, REFERENCE_DAYS, RULES, RULES_VERSION, money, severity, triggers
from app.services.ownership_questions import display_label

SCHEMA_VERSION = "1.0"
ADAPTER_VERSION = "anomaly-explanation-1.0"

# Palabras del panel de anomalías, para que el asistente y la interfaz no digan cosas distintas.
STATUS_WORDS = {"new": "Nueva", "investigating": "Investigando", "resolved": "Resuelta", "false_positive": "Falso positivo"}
CLOSED_STATUSES = ("resolved", "false_positive")
SEVERITY_WORDS = {"P1": "Alta (P1)", "P2": "Media (P2)", "P3": "Baja (P3)"}

# Precisión holgada para las divisiones entre 7 y el porcentaje: el redondeo ocurre una sola vez, al
# mostrar (`money`), y la división previa no debe perder cifras antes de ese momento.
_PRECISION = 120

# Límites de los operandos guardados (spec «Operandos no finitos o fuera de rango»).
# Los 38 dígitos son los de los costes de origen (`pretax_cost DECIMAL(38, 12)`, migración 002 del procesador),
# de los que salen los operandos del episodio por sumas y productos por 7. Las columnas del episodio, en
# cambio, son `DECIMAL` sin precisión y admiten más, por eso el explicador acota él mismo.
_MAX_DIGITS = 38
_MAX_ADJUSTED_EXPONENT = 25
# Decimales de esos mismos costes de origen (12): las sumas y los productos por 7 no añaden decimales, así que
# un valor con más no puede venir de ellos. Hace falta un tope propio porque el recuento de dígitos no lo
# cubre: un exponente negativo enorme como `1E-150` cuenta como un solo dígito y aun así hace fallar el
# redondeo, y `1E-999999` hace saltar `decimal.Overflow`.
_MAX_DECIMALS = 12
OBSERVATIONS = ("observed", "no_longer_observed")


class ExplanationUnavailable(Exception):
    """El episodio no se puede explicar con las reglas que este módulo conoce; no se devuelve nada."""


def _exact(value: Decimal) -> str:
    # `format(..., "f")` conserva el texto exacto del Decimal recibido y evita la notación científica.
    return format(value, "f")


def _iso(value):
    # `isoformat()` y no `model_dump(mode="json")` de pydantic: este escribe "Z" en lugar de "+00:00" y
    # la evidencia debe poder recalcularse a mano con el contrato.
    return value.isoformat() if isinstance(value, (date, datetime)) else copy.deepcopy(value)


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


def _days(count: int) -> str:
    return "1 día" if count == 1 else f"{count} días"


def _thresholds(rules: dict) -> tuple[str, str, str, str]:
    """Límites de criticidad leídos de las `rules` del episodio, no de constantes del explicador."""
    bands = rules["severity"]
    p1_limit = bands["P1"].removeprefix("> ")
    p2_low, p2_high = bands["P2"].split(" to ")
    p3_limit = bands["P3"].removeprefix("< ")
    return p1_limit, p2_low, p2_high, p3_limit


def _severity_label(code: str, rules: dict, currency: str) -> str:
    p1_limit, p2_low, p2_high, p3_limit = _thresholds(rules)
    if code == "P1":
        return f"{SEVERITY_WORDS[code]}, por encima de {p1_limit} {currency}"
    if code == "P2":
        return f"{SEVERITY_WORDS[code]}, entre {p2_low} y {p2_high} {currency}, ambos incluidos"
    return f"{SEVERITY_WORDS[code]}, por debajo de {p3_limit} {currency}"


def _is_valid_operand(value) -> bool:
    # `type(...) is Decimal` y no `isinstance`: descarta `bool`/`int`/`float`/`str`, que no tienen la
    # exactitud contractual, antes de llamar a métodos que solo existen en `Decimal`. `is_finite()` va
    # primero porque NaN e infinitos rompen toda comparación posterior.
    if type(value) is not Decimal or not value.is_finite() or value < 0:
        return False
    # 38 dígitos y exponente ajustado <= 25 acotan la aritmética exacta (7 y 100 veces el operando caben
    # de sobra en `_PRECISION`) y mantienen `money()` lejos de su límite de precisión.
    # El tope de decimales va después de `is_finite()`: solo en un `Decimal` finito el exponente es un
    # `int`; en NaN e infinitos es un texto ("n", "F") y compararlo con un número lanzaría `TypeError`.
    return (len(value.as_tuple().digits) <= _MAX_DIGITS and value.adjusted() <= _MAX_ADJUSTED_EXPONENT
            and value.as_tuple().exponent >= -_MAX_DECIMALS)


def _require_valid_operands(*operands) -> None:
    if not all(_is_valid_operand(operand) for operand in operands):
        raise ExplanationUnavailable()


def _require_coherent_episode(episode: dict) -> None:
    """Rechaza datos guardados que no pueden ser de un episodio real, en lugar de explicarlos como válidos."""
    days = episode["impact_day_count"]
    if (episode["observation"] not in OBSERVATIONS
            # Comparación exacta, sin normalizar: el contrato guarda "EUR" y " eur" no es esa moneda.
            or episode["currency"] not in episode["rules"]["currencies"]
            # `type(...) is int` porque `True` es un `int` para Python y no es un recuento de días.
            or type(days) is not int or days < 1
            or episode["impact_through_date"] < episode["start_date"]):
        raise ExplanationUnavailable()


def _require_impact_covers_opening(reference_total: Decimal, observed: Decimal, numerator: Decimal) -> None:
    # El impacto acumulado incluye el día de apertura, así que no puede ser menor que su exceso. Igual es
    # válido (episodio de un solo día). Sin tolerancia y con la precisión del resto de la aritmética.
    if numerator < observed * REFERENCE_DAYS - reference_total:
        raise ExplanationUnavailable()


def _state_line(episode: dict) -> str:
    status = episode["status"]
    if status not in STATUS_WORDS:
        raise ExplanationUnavailable()
    word = STATUS_WORDS[status]
    if status in CLOSED_STATUSES:
        # El cierre manda sobre la observación y la fecha se da en UTC: la hora local de quien cerró
        # podría mostrar otro día. El motivo es texto libre del cliente, de ahí `display_label`.
        reason = episode["closure_reason"]
        # Un cierre real exige motivo con texto (lo exige la API de estados); solo se pide al cerrar.
        if episode["closed_at"] is None or not isinstance(reason, str) or not reason.strip():
            raise ExplanationUnavailable()
        # La fecha de cierre es un hecho ya guardado, no «el día de hoy»: nunca se usa para elegir el día visible
        # (eso es de `reference_date`, JUP-119). Se formatea con `strftime` y no extrayendo el día de un instante,
        # porque la guardia de `test_reference_date.py` busca ese patrón de texto en todo el código de la aplicación.
        closed = _utc(episode["closed_at"]).strftime("%Y-%m-%d")
        return f"Estado: {word}. Cerrada el {closed} (UTC) con el motivo {display_label(episode['closure_reason'])}."
    if episode["observation"] == "no_longer_observed":
        if episode["no_longer_observed_on"] is None:
            raise ExplanationUnavailable()
        return (f"Estado: {word}. Ya no se observa desde {episode['no_longer_observed_on'].isoformat()}; "
                "sigue abierta hasta que una persona la cierre.")
    return f"Estado: {word}. Se sigue observando."


def _evidence_id(tenant_id: str, body: dict) -> str:
    # El cliente entra en el hash para que dos clientes con episodios idénticos tengan evidencias
    # distintas, pero no se guarda en la evidencia (como `cost_evidence`). `ensure_ascii=False` porque el
    # contrato fija UTF-8 sin escapar y así se puede recalcular a mano.
    canonical = json.dumps({"tenant": tenant_id, **body}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "anomaly-explanation:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def explain_episode(snapshot: dict, *, tenant_id: str, explained_at: datetime) -> dict:
    episode = snapshot["episode"]
    operands = snapshot["operands"]
    reference_total = operands["reference_week_cost"]
    observed = operands["opening_observed_cost"]
    numerator = operands["impact_numerator"]

    # Se rechaza ANTES de construir texto o evidencia: una explicación aproximada de una regla que no se
    # conoce es justo el mensaje inventado que se quiere evitar. La igualdad de `rules` es exacta.
    if episode["rules_version"] != RULES_VERSION or episode["rules"] != RULES:
        raise ExplanationUnavailable()
    # Los operandos se validan ANTES de cualquier comparación o cuenta: un NaN hace saltar
    # `InvalidOperation` al comparar y una magnitud enorme al redondear, y ambos acabarían en un 500.
    _require_valid_operands(reference_total, observed, numerator)
    _require_coherent_episode(episode)
    try:
        with localcontext() as context:
            context.prec = _PRECISION
            if not triggers(observed, reference_total):
                raise ExplanationUnavailable()
            _require_impact_covers_opening(reference_total, observed, numerator)
            # Aritmética exacta con Decimal y un único redondeo, al mostrar. Nunca se restan importes ya
            # redondeados: 100.004 se vería como "100.00, que no supera 100".
            reference_daily = reference_total / REFERENCE_DAYS
            excess_week = observed * REFERENCE_DAYS - reference_total
            absolute_increase = excess_week / REFERENCE_DAYS
            relative_increase = excess_week * 100 / reference_total
            impact = numerator / REFERENCE_DAYS
            shown = {"reference": money(reference_daily), "absolute": money(absolute_increase),
                     "relative": money(relative_increase), "impact": money(impact)}
        observed_shown = money(observed)
    except ArithmeticError:
        # Defensa en profundidad: la validación previa ya acota los operandos, pero si se le escapara otra
        # clase de error aritmético que no prevé (`ArithmeticError` cubre `InvalidOperation`,
        # `ZeroDivisionError` y también `decimal.Overflow`, que NO es `InvalidOperation`) es mejor un 409
        # sin explicación que un 500; la excepción original no se propaga porque puede arrastrar valores
        # del cliente.
        raise ExplanationUnavailable() from None

    rules = episode["rules"]
    currency = episode["currency"]
    # La criticidad se decide sobre el numerador EXACTO: la cifra mostrada ya está redondeada y 499.996
    # se muestra como 500.00 pero sigue siendo P3.
    code = severity(numerator)
    p1_limit, _, _, p3_limit = _thresholds(rules)
    absolute_threshold = rules["absolute_increase"]
    relative_threshold = rules["relative_increase_percent"]

    # Notas de redondeo: solo cuando la cifra mostrada coincide con el umbral con el que se compara, que
    # es cuando la explicación parecería contradecir la regla. Orden fijo: absoluta, relativa, impacto.
    notes, note_lines = [], []
    if Decimal(shown["absolute"]) == Decimal(absolute_threshold):
        notes.append("absolute_increase")
        note_lines.append(f"Nota de redondeo: la subida absoluta exacta supera el umbral de {absolute_threshold} {currency} "
                          "aunque la cifra mostrada, redondeada a dos decimales, coincida con él.")
    if Decimal(shown["relative"]) == Decimal(relative_threshold):
        notes.append("relative_increase")
        note_lines.append(f"Nota de redondeo: la subida relativa exacta supera el umbral del {relative_threshold} % "
                          "aunque la cifra mostrada, redondeada a dos decimales, coincida con él.")
    for band_code, limit, position in (("P3", p3_limit, "por debajo de"), ("P1", p1_limit, "por encima de")):
        if code == band_code and Decimal(shown["impact"]) == Decimal(limit):
            notes.append("accumulated_impact")
            note_lines.append(f"Nota de redondeo: el impacto acumulado exacto queda {position} {limit} {currency} "
                              "aunque la cifra mostrada, redondeada a dos decimales, coincida con ese límite.")

    state_line = _state_line(episode)
    service = episode["service"]
    service_text = "sin servicio informado" if service is None else f"en el servicio {display_label(service)}"
    explained = _utc(explained_at).isoformat()

    # La evidencia se arma entera antes del hash: `id` y `explained_at` quedan fuera de él para que el
    # mismo estado dé el mismo identificador aunque se explique en momentos distintos.
    body = {
        "schema_version": SCHEMA_VERSION, "adapter_version": ADAPTER_VERSION, "status": "ok",
        "source": {"kind": "anomaly_episodes", "rules_version": episode["rules_version"],
                   "data_as_of": episode["impact_through_date"].isoformat()},
        "episode": {key: _iso(value) for key, value in episode.items()},
        "operands": {"reference_seven_day_total": _exact(reference_total), "opening_observed_cost": _exact(observed),
                     "accumulated_impact_times_seven": _exact(numerator)},
        "opening": {"reference_daily_cost": shown["reference"], "observed_cost": observed_shown,
                    "absolute_increase": shown["absolute"], "relative_increase_percent": shown["relative"],
                    "absolute_threshold": absolute_threshold, "relative_threshold_percent": relative_threshold,
                    "conditions_met": True},
        "impact": {"accumulated_impact": shown["impact"], "day_count": episode["impact_day_count"],
                   "through_date": episode["impact_through_date"].isoformat(), "severity": code,
                   "severity_band": rules["severity"][code]},
        "rounding_notes": notes, "includes_synthetic_data": snapshot["includes_synthetic_data"],
        "cause_status": "not_established", "assumptions": [], "limitations": list(LIMITATIONS),
    }
    evidence_id = _evidence_id(tenant_id, body)
    evidence = {"id": evidence_id, **body, "explained_at": explained}

    # Plantilla fija, una línea por frase. Los datos del cliente ya van escapados y entrecomillados en una
    # sola línea, así que no pueden hacerse pasar por otra frase de la respuesta.
    lines = [
        f"Anomalía candidata {service_text} ({currency}).",
        f"Por qué se marcó: el {episode['start_date'].isoformat()} el coste observado fue {observed_shown} {currency} "
        f"frente a una referencia de {shown['reference']} {currency} al día (media de los 7 días anteriores a la "
        f"apertura). Subió {shown['absolute']} {currency} ({shown['relative']} %).",
        f"Regla {episode['rules_version']}: un día se marca solo si supera la referencia en más de "
        f"{absolute_threshold} {currency} y en más de un {relative_threshold} %, las dos condiciones a la vez. "
        "Este día cumple las dos.",
        f"Impacto acumulado: {shown['impact']} {currency} en {_days(episode['impact_day_count'])}, hasta el "
        f"{episode['impact_through_date'].isoformat()}. Criticidad: {_severity_label(code, rules, currency)}.",
        *note_lines,
        state_line,
    ]
    if episode["previous_episode_id"] is not None:
        lines.append(f"Este servicio ya tuvo una anomalía anterior: {episode['previous_episode_id']}.")
    lines += [
        "Causa no establecida: es un candidato para investigar, no una causa demostrada ni un ahorro.",
        "Limitaciones:",
        *(f"- {text}" for text in LIMITATIONS),
    ]
    if snapshot["includes_synthetic_data"]:
        lines.append("Aviso: los datos de este cliente incluyen datos sintéticos de demostración.")
    lines += [
        "Alcance: esta explicación cubre el día de apertura y los acumulados; no hay detalle día a día.",
        f"Fotografía tomada el {explained} (UTC).",
        f"Evidencia: {evidence_id}.",
    ]
    return {"content": "\n".join(lines), "anomaly_evidence": evidence}
