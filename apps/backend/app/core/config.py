from functools import lru_cache
import json
import os
import re
from typing import Literal

from pydantic import AnyHttpUrl, Field, Json, SecretStr, StrictStr, field_validator, model_validator
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
    auth_token_ttl_minutes: int = Field(default=480, gt=0)
    cors_allowed_origins: Json[list[StrictStr]] = Field(default_factory=list)
    demo_seed_enabled: bool = False
    demo_password: SecretStr | None = None

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def validate_origin_list(cls, value):
        # Json defers source decoding so explicit null cannot become a missing value.
        # List defaults and direct inputs use the same strict JSON validation.
        return json.dumps(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        validate_connections(self)
        for origin in self.cors_allowed_origins:
            url = AnyHttpUrl(origin)
            if (
                str(url) != origin + "/"
                or url.username is not None or url.password is not None
                or url.query is not None or url.fragment is not None
                or not url.host
                or not re.fullmatch(r"[a-z0-9.\-]+|\[[0-9a-f:]+\]", url.host)
                or (self.runtime_environment == "production" and url.scheme != "https")
            ):
                raise ValueError("CORS origins must be exact serialized origins for this environment")
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
