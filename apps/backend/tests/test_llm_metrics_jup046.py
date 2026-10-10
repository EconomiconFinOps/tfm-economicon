"""JUP-046: actual embedding adapter observations against the local fake gateway."""
from types import SimpleNamespace

import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram, REGISTRY, generate_latest
from pydantic import SecretStr, ValidationError
from structlog.testing import capture_logs

from app.core import llm_metrics
from app.core.config import Settings
from app.services import embedding_provider
from app.services.embedding_provider import LiteLLMEmbeddingProvider, MockEmbeddingProvider, ProviderError
from embedding_support import FakeGateway, vector_payload


VECTOR = [0.5] * 1536
PRIVATE = "jup046-private-content"


def provider_for(gateway, **kwargs):
    values = dict(
        litellm_base_url=gateway.url,
        litellm_api_key=SecretStr(PRIVATE),
        embedding_model="economicon-embedding",
        embedding_dimension=1536,
        embedding_timeout_seconds=2,
        embedding_max_retries=2,
    )
    values.update(kwargs)
    return LiteLLMEmbeddingProvider(SimpleNamespace(**values))


def count(outcome, category):
    return REGISTRY.get_sample_value("llm_provider_requests_total", {
        "operation": "embedding", "outcome": outcome, "category": category,
    }) or 0


def duration(suffix):
    return REGISTRY.get_sample_value(
        "llm_provider_request_duration_seconds_" + suffix, {"operation": "embedding"},
    ) or 0


def request_samples():
    return {tuple(sorted(sample.labels.items())): sample.value
            for metric in llm_metrics.requests_total.collect()
            for sample in metric.samples if sample.name.endswith("_total")}


@pytest.fixture(autouse=True)
def no_backoff_wait(monkeypatch):
    monkeypatch.setattr(embedding_provider, "_sleep", lambda seconds: None)


def test_success_after_retry_is_one_logical_call_including_backoff(monkeypatch):
    elapsed = [12.0]
    monkeypatch.setattr(llm_metrics, "perf_counter", lambda: elapsed[0])
    monkeypatch.setattr(embedding_provider, "_sleep", lambda seconds: elapsed.__setitem__(0, elapsed[0] + seconds))
    before = count("success", "none"), count("failure", "upstream"), duration("count"), duration("sum")
    with FakeGateway((503, {"error": PRIVATE}), (200, vector_payload(VECTOR))) as gateway:
        assert provider_for(gateway).embed(PRIVATE) == VECTOR
    assert len(gateway.requests) == 2
    assert count("success", "none") == before[0] + 1
    assert count("failure", "upstream") == before[1]
    assert duration("count") == before[2] + 1
    assert duration("sum") == pytest.approx(before[3] + .25)


@pytest.mark.parametrize("status,category,attempts", [
    (429, "rate_limit", 3), (503, "upstream", 3),
    (401, "authentication", 1), (400, "request", 1), (302, "redirect", 1),
])
def test_terminal_error_is_counted_once_after_bounded_retries(status, category, attempts):
    before = count("failure", category), count("success", "none"), duration("count")
    with FakeGateway((status, {"error": PRIVATE})) as gateway:
        with pytest.raises(ProviderError) as caught:
            provider_for(gateway).embed(PRIVATE)
    assert caught.value.category == category
    assert len(gateway.requests) == attempts
    assert count("failure", category) == before[0] + 1
    assert count("success", "none") == before[1]
    assert duration("count") == before[2] + 1


def test_vector_shape_validation_happens_before_observed_success():
    before = count("failure", "invalid_response"), count("success", "none")
    with FakeGateway((200, vector_payload([.5]))) as gateway:
        with pytest.raises(ProviderError, match="invalid_response"):
            provider_for(gateway).embed(PRIVATE)
    assert len(gateway.requests) == 1
    assert count("failure", "invalid_response") == before[0] + 1
    assert count("success", "none") == before[1]


def test_mock_and_missing_configuration_do_not_observe_provider_calls():
    before = request_samples(), duration("count")
    assert len(MockEmbeddingProvider(8).embed(PRIVATE)) == 8
    with pytest.raises(ValidationError):
        Settings(embedding_provider="litellm", embedding_dimension=1536)
    assert (request_samples(), duration("count")) == before


