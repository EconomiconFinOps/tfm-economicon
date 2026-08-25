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


@pytest.mark.parametrize(
    "alias",
    ["", "../provider", "economicon chat", "economicon\nchat", "a" * 129],
)
def test_services_reject_unsafe_or_unbounded_model_aliases(alias):
    with pytest.raises(ValidationError, match="logical model alias"):
        Settings(llm_model=alias, _env_file=None)


@pytest.mark.parametrize(
    "base_url",
    [
        "file:///etc/passwd",
        "http://user:secret@litellm:4000/v1",
        "http://litellm:4000/v1?token=secret",
        "http://litellm:4000/v1#fragment",
        "http://litellm:99999/v1",
    ],
)
def test_gateway_rejects_unsafe_base_urls(base_url):
    with pytest.raises(ValidationError, match="litellm_base_url"):
        Settings(litellm_base_url=base_url, _env_file=None)


@pytest.mark.parametrize("key", ["gateway\rsecret", "gateway\nsecret", "sk-or-v1-upstream"])
def test_gateway_rejects_header_injection_and_upstream_key_reuse(key):
    with pytest.raises(ValidationError, match="litellm_api_key"):
        Settings(llm_provider="litellm", litellm_api_key=key, _env_file=None)


@pytest.mark.parametrize("provider", ["openrouter", "openai", "azure", ""])
def test_services_accept_only_mock_or_litellm_providers(provider):
    with pytest.raises(ValidationError, match="AI providers"):
        Settings(llm_provider=provider, _env_file=None)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("llm_timeout_seconds", 0),
        ("llm_timeout_seconds", 301),
        ("llm_max_retries", -1),
        ("llm_max_retries", 11),
        ("llm_max_output_tokens", 0),
        ("llm_max_output_tokens", 8193),
    ],
)
def test_operational_llm_limits_are_bounded(field, value):
    with pytest.raises(ValidationError, match=field):
        Settings(**{field: value}, _env_file=None)


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


def test_explicit_deepseek_alias_is_supported_without_automatic_fallback():
    settings = Settings(
        llm_provider="litellm",
        llm_model="economicon-chat-deepseek",
        litellm_api_key="internal-gateway-key",
        _env_file=None,
    )

    assert settings.llm_model == "economicon-chat-deepseek"
