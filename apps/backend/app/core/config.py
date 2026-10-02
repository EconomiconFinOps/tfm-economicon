from functools import lru_cache
import json
import math
import os
import re
from typing import Literal
from urllib.parse import urlsplit

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
    embedding_provider: str = "mock"
    embedding_dimension: int = 8
    embedding_model: str = "economicon-embedding"
    litellm_base_url: str = "http://litellm:4000/v1"
    litellm_api_key: SecretStr | None = None
    embedding_timeout_seconds: float = 30.0
    embedding_max_retries: int = 2
    retrieval_top_k: int = 4
    retrieval_max_distance: float | None = None
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

    @field_validator("embedding_provider")
    @classmethod
    def validate_embedding_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"mock", "litellm"}:
            raise ValueError("embedding_provider must be either 'mock' or 'litellm'")
        return normalized

    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, value: str) -> str:
        normalized = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", normalized):
            raise ValueError("embedding_model must be a non-empty LiteLLM logical model alias")
        return normalized

    @field_validator("litellm_base_url")
    @classmethod
    def validate_litellm_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("litellm_base_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("litellm_base_url must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("litellm_base_url must not contain a query or fragment")
        try:
            parsed.port
        except ValueError:
            raise ValueError("litellm_base_url contains an invalid port") from None
        return value.rstrip("/")

    @field_validator("litellm_api_key")
    @classmethod
    def validate_litellm_api_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        key = value.get_secret_value()
        if any(character in key for character in ("\r", "\n")):
            raise ValueError("litellm_api_key must be a single-line gateway credential")
        if key.startswith("sk-or-"):
            raise ValueError("litellm_api_key must not contain an OpenRouter upstream key")
        return value

    @field_validator("embedding_timeout_seconds")
    @classmethod
    def validate_embedding_timeout(cls, value: float) -> float:
        if not math.isfinite(value) or not 0 < value <= 300:
            raise ValueError("embedding_timeout_seconds must be between 0 and 300")
        return value

    @field_validator("embedding_max_retries")
    @classmethod
    def validate_embedding_retries(cls, value: int) -> int:
        if not 0 <= value <= 10:
            raise ValueError("embedding_max_retries must be between 0 and 10")
        return value

    @field_validator("retrieval_top_k")
    @classmethod
    def validate_retrieval_top_k(cls, value: int) -> int:
        if not 1 <= value <= 20:
            raise ValueError("retrieval_top_k must be between 1 and 20")
        return value

    @field_validator("retrieval_max_distance", mode="before")
    @classmethod
    def validate_retrieval_max_distance(cls, value):
        if isinstance(value, str):
            if not value.strip():
                return None
            try:
                value = float(value)
            except ValueError:
                raise ValueError("retrieval_max_distance must be a number") from None
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value <= 2:
            raise ValueError("retrieval_max_distance must be greater than 0 and at most 2")
        return float(value)

    @model_validator(mode="after")
    def validate_embedding_configuration(self) -> "Settings":
        if self.embedding_provider == "mock" and self.runtime_environment not in {"development", "test"}:
            raise ValueError("embedding_provider mock is only allowed in development and test")
        if self.embedding_provider == "litellm":
            if not self.litellm_api_key or not self.litellm_api_key.get_secret_value().strip():
                raise ValueError("litellm_api_key is required when embedding_provider is litellm")
            if self.embedding_dimension != 1536:
                raise ValueError("embedding_dimension must be 1536 for the economicon-embedding alias")
        return self

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
