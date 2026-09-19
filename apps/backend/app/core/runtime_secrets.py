"""Runtime credential validation and bounded diagnostic redaction."""
from functools import wraps
import re
from urllib.parse import quote, quote_plus, unquote, urlsplit

from pydantic import SecretStr
from sqlalchemy.engine import make_url

REDACTED = "[REDACTED]"
_secret_values: tuple[str, ...] = ()
SENSITIVE_FIELDS = {
    "password", "password_hash", "authorization", "cookie", "set_cookie",
    "api_key", "access_token", "refresh_token", "token", "secret",
    "auth_secret_key", "database_url", "rabbitmq_url", "vector_database_url",
    "demo_password", "litellm_api_key", "litellm_master_key", "openrouter_api_key",
    "azure_cost_api_token", "grafana_admin_password",
}
PLACEHOLDERS = {"secret", "password", "changeme", "change-me", "replace-me", "replace-me-auth-secret"}
# Connection identity must come only from the DSN authority/path, not driver overrides.
DATABASE_QUERY_OPTIONS = {"sslmode", "connect_timeout", "application_name"}


class StartupError(RuntimeError):
    """An operator-facing error containing no underlying inputs."""


class DemoRotationRequired(StartupError):
    def __init__(self):
        super().__init__("Legacy demo credential detected; explicitly rotate the stored demo password before startup.")


def startup_boundary(function):
    @wraps(function)
    def guarded(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except StartupError:
            raise
        except Exception:
            raise StartupError("Runtime startup failed; check configuration and dependency availability.") from None
        except SystemExit as exc:
            if exc.code not in (None, 0):
                raise StartupError("Runtime startup failed.") from None
            raise
    return guarded


def validate_connections(settings):
    if settings.allow_insecure_local_database and settings.runtime_environment == "production":
        raise ValueError("Local database opt-in is forbidden in production")
    for name in ("database_url", "rabbitmq_url", "vector_database_url"):
        raw = getattr(settings, name).get_secret_value()
        try:
            if not raw.strip() or any(c.isspace() for c in raw):
                raise ValueError()
            if name == "rabbitmq_url":
                parsed = urlsplit(raw)
                valid = parsed.scheme in {"amqp", "amqps"} and parsed.hostname and parsed.port != 0
                username, password = unquote(parsed.username or ""), unquote(parsed.password or "")
            else:
                parsed = make_url(raw)
                if any(
                    key not in DATABASE_QUERY_OPTIONS or not isinstance(value, str)
                    for key, value in parsed.query.items()
                ):
                    raise ValueError()
                valid = parsed.host and parsed.port != 0 and parsed.database
                valid = valid and parsed.drivername in (
                    {"cockroachdb", "cockroachdb+psycopg", "cockroachdb+psycopg2"}
                    if name == "database_url" else {"postgresql", "postgresql+psycopg", "postgresql+psycopg2"}
                )
                username, password = parsed.username or "", parsed.password or ""
            if not valid:
                raise ValueError()
        except Exception:
            raise ValueError(f"{name} must be a valid service DSN") from None
        if name == "database_url":
            insecure = not password.strip() or parsed.query.get("sslmode") == "disable"
            if insecure and not (
                settings.allow_insecure_local_database
                and settings.runtime_environment in {"development", "test"}
                and parsed.host in {"localhost", "127.0.0.1", "::1", "cockroachdb"}
            ):
                raise ValueError("Unauthenticated or insecure database requires the isolated local opt-in")
        elif not username.strip() or not password.strip():
            raise ValueError(f"{name} requires nonempty credentials")
        if settings.runtime_environment != "test":
            if password.lower() in PLACEHOLDERS:
                raise ValueError(f"{name} contains a known credential placeholder")
            if name == "rabbitmq_url" and username == password == "guest":
                raise ValueError("Default broker credentials are forbidden")
            if name == "vector_database_url" and password == "postgres":
                raise ValueError("Default vector database password is forbidden")


def register_secrets(settings):
    global _secret_values
    values = set()
    for name in type(settings).model_fields:
        value = getattr(settings, name)
        if not isinstance(value, SecretStr):
            continue
        raw = value.get_secret_value()
        if raw:
            values.add(raw)
        if name.endswith("_url"):
            try:
                password = (urlsplit(raw).password if name == "rabbitmq_url" else make_url(raw).password)
                if password:
                    values.add(unquote(password) if name == "rabbitmq_url" else password)
            except Exception:
                pass
    for value in tuple(values):
        values.update((quote(value, safe=""), quote_plus(value, safe="")))
    _secret_values = tuple(sorted(values, key=len, reverse=True))


def redact(value):
    if isinstance(value, SecretStr):
        return REDACTED
    if isinstance(value, dict):
        return {
            redact(str(key)): REDACTED if str(key).lower().replace("-", "_") in SENSITIVE_FIELDS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if not isinstance(value, (str, int, float, bool, type(None))):
        value = str(value)
    if isinstance(value, str):
        for secret in _secret_values:
            value = value.replace(secret, REDACTED)
        # Also omit complete URLs in third-party messages (including HTTP access logs).
        value = re.sub(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+", "[URL]", value)
    return value


def redact_event(logger, method_name, event_dict):
    return redact(event_dict)
