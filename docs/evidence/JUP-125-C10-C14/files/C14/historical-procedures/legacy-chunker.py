class TextChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        step = self.chunk_size - self.chunk_overlap

        while start < len(normalized):
            end = min(len(normalized), start + self.chunk_size)
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(normalized):
                break
            start += step

        return chunks
