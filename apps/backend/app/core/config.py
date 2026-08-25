from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_port: int = 8000
    database_url: str = "cockroachdb+psycopg://root@localhost:26257/defaultdb?sslmode=disable"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    vector_database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/embeddings"
    processor_queue_name: str = "processor:jobs"
    embedding_dimension: int = 8
    auth_secret_key: str = "replace-me-auth-secret"
    auth_token_ttl_minutes: int = 480

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
