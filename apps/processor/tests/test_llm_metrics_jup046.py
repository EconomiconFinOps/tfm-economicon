"""Offline gateway transport: no LLM, secrets or notification receivers."""

import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from pydantic import ValidationError

from app.agents.providers import MockLLMProvider
from app.agents.service import AgentRuntime
from app.clients.litellm import ProviderError
from app.core import llm_metrics as metrics
from app.core.config import Settings
from app.embeddings.providers import LiteLLMEmbeddingProvider, MockEmbeddingProvider


JOB = {"tenant_id": "tenant-sentinel", "source": "azure", "metadata": {}}


@pytest.fixture
def registry(monkeypatch):
    registry = CollectorRegistry()
    monkeypatch.setattr(metrics, "requests_total", Counter(
        "llm_provider_requests_total", "test", ["operation", "outcome", "category"],
        registry=registry,
    ))
    monkeypatch.setattr(metrics, "duration_seconds", Histogram(
        "llm_provider_request_duration_seconds", "test", ["operation"],
        buckets=(.1, .25, .5, 1, 2, 5, 10, 20, 30, 60, 120), registry=registry,
    ))
    return registry


def count(registry, operation, outcome, category):
    return registry.get_sample_value("llm_provider_requests_total", {
        "operation": operation, "outcome": outcome, "category": category,
    }) or 0


def run_generation(settings):
    return AgentRuntime(settings).invoke(JOB, "running")


def generation_response(content=None):
    if content is None:
        content = MockLLMProvider().invoke("ignored", response_format={})
    return {"choices": [{"message": {"content": content}}]}


def test_retried_generation_records_one_completion_with_total_latency(
    registry, litellm_settings, gateway_transport, monkeypatch,
):
    gateway_transport.responses = [(503, {}, {}), (200, generation_response(), {})]
    ticks = iter([10, 30.5])
    monkeypatch.setattr(metrics, "perf_counter", lambda: next(ticks))
    result = run_generation(litellm_settings)
    assert result["response"]["status"] == "insufficient_data"
    assert len(gateway_transport.calls) == 2
    assert count(registry, "generation", "success", "none") == 1
    assert count(registry, "generation", "failure", "upstream") == 0
    labels = {"operation": "generation"}
    assert registry.get_sample_value("llm_provider_request_duration_seconds_count", labels) == 1
    assert registry.get_sample_value("llm_provider_request_duration_seconds_sum", labels) == 20.5


@pytest.mark.parametrize("status,category,attempts", [
    (401, "authentication", 1), (403, "authentication", 1),
    (429, "rate_limit", 3), (503, "upstream", 3), (400, "request", 1),
])
def test_terminal_failure_is_counted_once(
    registry, litellm_settings, gateway_transport, status, category, attempts,
):
    gateway_transport.responses = [(status, {"secret": "response-sentinel"}, {})] * attempts
    with pytest.raises(ProviderError, match=category):
        run_generation(litellm_settings)
    assert len(gateway_transport.calls) == attempts
    assert count(registry, "generation", "failure", category) == 1
    assert count(registry, "generation", "success", "none") == 0


@pytest.mark.parametrize("body", [{}, {"choices": []}, generation_response("not-json"),
                                      generation_response('{"schema_version":"99"}')])
def test_transport_and_finops_shape_failures_are_observed(
    registry, litellm_settings, gateway_transport, body,
):
    gateway_transport.responses = [(200, body, {})]
    with pytest.raises(ProviderError, match="invalid_response"):
        run_generation(litellm_settings)
    assert count(registry, "generation", "failure", "invalid_response") == 1
    assert count(registry, "generation", "success", "none") == 0


@pytest.mark.parametrize("failure,category", [
    (TimeoutError("private-url-sentinel"), "timeout"),
    (ConnectionRefusedError("private-url-sentinel"), "connection"),
])
def test_network_failures_keep_bounded_categories(
    registry, litellm_settings, gateway_transport, failure, category,
):
    gateway_transport.responses = [failure] * 3
    with pytest.raises(ProviderError, match=category):
        run_generation(litellm_settings)
    assert count(registry, "generation", "failure", category) == 1
    exposition = generate_latest(registry).decode()
    assert "private-url-sentinel" not in exposition


