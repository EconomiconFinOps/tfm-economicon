from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
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
    azure_cost_auth_enabled: bool = True
    azure_cost_valid_tokens: str = "jupiter-local-token"
    azure_cost_forbidden_tokens: str = "jupiter-forbidden-token"
    azure_cost_page_size: int = 10
    azure_cost_skiptoken_secret: str = "jupiter-local-skiptoken-secret"
    azure_cost_default_scenario: str = "normal"
    azure_cost_fake_timeout_seconds: float = 2.0
    azure_cost_retry_after_seconds: int = 1

    @field_validator("azure_cost_page_size")
    @classmethod
    def validate_page_size(cls, value: int) -> int:
        if not 1 <= value <= 1000:
            raise ValueError("azure_cost_page_size must be between 1 and 1000")
        return value

    @field_validator("azure_cost_fake_timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: float) -> float:
        if not 0 <= value <= 30:
            raise ValueError("azure_cost_fake_timeout_seconds must be between 0 and 30")
        return value

    @field_validator("azure_cost_retry_after_seconds")
    @classmethod
    def validate_retry_after(cls, value: int) -> int:
        if not 0 <= value <= 3600:
            raise ValueError("azure_cost_retry_after_seconds must be between 0 and 3600")
        return value

    @field_validator("azure_cost_skiptoken_secret")
    @classmethod
    def validate_skiptoken_secret(cls, value: str) -> str:
        if len(value.strip()) < 16:
            raise ValueError("azure_cost_skiptoken_secret must contain at least 16 characters")
        return value

    @field_validator("azure_cost_default_scenario")
    @classmethod
    def validate_default_scenario(cls, value: str) -> str:
        supported = {
            "normal",
            "rate-limit",
            "server-error",
            "timeout",
            "empty-page",
            "invalid-data",
        }
        if value not in supported:
            raise ValueError(f"azure_cost_default_scenario must be one of: {', '.join(sorted(supported))}")
        return value

    @model_validator(mode="after")
    def validate_simulated_identities(self) -> "Settings":
        if self.azure_cost_auth_enabled and not self.valid_tokens:
            raise ValueError("azure_cost_valid_tokens must configure an allowed identity")
        if self.valid_tokens & self.forbidden_tokens:
            raise ValueError("simulated identities cannot be both allowed and forbidden")
        return self

    @property
    def valid_tokens(self) -> frozenset[str]:
        return self._token_set(self.azure_cost_valid_tokens)

    @property
    def forbidden_tokens(self) -> frozenset[str]:
        return self._token_set(self.azure_cost_forbidden_tokens)

    @staticmethod
    def _token_set(raw: str) -> frozenset[str]:
        return frozenset(token.strip() for token in raw.split(",") if token.strip())

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
