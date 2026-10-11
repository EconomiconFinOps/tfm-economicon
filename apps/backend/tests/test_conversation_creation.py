"""JUP-054 (hueco H-03): creacion con exito de conversaciones, POST /assistant/conversations.

`test_tenant_isolation_api.py` solo cubre los RECHAZOS de esta ruta (p. ej. 422
por el campo de autoridad `user_id` en el cuerpo). Aqui se ejercita el camino
feliz, que es una ESCRITURA con aislamiento por tenant y por usuario: se usa la
app real, la autenticacion real (token firmado), la validacion de pertenencia
real y SQL real sobre SQLite; los unicos dobles son los de las fronteras
externas del fixture `api` (cola, vector, embeddings).

No se repiten aqui los casos ya presentes en `test_tenant_isolation_api.py`
(422 por `user_id` en el cuerpo, 404 indistinguible de ids ajenos/inexistentes
sobre conversaciones preexistentes).
"""
import re
from datetime import datetime, timezone

import pytest

from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging

SQLITE = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)

# El id se genera con uuid4 en el producto: se valida por patron y unicidad,
# nunca por un valor concreto.
UUID4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def create(api, user="alice", tenant="tenant-a", title="Nueva", **kwargs):
    return call(api, "POST", "/assistant/conversations", headers=headers(user, tenant), json={"title": title}, **kwargs)


def persisted(api, conversation_id):
    # Aisla la fila nueva por id: no se asierta nada sobre las filas
    # preexistentes del fixture (own, foreign-marker, other-owner, multi-b).
    return [row for row in rows(api.db, "conversations") if row["id"] == conversation_id]


def parse(value):
    # SQLite devuelve las fechas como texto en SQL crudo; la API las serializa
    # en ISO-8601. Se normalizan ambas a datetime con zona para comparar.
    parsed = datetime.fromisoformat(str(value))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def count(api):
    return len(rows(api.db, "conversations"))


@SQLITE
def test_create_returns_201_and_persists_exactly_the_returned_record(api):
    antes = datetime.now(timezone.utc)
    response = create(api, title="  Costes de Azure  ")
    despues = datetime.now(timezone.utc)

    assert response.status_code == 201
    body = response.json()
    # Forma exacta de ConversationRecord: ni campos de mas ni de menos.
    assert set(body) == {"id", "tenant_id", "user_id", "title", "created_at", "updated_at"}
    assert UUID4.match(body["id"])
    # La autoridad sale del contexto autenticado, no del cliente.
    assert body["tenant_id"] == "tenant-a"
    assert body["user_id"] == "alice"
    # El esquema recorta los espacios (strip_whitespace) antes de persistir.
    assert body["title"] == "Costes de Azure"
    # Al crear, ambas marcas de tiempo son la misma y caen en la ventana de la llamada
    # (se comparan contra el reloj real solo de forma relativa, sin fijar un valor).
    assert body["created_at"] == body["updated_at"]
    assert antes <= parse(body["created_at"]) <= despues

    # La fila realmente escrita coincide con lo devuelto (no se devuelve un
    # registro "fantasma" sin persistir).
    [row] = persisted(api, body["id"])
    assert row["tenant_id"] == "tenant-a"
    assert row["user_id"] == "alice"
    assert row["title"] == "Costes de Azure"
    assert parse(row["created_at"]) == parse(body["created_at"])
    assert parse(row["updated_at"]) == parse(body["updated_at"])
    assert parse(row["created_at"]) == parse(row["updated_at"])


@SQLITE
def test_create_inserts_one_row_and_leaves_preexisting_rows_untouched(api):
    previas = rows(api.db, "conversations")
    response = create(api)
    assert response.status_code == 201
    # Exactamente una fila nueva y las existentes no se alteran.
    despues = rows(api.db, "conversations")
    assert len(despues) == len(previas) + 1
    assert all(fila in despues for fila in previas)
    # Crear no escribe en otras tablas de negocio.
    assert rows(api.db, "messages") == []