def test_unrelated_application_error_is_not_a_provider_failure(monkeypatch):
    # Entering a real-provider boundary may initialize zeros for future rates;
    # an application error still contributes no completed request or duration.
    completed = lambda: {labels: value for labels, value in request_samples().items() if value}
    before = completed(), duration("count")
    with FakeGateway((200, vector_payload(VECTOR))) as gateway:
        provider = provider_for(gateway)
        def application_bug(payload):
            raise RuntimeError(PRIVATE)
        monkeypatch.setattr(provider, "_attempt", application_bug)
        with pytest.raises(RuntimeError, match=PRIVATE):
            provider.embed(PRIVATE)
    assert (completed(), duration("count")) == before


def test_metrics_expose_only_fixed_labels_and_not_private_content():
    with FakeGateway((401, {"error": PRIVATE})) as gateway, capture_logs() as logs:
        with pytest.raises(ProviderError):
            provider_for(gateway).embed(PRIVATE)
    assert len(logs) == 1
    assert logs[0]["event"] == "llm_observation"
    assert logs[0]["operation"] == "embedding"
    assert logs[0]["outcome"] == "failure"
    assert logs[0]["category"] == "authentication"
    assert logs[0]["duration_ms"] >= 0
    assert PRIVATE not in repr(logs)
    for metric in llm_metrics.requests_total.collect():
        for sample in metric.samples:
            assert set(sample.labels) == {"operation", "outcome", "category"}
            assert sample.labels["operation"] == "embedding"
            assert sample.labels["category"] in llm_metrics._CATEGORIES | {"none"}
    for metric in llm_metrics.duration_seconds.collect():
        for sample in metric.samples:
            assert set(sample.labels) <= {"operation", "le"}
    text = generate_latest().decode()
    assert PRIVATE not in text
    assert gateway.url not in text
    assert "llm_provider_requests_total" in text
    assert 'llm_provider_request_duration_seconds_bucket{le="120.0",operation="embedding"}' in text


def test_unknown_failure_category_is_normalized_before_export():
    failure = ProviderError("transport")
    failure.category = PRIVATE
    before = count("failure", "transport")
    with capture_logs() as logs, pytest.raises(ProviderError):
        with llm_metrics.observe_provider_call("embedding", ProviderError):
            raise failure
    assert count("failure", "transport") == before + 1
    assert PRIVATE not in repr(logs)
    assert PRIVATE not in generate_latest().decode()


def test_success_establishes_zero_baselines_for_later_failure_categories(monkeypatch):
    registry = CollectorRegistry()
    monkeypatch.setattr(llm_metrics, "requests_total", Counter(
        "llm_provider_requests_total", "test observations",
        ["operation", "outcome", "category"], registry=registry,
    ))
    monkeypatch.setattr(llm_metrics, "duration_seconds", Histogram(
        "llm_provider_request_duration_seconds", "test durations",
        ["operation"], registry=registry,
    ))
    def sample(outcome, category):
        return registry.get_sample_value("llm_provider_requests_total", {
            "operation": "embedding", "outcome": outcome, "category": category,
        })
    assert sample("failure", "timeout") is None
    with FakeGateway((200, vector_payload(VECTOR)), (503, {})) as gateway:
        provider = provider_for(gateway)
        assert provider.embed(PRIVATE) == VECTOR
        assert sample("success", "none") == 1
        assert all(sample("failure", category) == 0 for category in llm_metrics._CATEGORIES)
        assert registry.get_sample_value("llm_provider_request_duration_seconds_count", {"operation": "embedding"}) == 1
        with pytest.raises(ProviderError, match="upstream"):
            provider.embed(PRIVATE)
    assert sample("success", "none") == 1
    assert sample("failure", "upstream") == 1
    assert all(sample("failure", category) == 0 for category in llm_metrics._CATEGORIES - {"upstream"})
    assert registry.get_sample_value("llm_provider_request_duration_seconds_count", {"operation": "embedding"}) == 2