def test_embedding_validation_recovery_and_privacy(registry, litellm_settings, gateway_transport):
    gateway_transport.responses = [
        (200, {"data": [{"embedding": [0.1]}]}, {}),
        (200, {"data": [{"embedding": [0.1] * 1536}]}, {}),
    ]
    provider = LiteLLMEmbeddingProvider(1536, litellm_settings)
    with pytest.raises(ProviderError, match="invalid_response"):
        provider.embed("prompt-sentinel")
    assert provider.embed("prompt-sentinel") == [0.1] * 1536
    assert count(registry, "embedding", "failure", "invalid_response") == 1
    assert count(registry, "embedding", "success", "none") == 1
    exposition = generate_latest(registry).decode()
    for forbidden in ("prompt-sentinel", "tenant-sentinel", "synthetic-virtual-key", "gateway.invalid"):
        assert forbidden not in exposition
    for sample in metrics.requests_total.collect()[0].samples:
        assert set(sample.labels) == {"operation", "outcome", "category"}


def test_mock_missing_configuration_and_unsupported_source_are_not_degradation(
    registry, litellm_settings, gateway_transport,
):
    run_generation(Settings(llm_provider="mock"))
    MockEmbeddingProvider(3).embed("ignored")
    with pytest.raises(ValidationError):
        Settings(llm_provider="litellm", litellm_api_key=None)
    result = AgentRuntime(litellm_settings).invoke({**JOB, "source": "aws"}, "running")
    assert result["response"]["status"] == "unsupported"
    assert gateway_transport.calls == []
    assert metrics.requests_total.collect()[0].samples == []


def test_observation_logs_use_existing_context_without_provider_content(
    registry, litellm_settings, gateway_transport, monkeypatch,
):
    entries = []
    class Recorder:
        def info(self, event, **kwargs):
            entries.append((event, kwargs))
    monkeypatch.setattr(metrics, "logger", Recorder())
    gateway_transport.responses = [(200, generation_response("secret-response-sentinel"), {})]
    with pytest.raises(ProviderError):
        run_generation(litellm_settings)
    assert len(entries) == 1
    assert entries[0][0] == "llm_observation"
    assert entries[0][1]["category"] == "invalid_response"
    assert set(entries[0][1]) == {"operation", "outcome", "category", "duration_ms"}
    assert "secret-response-sentinel" not in repr(entries)


def test_unrelated_application_exception_is_not_a_provider_outcome(registry):
    with pytest.raises(TypeError):
        with metrics.observe_provider_call("generation", ProviderError):
            raise TypeError("internal bug")
    assert all(sample.value == 0 for sample in metrics.requests_total.collect()[0].samples
               if sample.name.endswith("_total"))


def test_success_initializes_zero_baseline_for_every_failure_category(
    registry, litellm_settings, gateway_transport,
):
    gateway_transport.responses = [(200, generation_response(), {})]
    run_generation(litellm_settings)
    for category in metrics._CATEGORIES:
        assert registry.get_sample_value("llm_provider_requests_total", {
            "operation": "generation", "outcome": "failure", "category": category,
        }) == 0
    gateway_transport.responses = [(503, {}, {})] * 3
    with pytest.raises(ProviderError):
        run_generation(litellm_settings)
    assert count(registry, "generation", "failure", "upstream") == 1
    assert count(registry, "generation", "success", "none") == 1


def test_observations_are_visible_on_existing_metrics_endpoint(litellm_settings, gateway_transport):
    from app.core.metrics import get_metrics

    gateway_transport.responses = [(200, generation_response(), {})]
    run_generation(litellm_settings)
    body = get_metrics().body.decode()
    assert 'llm_provider_requests_total{category="none",operation="generation",outcome="success"}' in body
    assert 'llm_provider_request_duration_seconds_count{operation="generation"}' in body
