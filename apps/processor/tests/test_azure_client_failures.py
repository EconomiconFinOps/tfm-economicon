"""Fallos de red REALES y paginas malformadas del cliente Azure Cost (H-09, JUP-054).

Complementa test_azure_cost_client.py: alli el timeout solo se LANZA desde un
FakeTransport; aqui se ejercita el mapeo real de UrllibTransport con sockets
loopback y las ramas de _validate_page que aun no tenian cobertura.
"""
import socket
from threading import Event, Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError

import pytest

from app.clients.azure_cost import (
    AzureCostClient, AzureCostClientError, AzureCostResponseError, AzureCostTimeoutError, UrllibTransport,
)
from app.normalization.azure_cost import AzureCostNormalizer
from app.repositories.azure_cost import SqlAzureCostRepository
from app.tasks.azure_cost_ingest import AzureCostIngestionService, ingestion_run_id
from tenant_isolation_support import isolation_database, snapshot
from test_azure_cost_client import (
    COLUMNS, DEFINITION, SUBSCRIPTION_ID, FakeTransport, continuation, response, settings,
)

TOKEN = "jup054-synthetic-h09-token"


class CountingTransport(UrllibTransport):
    """Transporte REAL que cuenta intentos: detecta reintentos de errores de red."""

    calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        return super().post(*args, **kwargs)


def hang(handler, release):
    release.wait(5)  # Tope de seguridad; el teardown libera el Event antes.


def stalled_body(handler, release):
    # Content-Length mayor que lo enviado y silencio: el timeout salta al leer el cuerpo.
    handler.send_response(200)
    handler.send_header("Content-Length", "1000")
    handler.end_headers()
    handler.wfile.write(b'{"properties":')
    handler.wfile.flush()
    release.wait(5)


class SilentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.hits.append(self.path)
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.behavior(self, self.server.release)

    def log_message(self, format, *args):
        pass


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True  # Un handler bloqueado nunca retiene el cierre del servidor.

    def handle_error(self, request, client_address):
        pass  # El cliente corta a mitad de respuesta: ruido esperado.


@pytest.fixture
def serve(monkeypatch):
    """Arranca servidores loopback y los cierra SIEMPRE (sin hilos ni puertos huerfanos)."""
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    started = []

    def start(behavior):
        server = QuietServer(("127.0.0.1", 0), SilentHandler)
        server.behavior, server.release, server.hits = behavior, Event(), []
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        started.append((server, worker))
        return server.server_port, server.hits

    yield start
    for server, worker in started:
        server.release.set()  # Libera handlers bloqueados antes de cerrar.
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def closed_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


# Puerto cerrado: no se espera nada, asi que el plazo generoso no anade duracion. Windows rechaza
# la conexion loopback con retraso y, si el plazo es corto (0.3 s), la reporta como timeout.
REFUSED_TIMEOUT = 5


def real_client(port, transport=None, timeout=0.3):
    config = settings(
        azure_cost_api_base_url=f"http://127.0.0.1:{port}",
        azure_cost_api_token=TOKEN,
        azure_cost_api_timeout_seconds=timeout,
    )
    return AzureCostClient(config, transport=transport or CountingTransport(), sleeper=lambda _: None)


def test_connection_refused_is_generic_client_error_without_retries_or_secrets():
    port, transport = closed_port(), CountingTransport()

    with pytest.raises(AzureCostClientError, match="connection failed") as failure:
        real_client(port, transport, REFUSED_TIMEOUT).query_all(SUBSCRIPTION_ID, DEFINITION)

    # Tipo exacto: un rechazo de conexion NO es un timeout (diagnostico distinto).
    assert type(failure.value) is AzureCostClientError
    assert TOKEN not in str(failure.value) and str(port) not in str(failure.value)
    assert transport.calls == 1  # Los errores de transporte no se reintentan (max_retries=3).


@pytest.mark.parametrize("behavior", [hang, stalled_body], ids=["sin-respuesta", "cuerpo-detenido"])
def test_read_timeout_is_mapped_to_timeout_error_without_retries_or_secrets(serve, behavior):
    port, hits = serve(behavior)
    transport = CountingTransport()

    with pytest.raises(AzureCostTimeoutError, match="timed out") as failure:
        real_client(port, transport).query_all(SUBSCRIPTION_ID, DEFINITION)

    assert type(failure.value) is AzureCostTimeoutError
    assert TOKEN not in str(failure.value) and str(port) not in str(failure.value)
    assert transport.calls == 1 and len(hits) == 1


