"""JUP-022: the lifespan selects the configured embedding provider, checks the column dimension and states the configuration."""
import asyncio
import json

import pytest

from app.services.embedding_provider import LiteLLMEmbeddingProvider, MockEmbeddingProvider
from app.services.vector_store import EmbeddingDimensionMismatch
from conftest import use_gateway_embeddings
from test_secret_boundaries import main_module, resource_mocks, restore_logging  # noqa: F401


def start(main_module):
    state = {}

    async def run():
        async with main_module.app.router.lifespan_context(main_module.app):
            state["provider"] = main_module.app.state.embedding_provider

    asyncio.run(run())
    return state.get("provider")


@pytest.mark.parametrize("gateway,expected,dimension", [(False, MockEmbeddingProvider, 8), (True, LiteLLMEmbeddingProvider, 1536)])
def test_lifespan_wires_the_configured_provider_checks_the_dimension_and_logs_it(
    main_module, resource_mocks, monkeypatch, capsys, gateway, expected, dimension,
):
    if gateway:
        use_gateway_embeddings(monkeypatch)
    provider = start(main_module)
    assert type(provider) is expected and provider.dimension == dimension
    resource_mocks[2].return_value.verify_dimension.assert_called_once_with(dimension)
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    configuration = [line for line in lines if line.get("event") == "embedding_configuration"]
    assert len(configuration) == 1 and configuration[0]["embedding_dimension"] == dimension


def test_a_dimension_mismatch_stops_the_lifespan_with_the_fixed_message(main_module, resource_mocks):
    resource_mocks[2].return_value.verify_dimension.side_effect = EmbeddingDimensionMismatch()
    with pytest.raises(EmbeddingDimensionMismatch, match="re-index"):
        start(main_module)
