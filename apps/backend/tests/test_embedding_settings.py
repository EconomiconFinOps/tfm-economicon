"""JUP-022: backend settings for the query embedding provider and the retrieval parameters."""
import json
import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.runtime_secrets import StartupError

SENTINEL = "sk-backend-sentinel-0123456789"


def make(monkeypatch, **env):
    for name, value in env.items():
        monkeypatch.setenv(name.upper(), str(value))
    return Settings(_env_file=None)


def litellm(**extra):
    return {"embedding_provider": "litellm", "embedding_dimension": 1536, "litellm_api_key": SENTINEL, **extra}


def test_defaults_keep_the_current_behaviour(monkeypatch):
    settings = make(monkeypatch)
    assert settings.embedding_provider == "mock"
    assert settings.embedding_dimension == 8
    assert settings.embedding_model == "economicon-embedding"
    assert settings.retrieval_top_k == 4
    assert settings.retrieval_max_distance is None
    assert settings.litellm_api_key is None


def test_litellm_with_key_is_accepted_and_the_key_is_secret(monkeypatch):
    settings = make(monkeypatch, **litellm())
    assert settings.embedding_provider == "litellm"
    assert settings.litellm_api_key.get_secret_value() == SENTINEL
    assert SENTINEL not in repr(settings) and SENTINEL not in str(settings)


@pytest.mark.parametrize("key", [None, "", "   "])
def test_litellm_without_a_usable_key_is_rejected_naming_the_setting(monkeypatch, key):
    env = litellm()
    env.pop("litellm_api_key")
    if key is not None:
        env["litellm_api_key"] = key
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, **env)
    assert "litellm_api_key" in str(error.value)


@pytest.mark.parametrize("key", ["sk-or-v1-upstream", "line\nbreak"])
def test_the_key_must_be_a_single_line_gateway_credential(monkeypatch, key):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, **litellm(litellm_api_key=key))
    assert "litellm_api_key" in str(error.value)
    assert key.strip() not in str(error.value)


@pytest.mark.parametrize("environment", ["production"])
def test_mock_is_rejected_outside_development_and_test(monkeypatch, environment):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, runtime_environment=environment, embedding_provider="mock")
    assert "embedding_provider" in str(error.value)


@pytest.mark.parametrize("environment", ["development", "test"])
def test_mock_is_accepted_in_development_and_test(monkeypatch, environment):
    assert make(monkeypatch, runtime_environment=environment).embedding_provider == "mock"


def test_litellm_is_accepted_in_production(monkeypatch):
    assert make(monkeypatch, runtime_environment="production", **litellm()).embedding_provider == "litellm"


@pytest.mark.parametrize("value", ["openai", "", "MOCKS"])
def test_unknown_provider_is_rejected(monkeypatch, value):
    with pytest.raises(ValidationError):
        make(monkeypatch, embedding_provider=value)


def test_provider_is_case_insensitive_and_trimmed(monkeypatch):
    assert make(monkeypatch, **litellm(embedding_provider=" LiteLLM ")).embedding_provider == "litellm"


def test_litellm_requires_the_dimension_of_the_ingestion_model(monkeypatch):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, **litellm(embedding_dimension=8))
    assert "embedding_dimension" in str(error.value)


@pytest.mark.parametrize("alias", ["", "has space", "../x", "a" * 129])
def test_alias_must_be_a_logical_model_alias(monkeypatch, alias):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, embedding_model=alias)
    assert "embedding_model" in str(error.value)


@pytest.mark.parametrize("url", [
    "ftp://litellm:4000/v1", "litellm:4000", "http://user:pass@litellm:4000/v1",
    "http://litellm:4000/v1?x=1", "http://litellm:4000/v1#frag", "http://litellm:99999/v1",
])
def test_gateway_url_must_be_a_plain_http_url(monkeypatch, url):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, **litellm(litellm_base_url=url))
    assert "litellm_base_url" in str(error.value)


def test_gateway_url_is_normalized_without_trailing_slash(monkeypatch):
    assert make(monkeypatch, **litellm(litellm_base_url="http://litellm:4000/v1/")).litellm_base_url == "http://litellm:4000/v1"


@pytest.mark.parametrize("value", [0, -1, 300.5, "nan", "inf"])
def test_timeout_must_be_positive_and_bounded(monkeypatch, value):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, embedding_timeout_seconds=value)
    assert "embedding_timeout_seconds" in str(error.value)


@pytest.mark.parametrize("value", [-1, 11])
def test_retries_are_bounded(monkeypatch, value):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, embedding_max_retries=value)
    assert "embedding_max_retries" in str(error.value)


@pytest.mark.parametrize("value", [1, 4, 20])
def test_top_k_inside_the_range_is_accepted(monkeypatch, value):
    assert make(monkeypatch, retrieval_top_k=value).retrieval_top_k == value


