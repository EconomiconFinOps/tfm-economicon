from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    processor_port: int = 8001
    processor_concurrency: int = 2
    processor_queue_name: str = "processor:jobs"
    database_url: str = "postgresql+psycopg://root@localhost:26257/defaultdb?sslmode=disable"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    vector_database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/embeddings"
    embedding_provider: str = "mock"
    embedding_dimension: int = 8
    embedding_chunk_size: int = 500
    embedding_chunk_overlap: int = 50
    llm_provider: str = "mock"
    openai_api_key: str = "replace-me"
    azure_cost_api_base_url: str = "http://azure-cost-api:8002"
    azure_cost_api_token: SecretStr = SecretStr("jupiter-local-token")
    azure_cost_api_version: str = "2025-03-01"
    azure_cost_api_timeout_seconds: float = 5.0
    azure_cost_api_max_retries: int = 3
    azure_cost_api_retry_backoff_seconds: float = 0.25
    azure_cost_api_max_retry_after_seconds: float = 30.0
    azure_cost_api_max_pages: int = 1000

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
