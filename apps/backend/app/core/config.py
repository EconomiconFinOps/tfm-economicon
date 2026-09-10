from functools import lru_cache
import os
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.runtime_secrets import PLACEHOLDERS, StartupError, register_secrets, validate_connections

class Settings(BaseSettings):
    api_port: int = 8000
    runtime_environment: Literal["production", "development", "test"] = "production"
    allow_insecure_local_database: bool = False
    database_url: SecretStr
    rabbitmq_url: SecretStr
    vector_database_url: SecretStr
    processor_queue_name: str = "processor:jobs"
    embedding_dimension: int = 8
    auth_secret_key: SecretStr
    auth_token_ttl_minutes: int = 480
    demo_seed_enabled: bool = False
    demo_password: SecretStr | None = None

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        validate_connections(self)
        key = self.auth_secret_key.get_secret_value()
        if not key.strip() or any(c in key for c in ("\r", "\n")):
            raise ValueError("JWT signing key must be nonempty and single-line")
        if self.runtime_environment != "test" and (len(key) < 32 or key.lower() in PLACEHOLDERS):
            raise ValueError("JWT signing key must have at least 32 characters and not be a placeholder")
        if self.demo_seed_enabled:
            password = self.demo_password.get_secret_value() if self.demo_password else ""
            if not password.strip() or any(c in password for c in ("\r", "\n")):
                raise ValueError("Demo seeding requires an external nonempty password")
            if self.runtime_environment != "test" and password.lower() in PLACEHOLDERS:
                raise ValueError("Demo seeding requires a nonlegacy password")
        return self

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )


@lru_cache
def get_settings() -> Settings:
    try:
        settings = Settings(_env_file=os.environ.get("ECONOMICON_ENV_FILE") or None)
    except Exception:
        raise StartupError("Invalid runtime configuration; check required credentials and settings.") from None
    register_secrets(settings)
    return settings
