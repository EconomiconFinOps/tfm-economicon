import hashlib
import math
import json
import re

from app.clients.litellm import LiteLLMClient, ProviderError
from app.core.config import Settings


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

    def embed_batch(self, texts, **kwargs):
        if any(not isinstance(value, str) or not value.strip() for value in texts):
            raise ValueError('Embedding inputs must be nonempty text')
        return [self.embed(value) for value in texts]


class LiteLLMEmbeddingProvider:
    def __init__(self, dimension: int, settings: Settings):
        if dimension != 1536:
            raise ValueError("economicon-embedding requires dimension=1536")
        self.dimension = dimension
        self.name = "litellm"
        self.model = settings.embedding_model
        self.mapping_sha256 = getattr(settings, 'embedding_mapping_sha256', None)
        self.deployment_id = getattr(settings, 'embedding_deployment_id', None)
        self.client = LiteLLMClient(settings)
        self.usage_records = []

    def embed_batch(self, texts, *, expected_model=None, counter=None,
                    max_items=16, max_tokens=16384, max_bytes=262144):
        """Bounded batches; only an explicit expected_model requests verified identity.

        Legacy ingestion supplies no model identity. GenerationStore always supplies
        its immutable space model, which requires the complete accredited binding.
        """
        from app.embeddings.space import resolved_model_matches
        from app.embeddings.tokenization import EmbeddingTokenCounter
        if (type(max_items) is not int or not 1 <= max_items <= 32
                or type(max_tokens) is not int or not 1 <= max_tokens <= 300000
                or type(max_bytes) is not int or not 1024 <= max_bytes <= 1048576):
            raise ValueError('Invalid embedding batch limits')
        counter = counter or EmbeddingTokenCounter()
        if not isinstance(texts, list):
            raise ValueError('Embedding batch must be a list')
        groups, current, tokens = [], [], 0
        def payload(items):
            return {'model': self.model, 'input': items, 'dimensions': self.dimension, 'encoding_format': 'float'}
        def size(items):
            return len(json.dumps(payload(items), allow_nan=False).encode('utf-8'))
        for value in texts:
            if not isinstance(value, str) or not value.strip():
                raise ValueError('Embedding inputs must be nonempty text')
            count = counter.count(value)
            if count > min(8192, max_tokens) or size([value]) > max_bytes:
                raise ValueError('Single embedding input exceeds batch limits')
            if current and (len(current) >= max_items or tokens + count > max_tokens or size(current + [value]) > max_bytes):
                groups.append(current); current, tokens = [], 0
            current.append(value); tokens += count
        if current:
            groups.append(current)
        if groups and expected_model is not None and (not getattr(self, 'deployment_id', None)
                or not re.fullmatch(r'[0-9a-f]{64}', getattr(self, 'mapping_sha256', None) or '')):
            raise ValueError('Verified batches require an accredited mapping/deployment binding')
        result = []
        for group in groups:
            try:
                response, usage = self.client.post('embeddings', payload(group), with_usage=True)
            except ProviderError:
                self.usage_records.append({'cost_usd': None, 'status': 'unknown'})
                raise
            self.usage_records.append(usage)
            try:
                data = response['data']
                gateway = usage.get('gateway') or {}
                # The operator binds deployment-id to the inspected effective mapping.
                # Body.model remains untouched; an alias alone never proves identity.
                invalid_identity = expected_model is not None and (
                    gateway.get('model_id') != self.deployment_id
                    or not resolved_model_matches('openai/text-embedding-3-small', expected_model)
                    or (gateway.get('model_name') is not None
                        and gateway['model_name'] != 'openrouter/' + expected_model)
                    or not (response.get('model') == self.model
                            or resolved_model_matches(response.get('model'), expected_model)))
                if invalid_identity or not isinstance(data, list) or len(data) != len(group):
                    raise ValueError('Invalid batch response')
                indexed = {}
                for item in data:
                    index, vector = item['index'], item['embedding']
                    if (type(index) is not int or index not in range(len(group)) or index in indexed
                            or not isinstance(vector, list) or len(vector) != self.dimension
                            or not all(type(v) in {int, float} and math.isfinite(v) for v in vector)
                            or not any(float(f'{v:.6f}') != 0 for v in vector)):
                        raise ValueError('Invalid batch vector or index')
                    indexed[index] = [float(v) for v in vector]
                result.extend(indexed[index] for index in range(len(group)))
            except (KeyError, TypeError, ValueError, OverflowError):
                raise ProviderError('invalid_response') from None
        return result

    def embed(self, text: str) -> list[float]:
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
