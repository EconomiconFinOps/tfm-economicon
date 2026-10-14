"""JUP-038 (tarea 4.7): remediación de mutación sobre `AnomalySelection.episode_id`.

Mutante que se mata: `Field(strict=True)` -> `Field(strict=False)` en
`app.schemas.anomaly_explanations`. Las pruebas de `test_anomaly_explanation_schema.py` solo envían
`str` (válidos o con el formato roto), así que el modo laxo de pydantic v2 pasaba inadvertido: en
modo laxo `bytes` y `bytearray` se decodifican a `str` y un identificador válido en bytes se aceptaría.

Por qué importa: el identificador del episodio es una selección estructurada, no texto libre. Con
`strict=True` el valor debe llegar ya como `str`; cualquier otro tipo se rechaza en lugar de
coaccionarse, de modo que lo que valida la expresión regular es exactamente lo que se guarda.

Metodología: cada rechazo va emparejado con su control positivo (el mismo identificador como `str`
SÍ se acepta). Así la prueba no puede pasar por vacuidad (p. ej. por un identificador mal formado
o por un campo desconocido) y solo falla/pasa por el tipo del valor.

No hay HTTP ni base de datos: solo validación de pydantic.
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.anomaly_explanations import AnomalySelection
from app.schemas.assistant import MessageCreateRequest

VALID_ID = "anomaly-" + "a" * 64


class StrSubclass(str):
    """Subclase de `str`: sigue siendo una instancia de `str`, así que la rigidez no debe rechazarla."""


# Valores de tipo no `str` que el modo laxo coaccionaría o decodificaría. Todos deben rechazarse.
# `bytes`/`bytearray` llevan un identificador por lo demás válido: es el caso que mata el mutante,
# porque en modo laxo se decodifican a "anomaly-aaaa..." y pasarían la expresión regular.
NON_STR_VALUES = [
    pytest.param(VALID_ID.encode("ascii"), id="bytes-con-id-valido"),
    pytest.param(bytearray(VALID_ID.encode("ascii")), id="bytearray-con-id-valido"),
]

# Otros tipos que el modo laxo de pydantic v2 no convertiría a `str` (o que no podrían cumplir el
# formato), pero que documentan que la selección no admite nada que no sea texto. Estas no matan por
# sí solas el mutante; fijan el contrato de tipos del identificador.
OTHER_NON_STR_VALUES = [
    pytest.param(12345, id="int"),
    pytest.param(1.5, id="float"),
    pytest.param(Decimal("1.5"), id="decimal"),
    pytest.param(True, id="bool"),
    pytest.param(None, id="none"),
    pytest.param(["a"], id="lista-de-un-caracter"),
]


@pytest.mark.parametrize("value", NON_STR_VALUES)
def test_selection_rejects_bytes_like_episode_id(value):
    """Mata `strict=False`: `bytes`/`bytearray` con un id válido no deben decodificarse a `str`."""
    # Control positivo: el mismo identificador como `str` se acepta, así que el rechazo de abajo
    # se debe únicamente al tipo del valor.
    assert AnomalySelection.model_validate({"episode_id": VALID_ID}).episode_id == VALID_ID

    with pytest.raises(ValidationError) as excinfo:
        AnomalySelection.model_validate({"episode_id": value})

    # El error debe apuntar al campo `episode_id`, no a otra causa (p. ej. un campo extra).
    assert [error["loc"] for error in excinfo.value.errors()] == [("episode_id",)]


@pytest.mark.parametrize("value", NON_STR_VALUES)
def test_message_request_rejects_bytes_like_anomaly_episode_id(value):
    """Mata `strict=False` a través de `MessageCreateRequest.anomaly_query` (ruta real del cuerpo)."""
    # Control positivo: la misma petición con el id como `str` es válida, de modo que el rechazo no
    # puede deberse a un campo desconocido ni a otra regla de la petición.
    accepted = MessageCreateRequest.model_validate(
        {"content": "x", "anomaly_query": {"episode_id": VALID_ID}}
    )
    assert accepted.anomaly_query is not None
    assert accepted.anomaly_query.episode_id == VALID_ID

    with pytest.raises(ValidationError) as excinfo:
        MessageCreateRequest.model_validate({"content": "x", "anomaly_query": {"episode_id": value}})

    assert [error["loc"] for error in excinfo.value.errors()] == [("anomaly_query", "episode_id")]


@pytest.mark.parametrize("value", OTHER_NON_STR_VALUES)
def test_selection_rejects_other_non_str_types(value):
    """Contrato de tipos: ni números, booleanos, `None` ni listas se aceptan como identificador."""
    # Control positivo para que el rechazo dependa solo del tipo.
    assert AnomalySelection.model_validate({"episode_id": VALID_ID}).episode_id == VALID_ID

    with pytest.raises(ValidationError):
        AnomalySelection.model_validate({"episode_id": value})


def test_selection_accepts_str_subclass_with_valid_id():
    """Documenta el alcance de la rigidez: una subclase de `str` sigue siendo un `str` y se acepta.

    `strict=True` exige que el valor sea una instancia de `str`, no que su tipo sea exactamente `str`.
    Lo que se rechaza es lo que NO es texto (bytes, números...), no un `str` especializado.
    """
    value = StrSubclass(VALID_ID)

    selection = AnomalySelection.model_validate({"episode_id": value})

    assert selection.episode_id == VALID_ID
