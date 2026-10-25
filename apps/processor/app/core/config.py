from functools import lru_cache
import os
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.runtime_secrets import StartupError, register_secrets, validate_connections

class Settings(BaseSettings):
    processor_port: int = 8001
    processor_concurrency: int = 2
    document_s3_access_key: SecretStr | None = None
    document_s3_secret_key: SecretStr | None = None
    processor_queue_name: str = "processor:jobs"
    summary_timeout_seconds: int = Field(default=180, ge=30, le=300)
    runtime_environment: Literal["production", "development", "test"] = "production"
    allow_insecure_local_database: bool = False
    database_url: SecretStr
    rabbitmq_url: SecretStr
    vector_database_url: SecretStr
    embedding_provider: str = "mock"
    embedding_dimension: int = 8
    embedding_model: str = "economicon-embedding"
    bedrock_region: Literal["eu-west-1"] | None = None
    bedrock_timeout_seconds: float = Field(default=20, gt=0, le=30, allow_inf_nan=False)
    embedding_mapping_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    embedding_deployment_id: str | None = Field(default=None, strict=True, pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
    # Character settings remain available for the explicit legacy comparison utility.
    embedding_chunk_target_tokens: int = Field(default=600, ge=8, le=800, strict=True)
    embedding_chunk_max_tokens: int = Field(default=800, ge=8, le=800, strict=True)
    embedding_chunk_overlap_ratio: float = Field(default=0.1, ge=0, lt=1, allow_inf_nan=False)
    embedding_chunk_size: int = 500
    embedding_chunk_overlap: int = 50
    llm_provider: str = "mock"
    llm_model: str = "economicon-chat"
    bedrock_chat_model_id: Literal["eu.amazon.nova-micro-v1:0", "eu.amazon.nova-lite-v1:0"] | None = None
    ai_execution_mode: str = "development"
    litellm_base_url: str = "http://litellm:4000/v1"
    litellm_api_key: SecretStr | None = None
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_max_output_tokens: int = 800
    azure_cost_api_base_url: str = "http://azure-cost-api:8002"
    azure_cost_api_token: SecretStr = SecretStr("jupiter-local-token")
    azure_cost_api_version: str = "2025-03-01"
    azure_cost_api_timeout_seconds: float = 5.0
    azure_cost_api_max_retries: int = 3
    azure_cost_api_retry_backoff_seconds: float = 0.25
    azure_cost_api_max_retry_after_seconds: float = 30.0
    azure_cost_api_max_pages: int = 1000

    @field_validator('embedding_mapping_sha256', 'embedding_deployment_id', mode='before')
    @classmethod
    def empty_mapping(cls, value):
        return None if value == '' else value

    @field_validator('embedding_chunk_target_tokens', 'embedding_chunk_max_tokens', mode='before')
    @classmethod
    def parse_chunk_tokens(cls, value):
        # Environment values are strings; constructor booleans/fractions remain invalid.
        if isinstance(value, str) and re.fullmatch(r'[0-9]+', value):
            return int(value)
        return value

    @field_validator('embedding_chunk_overlap_ratio', mode='before')
    @classmethod
    def reject_boolean_overlap(cls, value):
        if isinstance(value, bool):
            raise ValueError('overlap ratio must be numeric')
        return value

    @field_validator("embedding_provider", "llm_provider")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"mock", "litellm", "bedrock"}:
            raise ValueError("AI providers must be 'mock', 'litellm' or 'bedrock'")
        return normalized

    @field_validator("ai_execution_mode")
    @classmethod
    def validate_execution_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"test", "development", "evaluation"}:
            raise ValueError("ai_execution_mode must be test, development, or evaluation")
        return normalized

    @field_validator("llm_model", "embedding_model")
    @classmethod
    def validate_logical_model_alias(cls, value: str, info) -> str:
        normalized = value.strip()
        native_embedding = info.field_name == 'embedding_model' and normalized == 'amazon.titan-embed-text-v2:0'
        if not native_embedding and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", normalized):
            raise ValueError("services must use a non-empty LiteLLM logical model alias")
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
        except ValueError as exc:
            raise ValueError("litellm_base_url contains an invalid port") from exc
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

    @field_validator("llm_timeout_seconds")
    @classmethod
    def validate_llm_timeout(cls, value: float) -> float:
        if not 0 < value <= 300:
            raise ValueError("llm_timeout_seconds must be between 0 and 300")
        return value

    @field_validator("llm_max_retries")
    @classmethod
    def validate_llm_retries(cls, value: int) -> int:
        if not 0 <= value <= 10:
            raise ValueError("llm_max_retries must be between 0 and 10")
        return value

    @field_validator("llm_max_output_tokens")
    @classmethod
    def validate_max_output_tokens(cls, value: int) -> int:
        if not 1 <= value <= 8192:
            raise ValueError("llm_max_output_tokens must be between 1 and 8192")
        return value

    @model_validator(mode="after")
    def validate_ai_configuration(self) -> "Settings":
        from app.embeddings.contracts import ChunkingConfig
        ChunkingConfig(self.embedding_chunk_target_tokens, self.embedding_chunk_max_tokens,
                       self.embedding_chunk_overlap_ratio)
        providers = {self.llm_provider, self.embedding_provider}
        if self.llm_provider == "litellm" and self.llm_model != "economicon-chat":
            raise ValueError("economicon-chat is the only active generative alias")
        if self.ai_execution_mode == "evaluation" and "mock" in providers:
            raise ValueError("evaluation mode does not allow mock AI providers")
        if "litellm" in providers and (
            not self.litellm_api_key or not self.litellm_api_key.get_secret_value().strip()
        ):
            raise ValueError("litellm_api_key is required when a LiteLLM provider is selected")
        if self.embedding_provider == "litellm" and self.embedding_dimension != 1536:
            raise ValueError("economicon-embedding requires embedding_dimension=1536")
        if "litellm" in providers:
            if self.llm_timeout_seconds > 30:
                raise ValueError("llm_timeout_seconds must not exceed 30 for LiteLLM")
            if self.llm_max_retries > 2:
                raise ValueError("llm_max_retries must not exceed 2 for LiteLLM")
            if self.llm_max_output_tokens > 800:
                raise ValueError("llm_max_output_tokens must not exceed 800 for LiteLLM")
        return self

    @field_validator("azure_cost_api_base_url")
    @classmethod
    def validate_azure_cost_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("azure_cost_api_base_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("azure_cost_api_base_url must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("azure_cost_api_base_url must not contain a query or fragment")
        try:
            parsed.port
        except ValueError as exc:
            raise ValueError("azure_cost_api_base_url contains an invalid port") from exc
        return value.rstrip("/")

    @field_validator("azure_cost_api_token")
    @classmethod
    def validate_azure_cost_token(cls, value: SecretStr) -> SecretStr:
        token = value.get_secret_value()
        if not token.strip() or any(character in token for character in ("\r", "\n")):
            raise ValueError("azure_cost_api_token must be a non-empty single-line bearer")
        return value

    @field_validator("azure_cost_api_version")
    @classmethod
    def validate_azure_cost_api_version(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("azure_cost_api_version must not be empty")
        return value

    @field_validator("azure_cost_api_timeout_seconds")
    @classmethod
    def validate_azure_cost_timeout(cls, value: float) -> float:
        if not 0 < value <= 300:
            raise ValueError("azure_cost_api_timeout_seconds must be between 0 and 300")
        return value

    @field_validator("azure_cost_api_max_retries")
    @classmethod
    def validate_azure_cost_retries(cls, value: int) -> int:
        if not 0 <= value <= 10:
            raise ValueError("azure_cost_api_max_retries must be between 0 and 10")
        return value

    @field_validator(
        "azure_cost_api_retry_backoff_seconds",
        "azure_cost_api_max_retry_after_seconds",
    )
    @classmethod
    def validate_azure_cost_delay(cls, value: float) -> float:
        if not 0 <= value <= 300:
            raise ValueError("Azure cost retry delays must be between 0 and 300")
        return value

    @field_validator("azure_cost_api_max_pages")
    @classmethod
    def validate_azure_cost_max_pages(cls, value: int) -> int:
        if not 1 <= value <= 10000:
            raise ValueError("azure_cost_api_max_pages must be between 1 and 10000")
        return value

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        if self.embedding_model == 'amazon.titan-embed-text-v2:0' and self.embedding_provider != 'bedrock':
            raise ValueError('Native embedding model identity requires the Bedrock provider')
        if self.llm_provider == 'bedrock' and (self.bedrock_region is None
                or self.bedrock_chat_model_id is None or self.llm_model != 'economicon-chat'):
            raise ValueError('Bedrock chat requires an explicit EU profile from Ireland and the approved chat contract')
        if self.embedding_provider == 'bedrock':
            if (self.bedrock_region is None or self.embedding_model != 'amazon.titan-embed-text-v2:0'
                    or self.embedding_dimension not in {256,512,1024}):
                raise ValueError('Bedrock embeddings require explicit Ireland region, Titan V2 and a native dimension')
        validate_connections(self)
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
