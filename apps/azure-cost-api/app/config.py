from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repository_root() -> Path:
    """Locate the data root both in the source tree and in the container image."""
    module_path = Path(__file__).resolve()
    return next(
        (
            parent
            for parent in module_path.parents
            if (parent / "fixtures").is_dir() and (parent / "docs" / "api").is_dir()
        ),
        module_path.parent,
    )


REPOSITORY_ROOT = _find_repository_root()


class Settings(BaseSettings):
    azure_cost_api_port: int = 8002
    azure_cost_dataset_path: Path = (
        REPOSITORY_ROOT / "fixtures/azure-cost/EA-Cost-Actual.sample.csv"
    )
    azure_cost_mapping_path: Path = (
        REPOSITORY_ROOT / "docs/api/azure-cost-query-mapping.json"
    )
    azure_cost_openapi_path: Path = (
        REPOSITORY_ROOT / "docs/api/azure-cost-query.openapi.json"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
