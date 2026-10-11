"""JUP-054 (H-08): rechazo de runs ajenos y guardas de integridad por rowcount.

Cubre dos huecos de `SqlAzureCostRepository` que la CI (solo SQLite) no
ejercitaba:

1. `start_run` sobre un run que pertenece a otro tenant/suscripcion: el
   `ON CONFLICT ... DO UPDATE ... WHERE` debe dejar 0 filas afectadas y el
   repositorio debe responder `PermissionError` sin tocar el run ajeno.
2. Guardas de `rowcount` de `_delete_records`, del INSERT por registro y de los
   UPDATE finales de `complete_run`/`fail_run`. Su valor real es la
   ATOMICIDAD: si una guarda salta, la transaccion entera se revierte (no se
   pierden los registros previos, no quedan registros a medias y el run no
   cambia de estado).

Por que triggers de SQLite y no un doble del driver: `RAISE(IGNORE)` en un
trigger BEFORE hace que la base omita esa fila, de modo que el `rowcount` que
llega al repositorio es 0 de verdad. Es la base real la que "miente" y el
rollback lo hace el motor real, en lugar de depender de un proxy que
reimplemente la transaccion (como el helper `ReportZeroUpdatedRows`).
"""
from dataclasses import replace

import pytest
from sqlalchemy import text

from tenant_isolation_support import isolation_database  # noqa: F401  (fixture parametrizada)
from test_azure_cost_normalized_schema import normalized_record
from test_tenant_isolation_costs import costs, state  # noqa: F401  (fixture `costs` y helper)

SHARED = "shared-subscription"
SQLITE_ONLY = pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)

# Hashes distintos => ids de registro distintos (el id deriva de run:indice:hash).
HASH_PREVIOUS_1 = "b" * 64
HASH_PREVIOUS_2 = "c" * 64
HASH_NEW_1 = "d" * 64
HASH_NEW_2 = "e" * 64


def record(source_hash):
    return replace(normalized_record(), source_row_hash=source_hash)


def previous_records():
    return (record(HASH_PREVIOUS_1), record(HASH_PREVIOUS_2))


def new_records():
    return (record(HASH_NEW_1), record(HASH_NEW_2))


@pytest.fixture
def seeded(costs):
    """`run-a` con DOS registros previos, para distinguir "borra todo" de "borra algo"."""
    costs.repository.complete_run("run-a", "tenant-a", SHARED, previous_records(), page_count=2, retry_count=1)
    assert hashes(costs, "run-a") == {HASH_PREVIOUS_1, HASH_PREVIOUS_2}
    # Contadores de partida NO nulos: asi un `fail_run` que no los ponga a 0 se detecta.
    seeded_run = run_row(costs, "run-a")
    assert (seeded_run["page_count"], seeded_run["retry_count"], seeded_run["row_count"]) == (2, 1, 2)
    return costs


def hashes(costs, run_id="run-a", tenant="tenant-a", subscription=SHARED):
    rows = costs.repository.fetch_records(run_id, tenant_id=tenant, subscription_id=subscription)
    return {row["source_row_hash"] for row in rows}


def create_trigger(costs, event, table, when=None):
    """Instala un trigger BEFORE que ignora la fila (rowcount 0 en esa sentencia)."""
    condition = f"WHEN {when}" if when else ""
    with costs.db.engine.begin() as connection:
        connection.execute(text(
            f"CREATE TRIGGER reject_write BEFORE {event} ON {table} {condition} "
            "BEGIN SELECT RAISE(IGNORE); END"
        ))


def drop_trigger(costs):
    with costs.db.engine.begin() as connection:
        connection.execute(text("DROP TRIGGER reject_write"))


def run_row(costs, run_id):
    return next(row for row in state(costs)[0] if row["id"] == run_id)


# ---------------------------------------------------------------------------
# A. start_run sobre un run ajeno
# ---------------------------------------------------------------------------

