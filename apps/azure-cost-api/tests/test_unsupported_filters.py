from copy import deepcopy

import pytest

from test_query_api import CASES_BY_ID, post_query

# Filtros validos reutilizados como hermanos del filtro invalido y como control positivo.
OK_DIMENSION = {"dimensions": {"name": "ServiceName", "operator": "In", "values": ["Storage"]}}
OK_TAG = {"tags": {"name": "env", "operator": "In", "values": ["prod"]}}
BAD_DIMENSION = {"dimensions": {"name": "NoSuchDimension", "operator": "In", "values": ["x"]}}
BAD_TAG = {"tags": {"name": "NoSuchTag", "operator": "In", "values": ["x"]}}

# Posicion del hijo invalido: raiz y distintos anidamientos. Discriminan que la validacion
# recorra TODOS los hijos (primero, medio, ultimo) y TANTO `and` como `or`, a cualquier profundidad.
POSITIONS = {
    "raiz": lambda bad: bad,
    "and-primero": lambda bad: {"and": [bad, OK_TAG]},
    "and-ultimo": lambda bad: {"and": [OK_DIMENSION, bad]},
    "and-medio": lambda bad: {"and": [OK_DIMENSION, bad, OK_TAG]},
    "or-ultimo": lambda bad: {"or": [OK_DIMENSION, bad]},
    "or-primero": lambda bad: {"or": [bad, OK_DIMENSION]},
    "and-dentro-de-or": lambda bad: {"or": [OK_TAG, {"and": [OK_DIMENSION, bad]}]},
    "or-dentro-de-and": lambda bad: {"and": [OK_DIMENSION, {"or": [OK_TAG, bad]}]},
}


def query_with(*, filter=None, grouping=None):
    body = deepcopy(CASES_BY_ID["storage-only"]["request"])
    body["dataset"].pop("filter")
    if filter is not None:
        body["dataset"]["filter"] = filter
    if grouping is not None:
        body["dataset"]["grouping"] = [grouping]
    return body


def assert_bad_request(response, message):
    # Cuerpo exacto: forma de error de Azure y ni `properties` ni filas (no se filtran datos).
    assert response.status_code == 400
    assert response.json() == {"error": {"code": "BadRequest", "message": message}}


@pytest.mark.parametrize("position", POSITIONS)
@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (BAD_DIMENSION, "Unsupported dimension: NoSuchDimension"),
        (BAD_TAG, "Unsupported tag: NoSuchTag"),
    ],
    ids=["dimension", "tag"],
)
def test_unsupported_filter_name_is_rejected_at_any_position(client, position, bad, message):
    # Un nombre no soportado en un filtro se rechaza; nunca se ignora ni da 200 (vacio o filtrado).
    response = post_query(client, query_with(filter=POSITIONS[position](bad)))

    assert_bad_request(response, message)


@pytest.mark.parametrize(
    ("name", "field", "message"),
    [
        ("NoSuchTag", "grouping-tag", "Unsupported tag: NoSuchTag"),
        # Dimensiones y etiquetas son conjuntos distintos: un nombre valido de uno no vale en el otro.
        ("env", "grouping-dimension", "Unsupported dimension: env"),
        ("ServiceName", "grouping-tag", "Unsupported tag: ServiceName"),
        ("env", "filter-dimension", "Unsupported dimension: env"),
        ("ServiceName", "filter-tag", "Unsupported tag: ServiceName"),
    ],
)
def test_names_are_validated_against_their_own_namespace(client, name, field, message):
    kind, namespace = field.split("-")
    if kind == "grouping":
        body = query_with(grouping={"type": namespace.capitalize(), "name": name})
    else:
        body = query_with(filter={namespace + "s": {"name": name, "operator": "In", "values": ["x"]}})

    assert_bad_request(post_query(client, body), message)


def test_valid_dimension_and_tag_filters_are_still_accepted(client):
    # Control positivo: si la validacion rechazara todo, los casos anteriores pasarian por error.
    for expression in (OK_DIMENSION, OK_TAG, {"and": [OK_DIMENSION, OK_TAG]}):
        response = post_query(client, query_with(filter=expression))

        assert response.status_code == 200
        assert response.json()["properties"]["columns"]
