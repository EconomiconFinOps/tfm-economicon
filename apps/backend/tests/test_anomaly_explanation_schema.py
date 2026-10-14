"""JUP-038 (tarea 4.1): selección estructurada de una anomalía en el cuerpo del mensaje.

Qué se valida: la clase `AnomalySelection` (`app.schemas.anomaly_explanations`) y su integración en
`MessageCreateRequest` (`anomaly_query`, excluyente con `ownership_query`). No hay HTTP ni base de datos.

Metodología:
- El identificador de episodio debe cumplir EXACTAMENTE `^anomaly-[0-9a-f]{64}$` con coincidencia
  completa. Los casos rechazados son los bordes que suelen colarse con una expresión regular mal
  anclada: salto de línea final (`$` de Python lo acepta), mayúsculas, longitudes 63/65, dígitos
  unicode que `\\d` sí aceptaría y letras de ancho completo.
- Un campo extra (en especial `tenant_id` o `user_id`) se rechaza: el cliente y el usuario salen de la
  sesión, nunca del cuerpo.
- El módulo nuevo se importa dentro de cada prueba (`selection_class`) para que, mientras no exista,
  falle cada prueba por separado y no un único error de colección.
- `MessageCreateRequest` ya tiene `extra="forbid"`, así que hoy RECHAZA `anomaly_query` por ser un campo
  desconocido. Por eso cada prueba de rechazo exige primero que la misma petición sin el defecto SÍ se
  acepte: así no pueden pasar por el motivo equivocado (campo desconocido) y solo se cumplen cuando el
  campo existe y el rechazo viene de la validación real.
"""
import importlib

import pytest
from pydantic import ValidationError

from app.schemas.assistant import MessageCreateRequest
from app.schemas.ownership import OwnershipSelection

VALID_ID = "anomaly-" + "a" * 64
VALID_MIXED_ID = "anomaly-" + "0123456789abcdef" * 4
OWNERSHIP = {"group_by": "application", "start_date": "2024-06-01", "end_date": "2024-07-01"}


def selection_class():
    """Importa la clase en el momento de usarla (ver el docstring del módulo)."""
    return importlib.import_module("app.schemas.anomaly_explanations").AnomalySelection


# Identificadores que NO cumplen el formato. Cada uno rompe una sola parte de la expresión.
INVALID_IDS = [
    pytest.param("", id="vacio"),
    pytest.param("anomaly-", id="prefijo-sin-hex"),
    pytest.param("anomaly-" + "a" * 63, id="63-hex"),
    pytest.param("anomaly-" + "a" * 65, id="65-hex"),
    pytest.param("anomaly-" + "a" * 8, id="corto"),
    pytest.param("anomaly-" + "a" * 128, id="largo"),
    pytest.param("anomaly-" + "A" * 64, id="hex-en-mayusculas"),
    pytest.param("anomaly-" + "a" * 63 + "A", id="una-mayuscula-al-final"),
    pytest.param("ANOMALY-" + "a" * 64, id="prefijo-en-mayusculas"),
    pytest.param("episode-" + "a" * 64, id="prefijo-distinto"),
    pytest.param("a" * 64, id="sin-prefijo"),
    pytest.param("anomaly" + "a" * 64, id="sin-guion"),
    pytest.param("anomaly-" + "a" * 64 + "\n", id="salto-de-linea-final"),
    pytest.param("\nanomaly-" + "a" * 64, id="salto-de-linea-inicial"),
    pytest.param("anomaly-" + "a" * 64 + " ", id="espacio-final"),
    pytest.param(" anomaly-" + "a" * 64, id="espacio-inicial"),
    pytest.param("anomaly-" + "a" * 32 + " " + "a" * 31, id="espacio-intermedio"),
    pytest.param("anomaly-" + "a" * 63 + "g", id="caracter-fuera-de-hex"),
    pytest.param("anomaly-" + "g" * 64, id="todo-fuera-de-hex"),
    pytest.param("anomaly-" + "٠" * 64, id="digitos-arabes-indicos"),
    pytest.param("anomaly-" + "ａ" * 64, id="ancho-completo"),
    pytest.param("anomaly-" + "a" * 63 + "é", id="letra-acentuada"),
    pytest.param(123, id="entero"),
    pytest.param(None, id="none"),
    pytest.param([VALID_ID], id="lista"),
    pytest.param({"id": VALID_ID}, id="dict"),
]


def test_acepta_un_identificador_valido_y_lo_conserva_tal_cual():
    # Caso feliz: 64 hex en minúsculas. También se prueba una mezcla de dígitos y letras a-f para no
    # aceptar solo el caso de letras repetidas.
    cls = selection_class()
    assert cls(episode_id=VALID_ID).episode_id == VALID_ID
    assert cls.model_validate({"episode_id": VALID_MIXED_ID}).episode_id == VALID_MIXED_ID
    assert cls(episode_id="anomaly-" + "0" * 64).episode_id == "anomaly-" + "0" * 64
    assert cls(episode_id="anomaly-" + "f" * 64).episode_id == "anomaly-" + "f" * 64


def test_la_seleccion_solo_tiene_el_campo_episode_id():
    # Contrato: un único campo. Si apareciera otro (cliente, usuario) podría usarse como autoridad.
    assert list(selection_class().model_fields) == ["episode_id"]


@pytest.mark.parametrize("episode_id", INVALID_IDS)
def test_rechaza_identificadores_con_otro_formato(episode_id):
    # Control: la clase existe y acepta un id válido (si no, el rechazo sería por la razón equivocada).
    cls = selection_class()
    assert cls(episode_id=VALID_ID).episode_id == VALID_ID
    with pytest.raises(ValidationError):
        cls.model_validate({"episode_id": episode_id})