@SQLITE
def test_two_consecutive_creations_get_distinct_ids_and_rows(api):
    primera = create(api, title="Misma")
    segunda = create(api, title="Misma")
    assert primera.status_code == segunda.status_code == 201
    # Mismo titulo y mismo usuario no deduplican: son dos conversaciones.
    assert primera.json()["id"] != segunda.json()["id"]
    assert len(persisted(api, primera.json()["id"])) == 1
    assert len(persisted(api, segunda.json()["id"])) == 1


@SQLITE
@pytest.mark.parametrize("tenant", ["tenant-a", "tenant-b"])
def test_tenant_comes_from_validated_header_for_multi_tenant_user(api, tenant):
    # `multi` pertenece a ambos tenants: el mismo usuario y la misma accion
    # dejan la fila en el tenant seleccionado por la cabecera validada,
    # no en uno fijo ni en el primero que encuentre la BD.
    response = create(api, user="multi", tenant=tenant)
    assert response.status_code == 201
    assert response.json()["tenant_id"] == tenant
    [row] = persisted(api, response.json()["id"])
    assert row["tenant_id"] == tenant
    assert row["user_id"] == "multi"


@SQLITE
@pytest.mark.parametrize("user, tenant", [("alice", "tenant-a"), ("bob", "tenant-b"), ("other-a", "tenant-a"), ("multi", "tenant-b")])
def test_user_comes_from_the_token_for_every_identity(api, user, tenant):
    # Varias identidades distintas: evita que un user_id fijo pase desapercibido.
    response = create(api, user=user, tenant=tenant)
    assert response.status_code == 201
    assert response.json()["user_id"] == user
    [row] = persisted(api, response.json()["id"])
    assert row["user_id"] == user


@SQLITE
def test_created_conversation_is_readable_by_owner_with_empty_history(api):
    creada = create(api, title="  Mia  ").json()
    response = call(api, "GET", "/assistant/conversations/" + creada["id"], headers=headers("alice", "tenant-a"))
    assert response.status_code == 200
    # El detalle devuelve el mismo registro y un historial vacio recien creada.
    assert response.json()["conversation"] == creada
    assert response.json()["messages"] == []


@SQLITE
@pytest.mark.parametrize("user, tenant", [("bob", "tenant-b"), ("other-a", "tenant-a")], ids=["otro-tenant", "mismo-tenant-otro-usuario"])
def test_created_conversation_is_invisible_to_other_tenant_and_other_user(api, user, tenant):
    creada = create(api).json()
    ajena = call(api, "GET", "/assistant/conversations/" + creada["id"], headers=headers(user, tenant))
    inexistente = call(api, "GET", "/assistant/conversations/id-que-no-existe", headers=headers(user, tenant))
    assert ajena.status_code == 404
    # Mismo 404 y mismo cuerpo que un id inexistente: no se revela que existe.
    assert ajena.json() == inexistente.json() == {"detail": "Conversation not found."}
    assert creada["title"] not in ajena.text


@SQLITE
def test_created_conversation_is_not_readable_by_same_user_in_other_tenant(api):
    # Aislamiento por tenant para el MISMO usuario: multi crea en tenant-a y no la ve
    # cuando selecciona tenant-b (la pertenencia es valida, pero el tenant activo no coincide).
    creada = create(api, user="multi", tenant="tenant-a").json()
    en_a = call(api, "GET", "/assistant/conversations/" + creada["id"], headers=headers("multi", "tenant-a"))
    en_b = call(api, "GET", "/assistant/conversations/" + creada["id"], headers=headers("multi", "tenant-b"))
    assert en_a.status_code == 200
    assert en_b.status_code == 404


@SQLITE
def test_created_conversation_appears_only_in_the_owner_list(api):
    # El listado funciona con SQLite: no se asierta orden, solo pertenencia al conjunto.
    creada = create(api).json()

    def ids(user, tenant):
        response = call(api, "GET", "/assistant/conversations", headers=headers(user, tenant))
        assert response.status_code == 200
        return [item["id"] for item in response.json()["items"]]

    assert creada["id"] in ids("alice", "tenant-a")
    assert creada["id"] not in ids("other-a", "tenant-a")
    assert creada["id"] not in ids("bob", "tenant-b")
    assert creada["id"] not in ids("multi", "tenant-a")