@pytest.mark.parametrize("value", [0, -1, 21, "2.5", "abc"])
def test_top_k_outside_the_range_is_rejected(monkeypatch, value):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, retrieval_top_k=value)
    assert "retrieval_top_k" in str(error.value)


@pytest.mark.parametrize("value,expected", [("0.5", 0.5), ("2", 2.0), ("0.0001", 0.0001)])
def test_max_distance_inside_the_range_is_accepted(monkeypatch, value, expected):
    assert make(monkeypatch, retrieval_max_distance=value).retrieval_max_distance == expected


@pytest.mark.parametrize("value", ["0", "-0.1", "2.0001", "nan", "inf", "-inf", "abc"])
def test_max_distance_outside_the_range_is_rejected(monkeypatch, value):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, retrieval_max_distance=value)
    assert "retrieval_max_distance" in str(error.value)


def test_unset_or_empty_max_distance_uses_the_calibrated_default_of_the_provider(monkeypatch):
    assert make(monkeypatch).retrieval_max_distance is None
    assert make(monkeypatch, retrieval_max_distance="").retrieval_max_distance is None
    assert make(monkeypatch, **litellm()).retrieval_max_distance == 0.6
    monkeypatch.setenv("RETRIEVAL_MAX_DISTANCE", " ")
    assert Settings(_env_file=None).retrieval_max_distance == 0.6


@pytest.mark.parametrize("word", ["none", "NONE", " off "])
def test_explicit_none_disables_the_threshold_for_every_provider(monkeypatch, word):
    assert make(monkeypatch, retrieval_max_distance=word).retrieval_max_distance is None
    assert make(monkeypatch, **litellm(retrieval_max_distance=word)).retrieval_max_distance is None


def test_explicit_value_overrides_the_provider_default(monkeypatch):
    assert make(monkeypatch, **litellm(retrieval_max_distance="0.45")).retrieval_max_distance == 0.45
    assert make(monkeypatch, retrieval_max_distance="0.9").retrieval_max_distance == 0.9


def test_invalid_configuration_surfaces_only_a_fixed_message_without_the_key(monkeypatch):
    for name, value in {"EMBEDDING_PROVIDER": "litellm", "EMBEDDING_DIMENSION": "8",
                        "LITELLM_API_KEY": SENTINEL}.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(StartupError) as error:
        get_settings()
    assert SENTINEL not in str(error.value) and SENTINEL not in repr(error.value)


def test_the_key_is_registered_for_redaction(monkeypatch):
    from app.core.runtime_secrets import redact

    for name, value in {"EMBEDDING_PROVIDER": "litellm", "EMBEDDING_DIMENSION": "1536",
                        "LITELLM_API_KEY": SENTINEL}.items():
        monkeypatch.setenv(name, value)
    get_settings()
    assert SENTINEL not in redact(f"upstream said {SENTINEL}")


def test_validation_errors_never_echo_the_key(monkeypatch):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, **litellm(embedding_dimension=8))
    assert SENTINEL not in str(error.value) and SENTINEL not in repr(error.value)


@pytest.mark.parametrize("provider,extra,dimension", [
    ("mock", {}, 8),
    ("litellm", {"LITELLM_API_KEY": SENTINEL}, 1536),
])
def test_startup_logs_one_line_with_provider_alias_and_dimension(monkeypatch, capsys, provider, extra, dimension):
    from app.core.embedding_startup import log_embedding_configuration
    from app.core.logging import configure_logging

    monkeypatch.setenv("EMBEDDING_PROVIDER", provider)
    monkeypatch.setenv("EMBEDDING_DIMENSION", str(dimension))
    for name, value in extra.items():
        monkeypatch.setenv(name, value)
    settings = Settings(_env_file=None)
    configure_logging()
    capsys.readouterr()
    log_embedding_configuration(settings)
    output = capsys.readouterr().out
    lines = [json.loads(line) for line in output.splitlines() if line.strip()]
    assert len(lines) == 1
    assert lines[0]["embedding_provider"] == provider
    assert lines[0]["embedding_model"] == "economicon-embedding"
    assert lines[0]["embedding_dimension"] == dimension
    assert SENTINEL not in output and SENTINEL[:8] not in output
    logging.getLogger().handlers.clear()


# Hardening after the adversarial review.

@pytest.mark.parametrize("key", ["changeme", "CHANGEME", "replace-me", "password", " secret "])
def test_known_placeholder_keys_are_rejected_outside_the_test_environment(monkeypatch, key):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, runtime_environment="production", **litellm(litellm_api_key=key))
    assert "litellm_api_key" in str(error.value)
    assert key.strip() not in str(error.value)