@SQLITE_ONLY
@pytest.mark.parametrize(
    "run_id,tenant,subscription",
    [
        # Solo difiere el tenant (la suscripcion es la compartida): la condicion de tenant debe bastar.
        pytest.param("run-b", "tenant-a", SHARED, id="run-de-otro-tenant"),
        # Mismo tenant pero otra suscripcion: la condicion de suscripcion debe bastar por si sola.
        pytest.param("run-other-sub", "tenant-a", SHARED, id="run-de-otra-suscripcion"),
        # Suscripcion correcta del run, tenant erroneo.
        pytest.param("run-a", "tenant-b", SHARED, id="tenant-erroneo-suscripcion-correcta"),
        # Tenant correcto del run, suscripcion erronea.
        pytest.param("run-b", "tenant-b", "other-subscription", id="tenant-correcto-suscripcion-erronea"),
        pytest.param("run-a", "tenant-z", "zzz", id="ambos-erroneos"),
    ],
)
def test_start_run_rejects_foreign_run_without_touching_it(costs, run_id, tenant, subscription):
    before = state(costs)

    with pytest.raises(PermissionError, match=r"^Cost run not found\.$"):
        costs.repository.start_run(run_id, tenant, subscription, {"attempt": "foreign"})

    # Ni el run (estado, contadores, request) ni ningun registro cambian: el
    # ON CONFLICT no debe haber reiniciado el run ajeno.
    assert state(costs) == before


@SQLITE_ONLY
def test_start_run_restarts_own_run_without_rejection(costs):
    """Control positivo: sin el, una rotura que rechace TODO pasaria desapercibida."""
    before = state(costs)
    assert run_row(costs, "run-a")["status"] == "completed"

    costs.repository.start_run("run-a", "tenant-a", SHARED, {"attempt": "own"})

    after = state(costs)
    restarted = run_row(costs, "run-a")
    assert restarted["status"] == "running"
    assert (restarted["page_count"], restarted["retry_count"], restarted["row_count"]) == (0, 0, 0)
    assert restarted["error_code"] is None
    assert restarted["completed_at"] is None
    # El reinicio solo toca el run propio. `started_at` se renueva (no se compara
    # su valor absoluto: depende del reloj) y el resto de columnas de identidad se conserva.
    old = next(row for row in before[0] if row["id"] == "run-a")
    for column in ("id", "tenant_id", "subscription_id"):
        assert restarted[column] == old[column]
    # Los demas runs y TODOS los registros quedan intactos (start_run no borra hijos).
    assert [row for row in after[0] if row["id"] != "run-a"] == [row for row in before[0] if row["id"] != "run-a"]
    assert after[1] == before[1]


@SQLITE_ONLY
def test_start_run_restarts_own_failed_run_and_clears_error(costs):
    """Reintento real tras un fallo: el run propio `failed` vuelve a `running` sin error.

    El run de partida `completed` ya tiene `error_code` NULL, por lo que la
    comprobacion del test anterior no detecta que el reinicio olvide limpiarlo.
    Aqui se parte de un run `failed` con `error_code` relleno y contadores a 0.
    """
    costs.repository.fail_run("run-a", "SyntheticFailure", tenant_id="tenant-a", subscription_id=SHARED)
    failed = run_row(costs, "run-a")
    assert (failed["status"], failed["error_code"]) == ("failed", "SyntheticFailure")
    assert failed["completed_at"] is not None
    before = state(costs)

    costs.repository.start_run("run-a", "tenant-a", SHARED, {"attempt": "retry"})

    restarted = run_row(costs, "run-a")
    assert restarted["status"] == "running"
    assert restarted["error_code"] is None
    assert restarted["completed_at"] is None
    assert (restarted["page_count"], restarted["retry_count"], restarted["row_count"]) == (0, 0, 0)
    # Solo cambia el run propio; los demas runs y los registros siguen igual.
    assert [row for row in state(costs)[0] if row["id"] != "run-a"] == [row for row in before[0] if row["id"] != "run-a"]
    assert state(costs)[1] == before[1]


@SQLITE_ONLY
@pytest.mark.parametrize(
    "run_id,owner_tenant,owner_subscription,attacker_tenant,attacker_subscription",
    [
        pytest.param("run-b", "tenant-b", SHARED, "tenant-a", SHARED, id="failed-de-otro-tenant"),
        pytest.param("run-other-sub", "tenant-a", "other-subscription", "tenant-a", SHARED, id="failed-de-otra-suscripcion"),
    ],
)
def test_start_run_rejects_foreign_failed_run(
    costs, run_id, owner_tenant, owner_subscription, attacker_tenant, attacker_subscription
):
    """Un run ajeno en estado `failed` tampoco se puede reiniciar.

    El estado `failed` es el que legitimamente permite reintentar, asi que una
    excepcion mal puesta ("reiniciar si esta failed") abriria una via a otro
    tenant. Los demas casos usan runs ajenos `completed` y no la detectan.
    """
    costs.repository.fail_run(run_id, "SyntheticFailure", tenant_id=owner_tenant, subscription_id=owner_subscription)
    assert run_row(costs, run_id)["status"] == "failed"
    before = state(costs)

    with pytest.raises(PermissionError, match=r"^Cost run not found\.$"):
        costs.repository.start_run(run_id, attacker_tenant, attacker_subscription, {"attempt": "foreign"})

    assert state(costs) == before
    assert run_row(costs, run_id)["status"] == "failed"
    assert run_row(costs, run_id)["error_code"] == "SyntheticFailure"


