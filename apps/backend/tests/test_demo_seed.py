"""JUP-053 demo scenarios: create-only opt-in, rotation and legacy refusal."""
import re
import traceback
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event, text

from app.core.config import get_settings
from app.core.security import decode_access_token, hash_password, verify_password
from app.db.database import Database, USER_SEED
from conftest import SYNTHETIC_ENV

DEMO_PASSWORD = "jup053-external-demo-password"
ROTATED_PASSWORD = "jup053-explicitly-rotated-password"


@pytest.fixture
def database(monkeypatch, production_env):
    engine = create_engine("sqlite://")

    # SQLite's REPLACE reproduces the current Cockroach UPSERT overwrite so the
    # test observes stored state; INSERT ... ON CONFLICT remains executable too.
    @event.listens_for(engine, "before_cursor_execute", retval=True)
    def adapt_upsert(connection, cursor, statement, parameters, context, executemany):
        return re.sub(r"\bUPSERT\s+INTO\b", "INSERT OR REPLACE INTO", statement, flags=re.I), parameters

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE tenants (id TEXT PRIMARY KEY, name TEXT, slug TEXT, plan TEXT)"))
        connection.execute(text(
            "CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, "
            "full_name TEXT, role TEXT, created_at TEXT)"
        ))
        connection.execute(text(
            "CREATE TABLE user_tenants (user_id TEXT, tenant_id TEXT, role TEXT, created_at TEXT, "
            "PRIMARY KEY(user_id, tenant_id))"
        ))
    with patch("app.db.database.create_engine", return_value=engine), patch("app.db.database.MigrationRunner.run"):
        instance = Database(SYNTHETIC_ENV["DATABASE_URL"])
        yield instance
    engine.dispose()


def enable_seed(monkeypatch):
    monkeypatch.setenv("DEMO_SEED_ENABLED", "true")
    monkeypatch.setenv("DEMO_PASSWORD", DEMO_PASSWORD)
    get_settings.cache_clear()


def insert_existing(database, password):
    row = {
        "id": USER_SEED["id"], "email": "operator@example.com",
        "password_hash": hash_password(password), "full_name": "Existing Operator",
        "role": "admin", "created_at": "2026-01-01",
    }
    with database.engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO users (id,email,password_hash,full_name,role,created_at) "
            "VALUES (:id,:email,:password_hash,:full_name,:role,:created_at)"
        ), row)
        connection.execute(text(
            "INSERT INTO user_tenants VALUES (:user_id, 'tenant-core', 'viewer', '2026-01-01')"
        ), {"user_id": row["id"]})
    return row


def snapshot(database):
    with database.engine.connect() as connection:
        return {
            table: [dict(row) for row in connection.execute(text(f"SELECT * FROM {table}")).mappings()]
            for table in ("users", "user_tenants")
        }


def test_demo_seed_defaults_off_and_creates_no_account(database, monkeypatch):
    monkeypatch.delenv("DEMO_SEED_ENABLED")
    database.initialize()
    assert database.fetch_user_by_email("operator@example.com") is None
    assert snapshot(database)["user_tenants"] == []


def test_explicit_demo_seed_creates_account_with_external_password(database, monkeypatch):
    enable_seed(monkeypatch)
    database.initialize()
    user = database.fetch_user_by_email("operator@example.com")
    assert user is not None
    assert user["id"] == USER_SEED["id"]
    assert user["role"] == "admin"
    assert verify_password(DEMO_PASSWORD, user["password_hash"])
    assert not verify_password("secret", user["password_hash"])
    assert {row["tenant_id"] for row in snapshot(database)["user_tenants"]} == {"tenant-core", "tenant-growth"}


def test_restarts_do_not_overwrite_rotated_hash_identity_or_existing_role(database, monkeypatch):
    enable_seed(monkeypatch)
    original = insert_existing(database, ROTATED_PASSWORD)
    database.initialize()
    user = database.fetch_user_by_email("operator@example.com")
    assert user["password_hash"] == original["password_hash"]
    assert user["id"] == original["id"] and user["full_name"] == original["full_name"]
    assert user["role"] == original["role"]
    existing = next(row for row in snapshot(database)["user_tenants"] if row["tenant_id"] == "tenant-core")
    assert existing["role"] == "viewer"
    first_restart = snapshot(database)
    monkeypatch.setenv("DEMO_PASSWORD", "jup053-different-external-password")
    get_settings.cache_clear()
    database.initialize()
    assert snapshot(database) == first_restart


@pytest.mark.parametrize("seed_enabled", ["false", "true"])
def test_legacy_password_blocks_startup_without_automatic_rotation(database, monkeypatch, seed_enabled):
    insert_existing(database, "secret")
    before = snapshot(database)
    monkeypatch.setenv("DEMO_SEED_ENABLED", seed_enabled)
    monkeypatch.setenv("DEMO_PASSWORD", DEMO_PASSWORD)
    get_settings.cache_clear()
    with pytest.raises(Exception) as failure:
        database.initialize()
    message = "".join(traceback.format_exception(failure.value)).lower()
    assert "rotat" in message, "The operator must receive an explicit rotation instruction"
    assert DEMO_PASSWORD not in message
    assert snapshot(database) == before


def test_manual_demo_login_preserves_token_and_identity_contract(database):
    from app.api.routes.auth import login
    from app.schemas.auth import LoginRequest

    insert_existing(database, ROTATED_PASSWORD)
    response = login(LoginRequest(email="operator@example.com", password=ROTATED_PASSWORD), database)
    assert response.token_type == "bearer" and response.access_token
    assert response.user.id == USER_SEED["id"]
    assert response.user.email == "operator@example.com" and response.user.role == "admin"
    claims = decode_access_token(response.access_token, SYNTHETIC_ENV["AUTH_SECRET_KEY"])
    assert claims["sub"] == USER_SEED["id"] and "exp" in claims


def test_explicit_jwt_rotation_invalidates_old_tokens_without_changing_claims():
    from app.core.security import create_access_token
    from jwt import InvalidSignatureError

    token = create_access_token(USER_SEED["id"], SYNTHETIC_ENV["AUTH_SECRET_KEY"], 480)
    with pytest.raises(InvalidSignatureError):
        decode_access_token(token, "jup053-rotated-jwt-key-0123456789abcdef")