def test_rechaza_cuando_falta_el_identificador():
    cls = selection_class()
    assert cls(episode_id=VALID_ID)
    with pytest.raises(ValidationError):
        cls.model_validate({})


@pytest.mark.parametrize("extra", [
    {"tenant_id": "tenant-b"},
    {"user_id": "bob"},
    {"extra": "x"},
    {"tenant_id": "tenant-a", "user_id": "alice"},
])
def test_rechaza_campos_extra_incluidos_cliente_y_usuario(extra):
    # El cliente y el usuario salen de la sesión: aunque coincidan con los de la sesión, no se admiten
    # en el cuerpo (`extra="forbid"`).
    cls = selection_class()
    assert cls.model_validate({"episode_id": VALID_ID}).episode_id == VALID_ID
    with pytest.raises(ValidationError) as caught:
        cls.model_validate({"episode_id": VALID_ID, **extra})
    assert {error["type"] for error in caught.value.errors()} == {"extra_forbidden"}


# --------------------------------------------------------------------------------------------------
# Integración en MessageCreateRequest
# --------------------------------------------------------------------------------------------------

def test_el_mensaje_acepta_solo_anomaly_query_y_lo_convierte_en_la_seleccion():
    message = MessageCreateRequest.model_validate({"content": "¿Por qué?", "anomaly_query": {"episode_id": VALID_ID}})
    assert isinstance(message.anomaly_query, selection_class())
    assert message.anomaly_query.episode_id == VALID_ID
    assert message.ownership_query is None
    assert message.content == "¿Por qué?"


def test_sin_anomaly_query_el_campo_queda_en_none_y_las_peticiones_de_hoy_validan_igual():
    # Compatibilidad: una pregunta documental o de costes por propiedad no cambia. Se comprueba además
    # que existe el campo nuevo (no es solo un atributo ausente).
    assert "anomaly_query" in MessageCreateRequest.model_fields
    plain = MessageCreateRequest(content="Costes")
    assert plain.anomaly_query is None and plain.ownership_query is None
    owned = MessageCreateRequest.model_validate({"content": "Gasto", "ownership_query": OWNERSHIP})
    assert owned.anomaly_query is None
    assert owned.ownership_query == OwnershipSelection(**OWNERSHIP)
    # `anomaly_query` enviado explícitamente como null equivale a no enviarlo y deja pasar la otra selección.
    explicit_none = MessageCreateRequest.model_validate(
        {"content": "Gasto", "anomaly_query": None, "ownership_query": OWNERSHIP})
    assert explicit_none.anomaly_query is None and explicit_none.ownership_query is not None


def test_el_mensaje_rechaza_las_dos_selecciones_a_la_vez():
    # Excluyentes: ninguna de las dos gana en silencio. Control previo: cada una por separado es válida,
    # de modo que el rechazo no se pueda explicar por un campo desconocido (ver docstring del módulo).
    only_anomaly = {"content": "x", "anomaly_query": {"episode_id": VALID_ID}}
    only_ownership = {"content": "x", "ownership_query": OWNERSHIP}
    assert MessageCreateRequest.model_validate(only_anomaly).anomaly_query is not None
    assert MessageCreateRequest.model_validate(only_ownership).ownership_query is not None
    with pytest.raises(ValidationError) as caught:
        MessageCreateRequest.model_validate({**only_anomaly, **only_ownership})
    assert "extra_forbidden" not in {error["type"] for error in caught.value.errors()}


@pytest.mark.parametrize("episode_id", [
    "anomaly-" + "a" * 63, "anomaly-" + "A" * 64, "anomaly-" + "a" * 64 + "\n", "", "ANOMALY-" + "a" * 64,
])
def test_el_mensaje_rechaza_un_identificador_invalido_dentro_de_anomaly_query(episode_id):
    # El formato también se exige a través del mensaje (es lo que recibe la ruta). Control: el válido pasa.
    assert MessageCreateRequest.model_validate(
        {"content": "x", "anomaly_query": {"episode_id": VALID_ID}}).anomaly_query is not None
    with pytest.raises(ValidationError):
        MessageCreateRequest.model_validate({"content": "x", "anomaly_query": {"episode_id": episode_id}})


@pytest.mark.parametrize("extra", [{"tenant_id": "tenant-b"}, {"user_id": "bob"}, {"extra": 1}])
def test_el_mensaje_rechaza_campos_extra_dentro_de_anomaly_query(extra):
    assert MessageCreateRequest.model_validate(
        {"content": "x", "anomaly_query": {"episode_id": VALID_ID}}).anomaly_query is not None
    with pytest.raises(ValidationError):
        MessageCreateRequest.model_validate({"content": "x", "anomaly_query": {"episode_id": VALID_ID, **extra}})


def test_el_mensaje_sigue_rechazando_campos_desconocidos_y_contenido_vacio():
    # No se debilita lo que ya existía al añadir el campo nuevo.
    assert MessageCreateRequest.model_validate(
        {"content": "x", "anomaly_query": {"episode_id": VALID_ID}}).anomaly_query is not None
    with pytest.raises(ValidationError):
        MessageCreateRequest.model_validate({"content": "x", "anomaly_query": {"episode_id": VALID_ID}, "tenant_id": "tenant-b"})
    with pytest.raises(ValidationError):
        MessageCreateRequest.model_validate({"content": "   ", "anomaly_query": {"episode_id": VALID_ID}})
