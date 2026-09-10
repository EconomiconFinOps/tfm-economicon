"""JUP-053: external inputs, precedence, test isolation and approved local boundary."""
import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
from conftest import SYNTHETIC_ENV


def _effective_driver_kwargs(raw):
    from sqlalchemy.engine import make_url

    url = make_url(raw)
    positional, keyword = url.get_dialect()().create_connect_args(url)
    assert not positional
    return keyword


@pytest.mark.parametrize("query,effective", [
    ("host=shared.example.invalid", {"host": "shared.example.invalid"}),
    ("hostaddr=203.0.113.8", {"hostaddr": "203.0.113.8"}),
    ("hostaddr=2001%3Adb8%3A%3A8", {"hostaddr": "2001:db8::8"}),
    ("host=localhost,shared.example.invalid&port=26257,26258",
     {"host": "localhost,shared.example.invalid", "port": "26257,26258"}),
    ("host=localhost:26257&host=shared.example.invalid:26258",
     {"host": "localhost,shared.example.invalid", "port": "26257,26258"}),
    ("hostaddr=127.0.0.1&hostaddr=203.0.113.8",
     {"hostaddr": ("127.0.0.1", "203.0.113.8")}),
])
def test_rf053_001_query_cannot_redirect_local_database(monkeypatch, query, effective):
    """Authority localhost does not constrain libpq's effective target."""
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "development")
    monkeypatch.setenv("ALLOW_INSECURE_LOCAL_DATABASE", "true")
    raw = "cockroachdb+psycopg://root@localhost:26257/unit?sslmode=disable&" + query
    driver = _effective_driver_kwargs(raw)
    assert driver["sslmode"] == "disable"
    assert all(driver[key] == value for key, value in effective.items())
    monkeypatch.setenv("DATABASE_URL", raw)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("field", ["DATABASE_URL", "VECTOR_DATABASE_URL"])
@pytest.mark.parametrize("query,effective", [
    ("password=postgres", {"password": "postgres"}),
    ("user=alternate-user", {"user": "alternate-user"}),
    ("dbname=alternate-db", {"dbname": "alternate-db"}),
    ("database=alternate-db", {"database": "alternate-db"}),
    ("port=6543", {"port": "6543"}),
    ("service=untrusted-profile", {"service": "untrusted-profile"}),
    ("passfile=/jup053-nonexistent-credentials", {"passfile": "/jup053-nonexistent-credentials"}),
    ("password=synthetic-first&password=postgres", {"password": ("synthetic-first", "postgres")}),
])
def test_rf053_001_query_cannot_override_connection_identity(
    production_env, monkeypatch, field, query, effective,
):
    """Reject forwarded selectors, including invalid/ambiguous driver inputs."""
    separator = "&" if "?" in SYNTHETIC_ENV[field] else "?"
    raw = SYNTHETIC_ENV[field] + separator + query
    driver = _effective_driver_kwargs(raw)
    assert all(driver[key] == value for key, value in effective.items())
    monkeypatch.setenv(field, raw)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("field", ["DATABASE_URL", "VECTOR_DATABASE_URL"])
def test_rf053_001_legitimate_secure_query_options_reach_driver(production_env, monkeypatch, field):
    from sqlalchemy.engine import make_url

    raw = str(make_url(SYNTHETIC_ENV[field]).set(query={
        "sslmode": "verify-full",
        "connect_timeout": "5",
        "application_name": "jup053-query-control",
    }).render_as_string(hide_password=False))
    monkeypatch.setenv(field, raw)
    settings = Settings(_env_file=None)
    value = getattr(settings, field.lower()).get_secret_value()
    driver = _effective_driver_kwargs(value)
    authority = make_url(SYNTHETIC_ENV[field])
    assert driver["host"] == authority.host
    assert driver["password"] == authority.password
    assert driver["user"] == authority.username
    assert driver["dbname"] == authority.database
    assert int(driver["port"]) == authority.port
    assert driver["sslmode"] == "verify-full"
    assert driver["connect_timeout"] == "5"
    assert driver["application_name"] == "jup053-query-control"


REQUIRED = ["DATABASE_URL", "RABBITMQ_URL", "VECTOR_DATABASE_URL"]
if "auth_secret_key" in Settings.model_fields:
    REQUIRED.append("AUTH_SECRET_KEY")


