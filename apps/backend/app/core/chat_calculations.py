"""Prose guard for typed expressions; no legacy calculation plans or slots."""

import re

CALCULATION_RULES = {
    "Calculation text type.": "calculation_text_type",
    "Free numeric equation forbidden.": "calculation_free_numeric_equation_forbidden",
    "Unknown calculation slot.": "calculation_unknown_calculation_slot",
}


class CalculationError(ValueError):
    def __init__(self, message):
        self.rule_code = CALCULATION_RULES.get(message, "calculation_invalid")
        super().__init__("Invalid calculation.")


_NUMBER = r"-?[0-9]+(?:[.,][0-9]+)?"
_UNIT = r"(?:\s*[A-Za-zÀ-ÿ€$%][A-Za-zÀ-ÿ€$%/ ]{0,31})?"
_FREE_EQUATION = re.compile(
    _NUMBER
    + _UNIT
    + r"\s*(?:[+×*/xX÷]|-(?!>)|>=?|<=?|==)\s*"
    + _NUMBER
    + _UNIT
    + r"[^\n]{0,64}?(?:=|≈|→|->)\s*(?:"
    + _NUMBER
    + r"|verdadero|falso|true|false)",
    re.IGNORECASE,
)


def render_text(text, records):
    if not isinstance(text, str):
        raise CalculationError("Calculation text type.")
    normalized = (
        text.replace("−", "-").replace("**", "").replace("__", "").replace("`", "")
    )
    if _FREE_EQUATION.search(normalized):
        raise CalculationError("Free numeric equation forbidden.")
    if records or "[[calc:" in text:
        raise CalculationError("Unknown calculation slot.")
    return text
