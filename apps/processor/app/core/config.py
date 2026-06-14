from functools import lru_cache

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