@pytest.mark.parametrize("name", REQUIRED)
@pytest.mark.parametrize("runtime", ["production", "test"])
def test_required_credentials_have_no_fallback(monkeypatch, name, runtime):
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", runtime)
    monkeypatch.delenv(name)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("name", REQUIRED)
@pytest.mark.parametrize("value", ["", "   "])
def test_blank_credentials_rejected(production_env, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("name,value", [
    ("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
    ("RABBITMQ_URL", "amqp://unit:@localhost:5672/%2F"),
    ("VECTOR_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/unit"),
    ("VECTOR_DATABASE_URL", "postgresql+psycopg://unit:@localhost:5432/unit"),
])
def test_known_unsafe_service_credentials_rejected(production_env, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_explicit_credentials_are_masked_and_recoverable(production_env):
    settings = Settings(_env_file=None)
    for name in REQUIRED:
        value = getattr(settings, name.lower())
        assert isinstance(value, SecretStr), name
        assert value.get_secret_value() == SYNTHETIC_ENV[name]
        assert SYNTHETIC_ENV[name] not in repr(settings)
        assert SYNTHETIC_ENV[name] not in settings.model_dump_json()


def test_no_implicit_dotenv(monkeypatch, tmp_path):
    port = "API_PORT" if "api_port" in Settings.model_fields else "PROCESSOR_PORT"
    (tmp_path / ".env").write_text(f"{port}=19123\n", encoding="utf-8")
    assert getattr(get_settings(), port.lower()) != 19123


def test_explicit_dotenv_environment_wins_and_foreign_keys_are_ignored(monkeypatch, tmp_path):
    port = "API_PORT" if "api_port" in Settings.model_fields else "PROCESSOR_PORT"
    dotenv = tmp_path / "synthetic.env"
    dotenv.write_text(
        f"{port}=19123\nRABBITMQ_URL=amqp://unit:file-fixture-pass@localhost:5672/%2F\n"
        "UNRELATED_SHARED_SERVICE_OPTION=synthetic\n", encoding="utf-8",
    )
    monkeypatch.setenv("ECONOMICON_ENV_FILE", str(dotenv))
    settings = get_settings()
    assert getattr(settings, port.lower()) == 19123
    value = settings.rabbitmq_url
    assert (value.get_secret_value() if isinstance(value, SecretStr) else value) == SYNTHETIC_ENV["RABBITMQ_URL"]


@pytest.mark.parametrize("runtime,opt_in,target", [
    ("development", None, "localhost"),
    ("test", None, "127.0.0.1"),
    ("production", "true", "localhost"),
    ("development", "true", "shared.example.invalid"),
    ("test", "true", "localhost.attacker.invalid"),
])
def test_local_exception_rejects_absent_opt_in_production_and_nonlocal_targets(
    monkeypatch, runtime, opt_in, target,
):
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", runtime)
    if opt_in is None:
        monkeypatch.delenv("ALLOW_INSECURE_LOCAL_DATABASE")
    else:
        monkeypatch.setenv("ALLOW_INSECURE_LOCAL_DATABASE", opt_in)
    monkeypatch.setenv("DATABASE_URL", f"cockroachdb+psycopg://root@{target}:26257/unit?sslmode=disable")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("runtime,target", [
    ("development", "localhost"), ("test", "127.0.0.1"), ("development", "cockroachdb"),
])
def test_approved_local_settings_allow_only_explicit_disposable_fixture(monkeypatch, runtime, target):
    # The fixture models isolation; URL validation cannot prove operator-confirmed isolation.
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", runtime)
    monkeypatch.setenv("ALLOW_INSECURE_LOCAL_DATABASE", "true")
    monkeypatch.setenv("DATABASE_URL", f"cockroachdb+psycopg://root@{target}:26257/unit?sslmode=disable")
    settings = Settings(_env_file=None)
    assert settings is not None


@pytest.mark.parametrize("name,value", [
    ("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
    ("VECTOR_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/unit"),
])
def test_local_exception_does_not_disable_other_secret_protections(monkeypatch, name, value):
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "development")
    monkeypatch.setenv("ALLOW_INSECURE_LOCAL_DATABASE", "true")
    monkeypatch.setenv("DATABASE_URL", "cockroachdb+psycopg://root@localhost:26257/unit?sslmode=disable")
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_pytest_and_ai_test_mode_do_not_enable_runtime_exception(monkeypatch):
    monkeypatch.delenv("RUNTIME_ENVIRONMENT")
    monkeypatch.setenv("AI_EXECUTION_MODE", "test")
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