# ---------------------------------------------------------------------------
# B0. complete_run sobre un run ajeno: la excepcion debe ser SIEMPRE PermissionError
# ---------------------------------------------------------------------------

@SQLITE_ONLY
@pytest.mark.parametrize("run_id", [pytest.param("run-b", id="run-de-otro-tenant"), pytest.param("run-other-sub", id="run-de-otra-suscripcion")])
@pytest.mark.parametrize(
    "attacker_record",
    [
        # Mismo run_id, indice 0 y hash que el registro existente del run ajeno =>
        # mismo uuid5. Sin la autorizacion previa del padre (`_lock_run`) saltaria
        # un UNIQUE/PK, que ademas serviria de oraculo de existencia de registros ajenos.
        pytest.param(normalized_record(), id="registro-colisionante"),
        # Registro invalido (currency NOT NULL): sin la guarda previa saldria un
        # IntegrityError distinto en lugar de la denegacion.
        pytest.param(replace(normalized_record(), source_row_hash="f" * 64, currency=None), id="registro-invalido"),
    ],
)
def test_complete_run_on_foreign_run_is_denied_before_touching_records(costs, run_id, attacker_record):
    before = state(costs)

    with pytest.raises(PermissionError, match=r"^Cost run not found\.$"):
        costs.repository.complete_run(run_id, "tenant-a", SHARED, (attacker_record,), page_count=1, retry_count=0)

    assert state(costs) == before


# ---------------------------------------------------------------------------
# B. complete_run: guardas de rowcount + atomicidad
# ---------------------------------------------------------------------------

@SQLITE_ONLY
@pytest.mark.parametrize(
    "when",
    [
        # La base ignora TODOS los borrados: se cuentan 2 y se borran 0.
        pytest.param(None, id="borrado-ninguno"),
        # La base ignora solo uno: se cuentan 2 y se borra 1 (un borrado parcial
        # no debe confundirse con exito ni con "no se borro nada").
        pytest.param(f"OLD.source_row_hash = '{HASH_PREVIOUS_2}'", id="borrado-parcial"),
    ],
)
def test_complete_run_aborts_when_delete_rowcount_differs_from_count(seeded, when):
    before = state(seeded)
    create_trigger(seeded, "DELETE", "azure_cost_records", when)

    with pytest.raises(RuntimeError, match=r"^Cost records update rejected\.$"):
        seeded.repository.complete_run("run-a", "tenant-a", SHARED, new_records(), page_count=9, retry_count=3)

    # Los registros viejos NO se pierden, no entran los nuevos y el run no cambia.
    assert state(seeded) == before
    assert hashes(seeded) == {HASH_PREVIOUS_1, HASH_PREVIOUS_2}

    # Control: sin el trigger la misma operacion funciona, asi que el rechazo lo provoco la base.
    drop_trigger(seeded)
    seeded.repository.complete_run("run-a", "tenant-a", SHARED, new_records(), page_count=9, retry_count=3)
    assert hashes(seeded) == {HASH_NEW_1, HASH_NEW_2}
    assert run_row(seeded, "run-a")["page_count"] == 9


@SQLITE_ONLY
@pytest.mark.parametrize(
    "when",
    [
        # El primer INSERT ya falla: el DELETE previo (que si funciono) debe revertirse.
        pytest.param(None, id="primer-insert-rechazado"),
        # Falla el segundo: el primer INSERT, ya ejecutado, tambien debe revertirse
        # (nada de registros a medias).
        pytest.param(f"NEW.source_row_hash = '{HASH_NEW_2}'", id="segundo-insert-rechazado"),
    ],
)
def test_complete_run_aborts_and_rolls_back_when_insert_is_rejected(seeded, when):
    before = state(seeded)
    create_trigger(seeded, "INSERT", "azure_cost_records", when)

    with pytest.raises(RuntimeError, match=r"^Cost record insert rejected\.$"):
        seeded.repository.complete_run("run-a", "tenant-a", SHARED, new_records(), page_count=9, retry_count=3)

    assert state(seeded) == before
    assert hashes(seeded) == {HASH_PREVIOUS_1, HASH_PREVIOUS_2}
    assert run_row(seeded, "run-a")["page_count"] == 2

    drop_trigger(seeded)
    seeded.repository.complete_run("run-a", "tenant-a", SHARED, new_records(), page_count=9, retry_count=3)
    assert hashes(seeded) == {HASH_NEW_1, HASH_NEW_2}


