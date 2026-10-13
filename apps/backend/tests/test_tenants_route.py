"""JUP-054 (hueco H-02): pruebas funcionales de GET /tenants.

La ruta es de autorizacion/pertenencia: devuelve SOLO los tenants a los que
pertenece el usuario autenticado. Se ejercita por HTTP con la aplicacion real,
su autenticacion real (token firmado) y SQL real sobre SQLite; los unicos dobles
son los de las fronteras externas que ya aporta el fixture `api` (cola, vector,
embeddings).
"""
import pytest

from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging

SQLITE = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)

# El fixture inserta cada tenant con id == name == slug y plan "test".
# `fetch_tenants` ordena por name, por lo que el orden de salida es determinista.
TENANT_A = {"id": "tenant-a", "name": "tenant-a", "slug": "tenant-a", "plan": "test"}
TENANT_B = {"id": "tenant-b", "name": "tenant-b", "slug": "tenant-b", "plan": "test"}


def get_tenants(api, user, **kwargs):
    # No se envia X-Tenant-Id: /tenants es la ruta que permite descubrir los
    # tenants, asi que no puede exigir uno previo.
    return call(api, "GET", "/tenants", headers=headers(user, None), **kwargs)


@SQLITE
def test_single_membership_user_sees_exactly_their_tenant(api):
    response = get_tenants(api, "alice")
    assert response.status_code == 200
    # Igualdad exacta de la forma TenantCollection: un tenant, sin campos extra.
    assert response.json() == {"items": [TENANT_A]}


@SQLITE
def test_multi_tenant_user_sees_exactly_both_tenants(api):
    response = get_tenants(api, "multi")
    assert response.status_code == 200
    # Ambos tenants, sin duplicados y en orden estable por nombre.
    assert response.json() == {"items": [TENANT_A, TENANT_B]}


@SQLITE
def test_user_never_sees_foreign_tenants(api):
    # bob solo pertenece a tenant-b: tenant-a (de alice/other-a/multi) no debe aparecer.
    response = get_tenants(api, "bob")
    assert response.status_code == 200
    assert response.json() == {"items": [TENANT_B]}
    assert "tenant-a" not in response.text


@SQLITE
def test_x_tenant_id_header_cannot_widen_the_listing(api):
    # Una cabecera X-Tenant-Id ajena no es una fuente de autoridad: la
    # pertenencia sale de la BD, no de lo que el cliente declare.
    response = call(api, "GET", "/tenants", headers=headers("bob", "tenant-a"))
    assert response.status_code == 200
    assert response.json() == {"items": [TENANT_B]}


@SQLITE
def test_admin_role_without_memberships_gets_empty_list(api):
    # Caso de autorizacion clave: el rol admin NO concede tenants; solo cuentan
    # las filas de user_tenants. admin-alone no tiene ninguna.
    response = get_tenants(api, "admin-alone")
    assert response.status_code == 200
    assert response.json() == {"items": []}


@SQLITE
def test_missing_token_is_rejected_without_tenant_data(api):
    response = call(api, "GET", "/tenants")
    assert response.status_code == 401
    # El rechazo no debe filtrar ni identificadores ni la clave "items".
    assert "tenant-a" not in response.text and "tenant-b" not in response.text
    assert "items" not in response.json()
    # El cuerpo es exactamente el error generico de autenticacion, nada mas.
    assert response.json() == {"detail": "Missing or invalid bearer token."}


@SQLITE
@pytest.mark.parametrize("authorization", ["Bearer not-a-valid-token", "Basic abc", "Bearer"], ids=["bad-token", "wrong-scheme", "no-token"])
def test_invalid_credentials_are_rejected_without_tenant_data(api, authorization):
    response = call(api, "GET", "/tenants", headers=[("Authorization", authorization)])
    assert response.status_code == 401
    assert "tenant-a" not in response.text and "tenant-b" not in response.text
    assert "items" not in response.json()


@SQLITE
def test_valid_token_of_unknown_user_is_rejected(api):
    # Token bien firmado pero cuyo sujeto no existe en BD (p. ej. usuario
    # borrado): no debe tratarse como usuario sin tenants (200 []), sino 401.
    response = get_tenants(api, "ghost-user")
    assert response.status_code == 401
    assert "items" not in response.json()
