import hashlib
import math

from app.clients.litellm import LiteLLMClient, ProviderError
from app.core.config import Settings
from app.core.llm_metrics import observe_provider_call


class MockEmbeddingProvider:
    def __init__(self, dimension: int):
        if dimension <= 0:
            raise ValueError("dimension must be greater than zero")
        self.dimension = dimension
        self.name = "mock"

    def embed(self, text: str) -> list[float]:
        vector: list[float] = []
        for index in range(self.dimension):
            digest = hashlib.sha256(f"{index}:{text}".encode("utf-8")).digest()
            raw_value = int.from_bytes(digest[:8], byteorder="big", signed=False)
            normalized = (raw_value / ((1 << 64) - 1)) * 2 - 1
            vector.append(round(normalized, 6))
        return vector


class LiteLLMEmbeddingProvider:
    def __init__(self, dimension: int, settings: Settings):
        if dimension != 1536:
            raise ValueError("economicon-embedding requires dimension=1536")
        self.dimension = dimension
        self.name = "litellm"
        self.model = settings.embedding_model
        self.client = LiteLLMClient(settings)

    def embed(self, text: str) -> list[float]:
        with observe_provider_call("embedding", ProviderError):
            return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        payload = self.client.post("embeddings", {
            "model": self.model, "input": text, "dimensions": self.dimension,
        })
        try:
            data = payload["data"]
            vector = data[0]["embedding"]
            if (
                isinstance(data, list) and len(data) == 1
                and isinstance(vector, list) and len(vector) == self.dimension
                and all(type(value) in {int, float} and math.isfinite(value) for value in vector)
            ):
                return [float(value) for value in vector]
        except (KeyError, IndexError, TypeError, OverflowError):
            pass
        raise ProviderError("invalid_response")


def get_embedding_provider(provider_name: str, dimension: int, settings: Settings | None = None):
    if provider_name == "mock":
        return MockEmbeddingProvider(dimension)
    if provider_name == "litellm":
        if settings is None:
            raise ValueError("LiteLLM requires explicit settings")
        return LiteLLMEmbeddingProvider(dimension, settings)
    raise ValueError(f"Unsupported embedding provider: {provider_name}")