def test_urlerror_with_timeout_reason_is_mapped_to_timeout_error():
    # El timeout de CONEXION llega envuelto en URLError(reason=TimeoutError); no es
    # reproducible de forma determinista con sockets, asi que se simula en la frontera del opener.
    transport = UrllibTransport()

    class TimedOutOpener:
        def open(self, request, timeout):
            raise URLError(TimeoutError("timed out"))

    transport._opener = TimedOutOpener()

    with pytest.raises(AzureCostTimeoutError, match="timed out") as failure:
        transport.post("http://127.0.0.1:9/q", body=b"{}", headers={}, timeout=1)

    assert type(failure.value) is AzureCostTimeoutError


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("mode,error", [("closed", AzureCostClientError), ("silent", AzureCostTimeoutError)])
def test_network_failure_marks_run_failed_without_records_or_touching_other_tenant(
    serve, isolation_database, mode, error
):
    repository = SqlAzureCostRepository(isolation_database)
    columns = COLUMNS + [{"name": "UsageDate", "type": "Number"}]
    good_page = FakeTransport([response([[3.5, "USD", 20240601]], columns=columns)])
    good = AzureCostIngestionService(
        AzureCostClient(settings(), transport=good_page), AzureCostNormalizer(), repository
    ).ingest("tenant-a", SUBSCRIPTION_ID, DEFINITION)
    before = snapshot(isolation_database, "azure_cost_records")
    port = closed_port() if mode == "closed" else serve(hang)[0]
    client = real_client(port, timeout=REFUSED_TIMEOUT if mode == "closed" else 0.3)
    service = AzureCostIngestionService(client, AzureCostNormalizer(), repository)

    with pytest.raises(error) as failure:
        service.ingest("tenant-b", SUBSCRIPTION_ID, DEFINITION)

    assert type(failure.value) is error
    failed_id = ingestion_run_id("tenant-b", SUBSCRIPTION_ID, DEFINITION)
    scope = {"tenant_id": "tenant-b", "subscription_id": SUBSCRIPTION_ID}
    failed = repository.fetch_run(failed_id, **scope)
    # error_code guarda solo el NOMBRE de la excepcion: nada de URL ni credenciales en la BD.
    assert (failed["status"], failed["error_code"]) == ("failed", error.__name__)
    assert (failed["row_count"], failed["page_count"], failed["retry_count"]) == (0, 0, 0)
    assert repository.fetch_records(failed_id, **scope) == []
    assert snapshot(isolation_database, "azure_cost_records") == before
    own = {"tenant_id": "tenant-a", "subscription_id": SUBSCRIPTION_ID}
    assert repository.fetch_run(good.run_id, **own)["status"] == "completed"


VALID_ROW = [1, "USD"]
MALFORMED_PAGES = [
    # (kwargs de response(), fragmento del mensaje): cada caso mata un mutante distinto de _validate_page.
    pytest.param({"columns": []}, "no columns", id="columns-vacia"),
    pytest.param({"columns": "x"}, "no columns", id="columns-cadena"),
    pytest.param({"columns": ["PreTaxCost"]}, "invalid column", id="columna-no-dict"),
    # Las columnas invalidas acompanan a las requeridas validas: si la comprobacion faltara,
    # la pagina seria aceptable y el test fallaria en lugar de caer en otro error.
    pytest.param({"columns": COLUMNS + [{"name": "", "type": "String"}]}, "invalid column", id="nombre-vacio"),
    pytest.param({"columns": COLUMNS + [{"name": 5, "type": "String"}]}, "invalid column", id="nombre-no-cadena"),
    pytest.param({"columns": COLUMNS + [{"name": "Extra", "type": "Date"}]}, "invalid column", id="tipo-fuera-de-contrato"),
    pytest.param({"rows": {}}, "rows must be an array", id="rows-dict"),
    pytest.param({"next_link": 5}, "invalid nextLink", id="nextlink-no-cadena"),
    pytest.param({"next_link": ""}, "invalid nextLink", id="nextlink-vacio"),
]


@pytest.mark.parametrize("page_kwargs,fragment", MALFORMED_PAGES)
def test_malformed_page_is_rejected_in_a_single_request_without_secrets(page_kwargs, fragment):
    kwargs = dict(page_kwargs)  # Copia: pop no debe mutar el catalogo compartido.
    rows = kwargs.pop("rows", [VALID_ROW])
    transport = FakeTransport([response(rows, **kwargs)])
    client = AzureCostClient(settings(azure_cost_api_token=TOKEN), transport=transport)

    with pytest.raises(AzureCostResponseError, match=fragment) as failure:
        client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert len(transport.requests) == 1  # Una respuesta invalida no se reintenta.
    assert TOKEN not in str(failure.value)


def test_malformed_second_page_fails_without_returning_partial_result():
    transport = FakeTransport([response([VALID_ROW], next_link=continuation()), response({})])
    client = AzureCostClient(settings(azure_cost_api_token=TOKEN), transport=transport)

    # La primera pagina es valida, pero el resultado parcial acumulado jamas debe devolverse.
    with pytest.raises(AzureCostResponseError, match="rows must be an array") as failure:
        client.query_all(SUBSCRIPTION_ID, DEFINITION)

    assert len(transport.requests) == 2
    assert TOKEN not in str(failure.value)
