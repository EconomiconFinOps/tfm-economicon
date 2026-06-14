import hashlib


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


def get_embedding_provider(provider_name: str, dimension: int):
    if provider_name == "mock":
        return MockEmbeddingProvider(dimension)
    raise ValueError(f"Unsupported embedding provider: {provider_name}")