@SQLITE_ONLY
def test_complete_run_rolls_back_inserted_records_when_final_update_is_rejected(seeded):
    before = state(seeded)
    # Solo el UPDATE final modifica `completed_at`; el UPDATE de bloqueo
    # (`SET id = id`) no lo toca, por lo que la guarda de `_lock_run` sigue pasando
    # y se aisla la guarda del UPDATE final.
    create_trigger(seeded, "UPDATE", "azure_cost_ingestion_runs", "NEW.completed_at IS NOT OLD.completed_at")

    with pytest.raises(PermissionError, match=r"^Cost run not found\.$"):
        seeded.repository.complete_run("run-a", "tenant-a", SHARED, new_records(), page_count=9, retry_count=3)

    # Los registros nuevos ya estaban insertados y los viejos borrados cuando
    # salto la guarda: todo debe haberse revertido.
    assert state(seeded) == before
    assert hashes(seeded) == {HASH_PREVIOUS_1, HASH_PREVIOUS_2}

    drop_trigger(seeded)
    seeded.repository.complete_run("run-a", "tenant-a", SHARED, new_records(), page_count=9, retry_count=3)
    assert hashes(seeded) == {HASH_NEW_1, HASH_NEW_2}
    completed = run_row(seeded, "run-a")
    assert (completed["status"], completed["page_count"], completed["retry_count"], completed["row_count"]) == ("completed", 9, 3, 2)


# ---------------------------------------------------------------------------
# B. fail_run: guardas de rowcount + atomicidad
# ---------------------------------------------------------------------------

@SQLITE_ONLY
@pytest.mark.parametrize(
    "when",
    [
        pytest.param(None, id="borrado-ninguno"),
        pytest.param(f"OLD.source_row_hash = '{HASH_PREVIOUS_2}'", id="borrado-parcial"),
    ],
)
def test_fail_run_aborts_when_delete_rowcount_differs_from_count(seeded, when):
    before = state(seeded)
    create_trigger(seeded, "DELETE", "azure_cost_records", when)

    with pytest.raises(RuntimeError, match=r"^Cost records update rejected\.$"):
        seeded.repository.fail_run("run-a", "SyntheticFailure", tenant_id="tenant-a", subscription_id=SHARED)

    # El run NO queda `failed` y sus registros (incluidos los que si se borraron
    # en el borrado parcial) siguen ahi.
    assert state(seeded) == before
    assert run_row(seeded, "run-a")["status"] == "completed"
    assert hashes(seeded) == {HASH_PREVIOUS_1, HASH_PREVIOUS_2}

    drop_trigger(seeded)
    seeded.repository.fail_run("run-a", "SyntheticFailure", tenant_id="tenant-a", subscription_id=SHARED)
    failed = run_row(seeded, "run-a")
    assert failed["status"] == "failed"
    # Un run fallido no conserva contadores de la ejecucion anterior.
    assert (failed["page_count"], failed["retry_count"], failed["row_count"]) == (0, 0, 0)
    assert hashes(seeded) == set()


@SQLITE_ONLY
def test_fail_run_rolls_back_deletion_when_final_update_is_rejected(seeded):
    before = state(seeded)
    # Solo el UPDATE final deja `status = 'failed'` (el run de partida esta
    # `completed`, asi que el UPDATE de bloqueo no cumple la condicion).
    create_trigger(seeded, "UPDATE", "azure_cost_ingestion_runs", "NEW.status = 'failed'")

    with pytest.raises(PermissionError, match=r"^Cost run not found\.$"):
        seeded.repository.fail_run("run-a", "SyntheticFailure", tenant_id="tenant-a", subscription_id=SHARED)

    # El DELETE ya habia borrado los registros: la guarda debe revertirlos.
    assert state(seeded) == before
    assert run_row(seeded, "run-a")["status"] == "completed"
    assert run_row(seeded, "run-a")["error_code"] is None
    assert hashes(seeded) == {HASH_PREVIOUS_1, HASH_PREVIOUS_2}

    drop_trigger(seeded)
    seeded.repository.fail_run("run-a", "SyntheticFailure", tenant_id="tenant-a", subscription_id=SHARED)
    failed = run_row(seeded, "run-a")
    assert (failed["status"], failed["error_code"]) == ("failed", "SyntheticFailure")
    assert (failed["page_count"], failed["retry_count"], failed["row_count"]) == (0, 0, 0)
    assert hashes(seeded) == set()
