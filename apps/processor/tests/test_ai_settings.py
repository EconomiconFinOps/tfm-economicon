import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_development_configuration_keeps_mocks_available():
    settings = Settings(_env_file=None)

    assert settings.ai_execution_mode == "development"
    assert settings.llm_provider == "mock"
    assert settings.embedding_provider == "mock"


def test_evaluation_rejects_mock_providers():
    with pytest.raises(ValidationError, match="does not allow mock"):
        Settings(ai_execution_mode="evaluation", _env_file=None)


@pytest.mark.parametrize("key", [None, "", "   "])
def test_litellm_requires_gateway_key(key):
    with pytest.raises(ValidationError, match="litellm_api_key is required"):
        Settings(llm_provider="litellm", litellm_api_key=key, _env_file=None)


def test_services_cannot_bypass_gateway_with_provider_model_id():
    with pytest.raises(ValidationError, match="logical model alias"):
        Settings(llm_model="z-ai/glm-5.2", _env_file=None)


def test_real_embeddings_require_decided_dimension():
    with pytest.raises(ValidationError, match="embedding_dimension=1536"):
        Settings(
            embedding_provider="litellm",
            litellm_api_key="gateway-secret",
            embedding_dimension=8,
            _env_file=None,
        )


def test_valid_litellm_evaluation_configuration_hides_secret():
    settings = Settings(
        ai_execution_mode="evaluation",
        llm_provider="litellm",
        embedding_provider="litellm",
        embedding_dimension=1536,
        litellm_api_key="gateway-secret",
        _env_file=None,
    )

    assert settings.llm_model == "economicon-chat"
    assert settings.embedding_model == "economicon-embedding"
    assert "gateway-secret" not in repr(settings)
