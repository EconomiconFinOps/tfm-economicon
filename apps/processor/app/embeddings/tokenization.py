"""Exact, offline cl100k_base accounting for the existing embedding model."""
import hashlib
from importlib.metadata import version
from pathlib import Path
import tiktoken
from tiktoken.load import load_tiktoken_bpe
from app.embeddings.tokenizer_resource import (
    ENCODING_NAME, LIBRARY_VERSION, PATTERN, RESOURCE_BYTES, RESOURCE_SHA256,
    SPECIAL_TOKENS, resource_path, assert_external_resource_path,
)


class EmbeddingTokenCounter:
    def __init__(self, path: Path | None = None):
        if version('tiktoken') != LIBRARY_VERSION:
            raise ValueError('Embedding tokenizer library version mismatch')
        path = Path(path) if path is not None else resource_path()
        assert_external_resource_path(path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size != RESOURCE_BYTES:
            raise ValueError('Prepare the pinned embedding tokenizer outside the repository before running')
        if hashlib.sha256(path.read_bytes()).hexdigest() != RESOURCE_SHA256:
            raise ValueError('Embedding tokenizer resource mismatch')
        # A filesystem path uses read_file's local branch, never an HTTP constructor.
        ranks = load_tiktoken_bpe(str(path), expected_hash=RESOURCE_SHA256)
        self.max_token_bytes = max(map(len, ranks))
        self.encoding = tiktoken.Encoding(name=ENCODING_NAME, pat_str=PATTERN,
                                         mergeable_ranks=ranks, special_tokens=SPECIAL_TOKENS)
        self.identity = f'tiktoken/{LIBRARY_VERSION}:{ENCODING_NAME}:{RESOURCE_SHA256}'

    def count(self, value: str) -> int:
        value.encode('utf-8')
        return len(self.encoding.encode_ordinary(value))
