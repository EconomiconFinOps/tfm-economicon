from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    processor_port: int = 8001
    processor_concurrency: int = 2
    processor_queue_name: str = "processor:jobs"
    database_url: str = "cockroachdb+psycopg://root@localhost:26257/defaultdb?sslmode=disable"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    vector_database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/embeddings"
    embedding_provider: str = "mock"
    embedding_dimension: int = 8
    embedding_model: str = "economicon-embedding"
    embedding_chunk_size: int = 500
    embedding_chunk_overlap: int = 50
    llm_provider: str = "mock"
    llm_model: str = "economicon-chat"
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

    @field_validator("embedding_provider", "llm_provider")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"mock", "litellm"}:
            raise ValueError("AI providers must be either 'mock' or 'litellm'")
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
    def validate_logical_model_alias(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or "/" in normalized:
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
        return value.rstrip("/")

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
        providers = {self.llm_provider, self.embedding_provider}
        if self.ai_execution_mode == "evaluation" and "mock" in providers:
            raise ValueError("evaluation mode does not allow mock AI providers")
        if "litellm" in providers and (
            not self.litellm_api_key or not self.litellm_api_key.get_secret_value().strip()
        ):
            raise ValueError("litellm_api_key is required when a LiteLLM provider is selected")
        if self.embedding_provider == "litellm" and self.embedding_dimension != 1536:
            raise ValueError("economicon-embedding requires embedding_dimension=1536")
        return self

    @field_validator("azure_cost_api_base_url")
    @classmethod
    def validate_azure_cost_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("azure_cost_api_base_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("azure_cost_api_base_url must not contain credentials")
        return value.rstrip("/")

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