@pytest.mark.parametrize("value", ["true", "True", "4.0", "1e1", "+3", "-1", "٤", "4 5", "0x4"])
def test_top_k_rejects_booleans_decimals_and_unicode_digits(monkeypatch, value):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, retrieval_top_k=value)
    assert "retrieval_top_k" in str(error.value)


@pytest.mark.parametrize("value,expected", [("4", 4), (" 5 ", 5), ("20", 20)])
def test_top_k_accepts_plain_ascii_integers(monkeypatch, value, expected):
    assert make(monkeypatch, retrieval_top_k=value).retrieval_top_k == expected


@pytest.mark.parametrize("value", ["٠.٥", "1e-3", "5e-1", "0x1", "1_0", "+0.5", "0.5.5", "--1"])
def test_max_distance_rejects_unicode_digits_exponents_and_odd_notations(monkeypatch, value):
    with pytest.raises(ValidationError) as error:
        make(monkeypatch, retrieval_max_distance=value)
    assert "retrieval_max_distance" in str(error.value)


@pytest.mark.parametrize("value,expected", [(".5", 0.5), ("0.5", 0.5), ("2", 2.0), ("1.25", 1.25)])
def test_max_distance_accepts_plain_ascii_decimals(monkeypatch, value, expected):
    assert make(monkeypatch, retrieval_max_distance=value).retrieval_max_distance == expected


# Review of PR 67: interactive worst case and startup messages that name the rejected settings.

def test_defaults_fit_an_interactive_route():
    settings = make_default()
    assert settings.embedding_timeout_seconds == 10.0 and settings.embedding_max_retries == 1
    assert (settings.embedding_max_retries + 1) * settings.embedding_timeout_seconds <= 20


def make_default():
    return Settings(_env_file=None)


@pytest.mark.parametrize("timeout,retries", [(30, 1), (60, 0), (20, 2), (10, 5), (6, 9)])
def test_the_worst_case_of_one_question_may_not_exceed_a_minute(monkeypatch, timeout, retries):
    monkeypatch.setenv("EMBEDDING_TIMEOUT_SECONDS", str(timeout))
    monkeypatch.setenv("EMBEDDING_MAX_RETRIES", str(retries))
    assert Settings(_env_file=None).embedding_timeout_seconds == timeout


@pytest.mark.parametrize("timeout,retries", [(30, 2), (60.5, 0), (21, 2), (10, 6), (300, 0)])
def test_a_combination_above_a_minute_is_rejected_naming_both_settings(monkeypatch, timeout, retries):
    monkeypatch.setenv("EMBEDDING_TIMEOUT_SECONDS", str(timeout))
    monkeypatch.setenv("EMBEDDING_MAX_RETRIES", str(retries))
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)
    assert "embedding_timeout_seconds" in str(error.value) and "embedding_max_retries" in str(error.value)


STARTUP_CASES = [
    ({"RUNTIME_ENVIRONMENT": "production"}, "embedding_provider"),
    ({"EMBEDDING_PROVIDER": "litellm", "EMBEDDING_DIMENSION": "1536"}, "litellm_api_key"),
    ({"EMBEDDING_PROVIDER": "litellm", "EMBEDDING_DIMENSION": "8", "LITELLM_API_KEY": SENTINEL}, "embedding_dimension"),
    ({"RETRIEVAL_TOP_K": "0"}, "retrieval_top_k"),
    ({"RETRIEVAL_MAX_DISTANCE": "3"}, "retrieval_max_distance"),
    ({"EMBEDDING_TIMEOUT_SECONDS": "300", "EMBEDDING_MAX_RETRIES": "0"}, "embedding_timeout_seconds"),
    ({"EMBEDDING_TIMEOUT_SECONDS": "abc"}, "embedding_timeout_seconds"),  # native type error: only the location names it
    ({"EMBEDDING_MAX_RETRIES": "x"}, "embedding_max_retries"),
]


@pytest.mark.parametrize("env,name", STARTUP_CASES)
def test_the_real_startup_names_the_rejected_setting_and_never_a_value(monkeypatch, env, name):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(StartupError) as error:
        get_settings()
    message = str(error.value)
    assert name in message
    assert SENTINEL not in message and SENTINEL not in repr(error.value)
    assert "Invalid runtime configuration" in message


def test_a_rejected_secret_setting_is_named_without_its_value(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "litellm")
    monkeypatch.setenv("EMBEDDING_DIMENSION", "1536")
    monkeypatch.setenv("LITELLM_API_KEY", "sk-or-v1-" + SENTINEL)
    with pytest.raises(StartupError) as error:
        get_settings()
    assert "litellm_api_key" in str(error.value)
    assert SENTINEL not in str(error.value) and "sk-or" not in str(error.value)


def test_errors_outside_the_embedding_settings_keep_the_generic_message(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "not-json")
    with pytest.raises(StartupError) as error:
        get_settings()
    assert str(error.value) == "Invalid runtime configuration; check required credentials and settings."
