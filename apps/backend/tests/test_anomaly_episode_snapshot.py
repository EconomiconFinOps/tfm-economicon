"""JUP-038 (tarea 3.1): lectura de la «fotografía» de un episodio con operandos exactos, sobre CockroachDB real.

`Database.fetch_anomaly_episode_snapshot(tenant_id, episode_id)` entrega al explicador puro
(`app.services.anomaly_explanations.explain_episode`) tres cosas: el payload redondeado de la API, los operandos
EXACTOS guardados en la tabla y la marca de datos sintéticos. Se prueba contra la base real porque lo que importa
es lo que el motor devuelve de verdad (tipos `Decimal`, `date` y `datetime` con zona horaria, un solo SELECT
filtrado por cliente) y un doble en memoria taparía justo esos riesgos.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import event, text

from app.services.anomaly_explanations import explain_episode
from anomaly_episode_support import episode_rows, episode_store, load_series
from billing_support import billing_schema, insert_run
from tenant_isolation_support import tenant_cockroach_database


TODAY = date(2026, 10, 12)
SPIKE = ["400.00"] * 7 + ["550.00", "400.00"]
# Importe observado con más de dos decimales: la referencia diaria es 400 y la subida exacta 100.004, que se
# muestra como 100.00 y obliga a la nota de redondeo del umbral absoluto.
FRACTIONAL = ["400.00"] * 7 + ["500.004", "400.00"]
EXPLAINED_AT = datetime(2026, 10, 12, 9, 30, tzinfo=timezone.utc)
MISSING_ID = "anomaly-" + "0" * 64


def open_episode(db, values=SPIKE, tenant="tenant-a", **series):
    """Carga la serie, corre la detección del cliente y devuelve el id del único episodio abierto."""
    load_series(db, values, tenant=tenant, **series)
    db.run_anomaly_detection(tenant, today=TODAY)
    [item] = db.fetch_anomaly_episodes(tenant)
    return item["id"]


def snapshot_state(db):
    """Estado completo de las tablas que la lectura nunca debe tocar."""
    with db.engine.connect() as connection:
        state = [dict(row) for row in connection.execute(
            text("SELECT * FROM anomaly_detection_state ORDER BY tenant_id")).mappings()]
    return episode_rows(db), state


def test_snapshot_episode_matches_api_payload_and_has_the_types_the_explainer_requires(episode_store):
    # Valida que la parte `episode` es el mismo payload de la API (sin `_order`) y que los tipos son los que
    # el explicador necesita: `date` puro en las fechas (un `datetime` rompería `isoformat()` y las
    # comparaciones) y `Decimal` en los operandos. Es el contrato de la lectura, no un detalle interno.
    db = episode_store
    episode_id = open_episode(db)
    snapshot = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)
    episode = snapshot["episode"]
    assert episode == db.fetch_anomaly_episode("tenant-a", episode_id)
    assert "_order" not in episode
    assert set(snapshot) == {"episode", "operands", "includes_synthetic_data"}
    for key in ("start_date", "last_seen_date", "impact_through_date"):
        assert type(episode[key]) is date, key
    # Episodio abierto y observado: no hay fecha de "ya no se observa" ni de cierre.
    assert episode["no_longer_observed_on"] is None and episode["closed_at"] is None
    for key in ("status_changed_at", "created_at"):
        # `created_at` siempre existe; `status_changed_at` es None hasta el primer cambio de estado.
        value = episode[key]
        if value is not None:
            assert isinstance(value, datetime) and value.utcoffset() is not None, key
    assert isinstance(episode["created_at"], datetime) and episode["created_at"].utcoffset() is not None
    assert snapshot["includes_synthetic_data"] is False
    assert set(snapshot["operands"]) == {"reference_week_cost", "opening_observed_cost", "impact_numerator"}
    assert all(type(value) is Decimal for value in snapshot["operands"].values())


def test_snapshot_operands_are_the_exact_stored_columns(episode_store):
    # Oráculo independiente: las columnas se leen directamente de la tabla con SQL, no con el código que se
    # prueba. Se compara por valor y por texto: `Decimal("2800.0")` y `Decimal("2800.00")` son iguales por
    # valor pero el texto del identificador de evidencia cambiaría, así que la escala también debe coincidir.
    db = episode_store
    episode_id = open_episode(db)
    [row] = episode_rows(db, "tenant-a")
    operands = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["operands"]
    for key in ("reference_week_cost", "opening_observed_cost", "impact_numerator"):
        assert operands[key] == row[key], key
        assert format(operands[key], "f") == format(row[key], "f"), key
    assert operands["reference_week_cost"] == Decimal("2800.00")
    assert operands["opening_observed_cost"] == Decimal("550.00")
    assert operands["impact_numerator"] == Decimal("1050.00")


def test_snapshot_operands_keep_extra_decimals_while_the_payload_rounds(episode_store):
    # Caso límite financiero: con 500.004 la API muestra 500.00 y un impacto de 100.00, pero la explicación
    # debe recalcularse con los valores exactos (500.004 y 700.028). El redondeo solo existe en el payload.
    db = episode_store
    episode_id = open_episode(db, FRACTIONAL)
    snapshot = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)
    operands = snapshot["operands"]
    assert operands["opening_observed_cost"] == Decimal("500.004")
    assert operands["impact_numerator"] == Decimal("700.028")
    # La tabla guarda los importes con 12 decimales (NUMERIC(38,12)), asi que el texto exacto lleva ceros finales
    # ("500.004000000000"). Se fija que el texto es el de la propia columna, sin normalizar, y que no se pierde
    # ningun decimal significativo. (Correccion autorizada por Victor el 2026-10-12: el literal "500.004" ignoraba la escala.)
    [row] = episode_rows(db, "tenant-a")
    assert format(operands["opening_observed_cost"], "f") == format(row["opening_observed_cost"], "f")
    assert format(operands["impact_numerator"], "f") == format(row["impact_numerator"], "f")
    assert format(operands["opening_observed_cost"], "f").startswith("500.004")
    assert format(operands["impact_numerator"], "f").startswith("700.028")
    assert snapshot["episode"]["opening_observed_cost"] == "500.00"
    assert snapshot["episode"]["accumulated_impact"] == "100.00"


def set_synthetic(db, run_id):
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE azure_cost_ingestion_runs SET request = '{\"synthetic\": true}'::JSONB "
                                "WHERE id = :id"), {"id": run_id})


def test_snapshot_flags_synthetic_data_of_a_completed_run_of_the_same_tenant(episode_store):
    # Misma regla que `fetch_anomaly_episode_list`: una ingesta COMPLETADA del cliente marcada sintética.
    db = episode_store
    episode_id = open_episode(db)
    assert db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["includes_synthetic_data"] is False
    set_synthetic(db, "run-a")
    assert db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["includes_synthetic_data"] is True


def test_snapshot_ignores_synthetic_runs_of_other_tenants_and_unfinished_runs(episode_store):
    # Dos falsos positivos posibles: (1) una ingesta sintética de OTRO cliente no debe filtrarse al aviso de
    # este (aislamiento); (2) una ingesta sintética que no llegó a `completed` no aporta datos al episodio.
    db = episode_store
    episode_id = open_episode(db)
    load_series(db, SPIKE, tenant="tenant-b", run="run-b", prefix="b")
    set_synthetic(db, "run-b")
    with db.engine.begin() as connection:
        insert_run(connection, "run-running", tenant="tenant-a", status="running")
        insert_run(connection, "run-failed", tenant="tenant-a", status="failed")
    set_synthetic(db, "run-running")
    set_synthetic(db, "run-failed")
    assert db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["includes_synthetic_data"] is False


def test_snapshot_is_none_for_other_tenant_or_unknown_id_and_each_tenant_sees_its_own(episode_store):
    # Un episodio ajeno y uno inexistente deben ser indistinguibles (`None`): no se revela que el id existe.
    db = episode_store
    a_id = open_episode(db)
    b_id = open_episode(db, tenant="tenant-b", run="run-b", prefix="b")
    assert a_id != b_id
    assert db.fetch_anomaly_episode_snapshot("tenant-a", b_id) is None
    assert db.fetch_anomaly_episode_snapshot("tenant-b", a_id) is None
    assert db.fetch_anomaly_episode_snapshot("tenant-a", MISSING_ID) is None
    assert db.fetch_anomaly_episode_snapshot("tenant-a", a_id)["episode"]["id"] == a_id
    assert db.fetch_anomaly_episode_snapshot("tenant-b", b_id)["episode"]["id"] == b_id


def test_snapshot_read_changes_nothing(episode_store):
    # La lectura es de solo lectura: ni episodios ni estado de detección cambian (ni `updated_at`).
    db = episode_store
    episode_id = open_episode(db)
    before = snapshot_state(db)
    assert before[1], "la detección debió dejar su estado guardado"
    assert db.fetch_anomaly_episode_snapshot("tenant-a", episode_id) is not None
    assert db.fetch_anomaly_episode_snapshot("tenant-a", MISSING_ID) is None
    assert snapshot_state(db) == before


def test_snapshot_uses_a_single_sql_statement(episode_store):
    # Una sola sentencia da una lectura coherente sin transacción explícita: la fila del episodio y la marca
    # sintética salen del mismo instante. Dos sentencias podrían ver estados distintos entre una y otra.
    db = episode_store
    episode_id = open_episode(db)
    statements = []

    def count(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", count)
    try:
        assert db.fetch_anomaly_episode_snapshot("tenant-a", episode_id) is not None
    finally:
        event.remove(db.engine, "before_cursor_execute", count)
    assert len(statements) == 1, statements


def test_snapshot_of_a_closed_episode_carries_closure_with_timezone(episode_store):
    # Un episodio cerrado trae motivo y `closed_at` con zona horaria. Si llegara sin zona, `explain_episode`
    # lo interpretaría en la hora local del servidor y podría mostrar otro día de cierre.
    db = episode_store
    episode_id = open_episode(db)
    db.change_anomaly_episode_status("tenant-a", episode_id, status="resolved", reason="Hecho", actor="alice")
    episode = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)["episode"]
    assert episode["status"] == "resolved" and episode["closure_reason"] == "Hecho"
    for key in ("closed_at", "status_changed_at", "created_at"):
        assert isinstance(episode[key], datetime), key
        assert episode[key].tzinfo is not None and episode[key].utcoffset() is not None, key


def test_snapshot_feeds_the_explainer_for_the_base_series(episode_store):
    # Integración real lectura + explicador: la subida (150.00 EUR, 37.50 %) y el impacto salen de los
    # operandos exactos leídos de la base, sin errores de tipo.
    db = episode_store
    episode_id = open_episode(db)
    result = explain_episode(db.fetch_anomaly_episode_snapshot("tenant-a", episode_id),
                             tenant_id="tenant-a", explained_at=EXPLAINED_AT)
    content = result["content"]
    assert "Subió 150.00 EUR (37.50 %)." in content
    assert "Impacto acumulado: 150.00 EUR en 1 día, hasta el 2026-09-08." in content
    assert "Nota de redondeo" not in content


def test_snapshot_feeds_the_explainer_with_the_rounding_note_for_fractional_amounts(episode_store):
    # Solo con operandos exactos (500.004) la subida absoluta es 100.004 > 100: se muestra 100.00 y la nota de
    # redondeo evita que parezca que no supera el umbral. Con importes ya redondeados la nota no aparecería.
    db = episode_store
    episode_id = open_episode(db, FRACTIONAL)
    result = explain_episode(db.fetch_anomaly_episode_snapshot("tenant-a", episode_id),
                             tenant_id="tenant-a", explained_at=EXPLAINED_AT)
    assert "Nota de redondeo: la subida absoluta exacta supera el umbral de 100.00 EUR" in result["content"]


def test_snapshot_feeds_the_explainer_for_a_closed_episode_with_the_utc_closing_date(episode_store):
    # El cierre se muestra con el motivo y la fecha de `closed_at` pasada a UTC (no la local del servidor).
    db = episode_store
    episode_id = open_episode(db)
    db.change_anomaly_episode_status("tenant-a", episode_id, status="resolved", reason="Hecho", actor="alice")
    snapshot = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)
    closed_day = snapshot["episode"]["closed_at"].astimezone(timezone.utc).date().isoformat()
    content = explain_episode(snapshot, tenant_id="tenant-a", explained_at=EXPLAINED_AT)["content"]
    assert "Cerrada el" in content
    assert 'con el motivo "Hecho"' in content
    assert f"Cerrada el {closed_day} (UTC) con el motivo" in content


def test_snapshot_is_stable_between_reads_so_the_evidence_id_does_not_change(episode_store):
    # El identificador de evidencia es un hash del contenido: si los operandos cambiaran de escala o de texto
    # entre dos lecturas del mismo episodio, el id cambiaría sin que cambiara nada real.
    db = episode_store
    episode_id = open_episode(db, FRACTIONAL)
    first = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)
    second = db.fetch_anomaly_episode_snapshot("tenant-a", episode_id)
    for key in ("reference_week_cost", "opening_observed_cost", "impact_numerator"):
        assert format(first["operands"][key], "f") == format(second["operands"][key], "f"), key
    ids = [explain_episode(item, tenant_id="tenant-a", explained_at=EXPLAINED_AT)["anomaly_evidence"]["id"]
           for item in (first, second)]
    assert ids[0] == ids[1]