@SQLITE
@pytest.mark.parametrize("title", ["", "   ", "\t\n "], ids=["vacio", "espacios", "blancos-mixtos"])
def test_blank_title_is_rejected_without_writing(api, title):
    antes = rows(api.db, "conversations")
    response = create(api, title=title)
    assert response.status_code == 422
    assert response.json() == {"detail": [{"type": "validation_error", "msg": "Invalid request value"}]}
    # La validacion del esquema ocurre antes de tocar la BD: la tabla no cambia
    # y la capa de persistencia ni se invoca.
    assert rows(api.db, "conversations") == antes
    api.spies["create_conversation"].assert_not_called()


@SQLITE
def test_missing_title_is_rejected_without_writing(api):
    antes = count(api)
    response = call(api, "POST", "/assistant/conversations", headers=headers(), json={})
    assert response.status_code == 422
    assert count(api) == antes


@SQLITE
def test_missing_token_is_rejected_with_401_without_writing(api):
    antes = rows(api.db, "conversations")
    response = call(api, "POST", "/assistant/conversations", headers=[("X-Tenant-Id", "tenant-a")], json={"title": "Nueva"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid bearer token."}
    assert rows(api.db, "conversations") == antes
    api.spies["create_conversation"].assert_not_called()


@SQLITE
def test_invalid_token_is_rejected_with_401_without_writing(api):
    antes = rows(api.db, "conversations")
    response = call(api, "POST", "/assistant/conversations",
                    headers=[("Authorization", "Bearer not-a-valid-token"), ("X-Tenant-Id", "tenant-a")], json={"title": "Nueva"})
    assert response.status_code == 401
    assert rows(api.db, "conversations") == antes
    api.spies["create_conversation"].assert_not_called()


@SQLITE
def test_missing_tenant_header_is_rejected_with_400_without_writing(api):
    antes = rows(api.db, "conversations")
    response = create(api, tenant=None)
    assert response.status_code == 400
    assert response.json() == {"detail": "A single valid X-Tenant-Id header is required."}
    assert rows(api.db, "conversations") == antes
    api.spies["create_conversation"].assert_not_called()


@SQLITE
@pytest.mark.parametrize("user, tenant", [("bob", "tenant-a"), ("alice", "tenant-b"), ("alice", "tenant-inexistente"), ("admin-alone", "tenant-a")],
                         ids=["bob-en-a", "alice-en-b", "tenant-inexistente", "admin-sin-membresias"])
def test_tenant_without_membership_is_rejected_with_403_without_writing(api, user, tenant):
    # Sin pertenencia en user_tenants no se puede escribir en ese tenant, ni siquiera
    # con rol admin ni con un tenant que no existe.
    antes = rows(api.db, "conversations")
    response = create(api, user=user, tenant=tenant)
    assert response.status_code == 403
    assert response.json() == {"detail": "The current user cannot access the requested tenant."}
    assert rows(api.db, "conversations") == antes
    api.spies["create_conversation"].assert_not_called()


@SQLITE
def test_created_conversation_appears_only_in_the_list_of_its_own_tenant_for_multi_tenant_user(api):
    # El listado de un usuario multi-tenant se acota por el tenant activo: lo creado en
    # tenant-a no aparece al listar con tenant-b aunque el usuario sea el mismo.
    # (Mata un listado que filtre solo por usuario y mezcle tenants.)
    creada = create(api, user="multi", tenant="tenant-a").json()

    def ids(tenant):
        response = call(api, "GET", "/assistant/conversations", headers=headers("multi", tenant))
        assert response.status_code == 200
        return [item["id"] for item in response.json()["items"]]

    assert creada["id"] in ids("tenant-a")
    assert creada["id"] not in ids("tenant-b")
    # La conversacion preexistente de multi en tenant-b sigue fuera del listado de tenant-a.
    assert "multi-b" not in ids("tenant-a")
