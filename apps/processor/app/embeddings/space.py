"""Controlled embedding identities, independent of tenant and index generation."""
from dataclasses import asdict, dataclass
import hashlib
import json


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class EmbeddingSpace:
    provider: str
    model_id: str
    mapping_sha256: str
    tokenizer_id: str
    preparation: str = 'plain_v1'
    dimension: int = 1536
    distance: str = 'cosine'
    config_version: str = 'embedding_config_v1'
    query_preparation: str = 'plain_query_v1'
    context_tokens: int = 128
    max_input_tokens: int = 1024
    max_input_bytes: int = 16384
    storage_format: str = 'decimal6_v1'

    def __post_init__(self):
        if self.provider not in {'litellm', 'mock', 'bedrock'}:
            raise ValueError('Unsupported embedding provider identity')
        expected = {'litellm': 'openai/text-embedding-3-small', 'mock': 'mock/sha256_v1',
                    'bedrock': 'amazon.titan-embed-text-v2:0'}[self.provider]
        dimensions = {256,512,1024} if self.provider == 'bedrock' else {1536}
        if self.model_id != expected or type(self.dimension) is not int or self.dimension not in dimensions:
            raise ValueError('Unsupported embedding model or dimension')
        if (not isinstance(self.mapping_sha256, str) or len(self.mapping_sha256) != 64 or any(c not in '0123456789abcdef' for c in self.mapping_sha256)
                or not isinstance(self.tokenizer_id, str) or not self.tokenizer_id):
            raise ValueError('A verified mapping fingerprint and tokenizer identity are required')
        if (self.preparation not in {'plain_v1', 'contextual_embedding_v1'} or self.distance != 'cosine'
                or self.query_preparation != 'plain_query_v1' or self.config_version != 'embedding_config_v1'
                or self.storage_format != 'decimal6_v1'):
            raise ValueError('Unsupported embedding recipe')
        if (type(self.context_tokens) is not int or not 0 <= self.context_tokens <= 512
                or type(self.max_input_tokens) is not int or not 800 <= self.max_input_tokens <= 8192
                or type(self.max_input_bytes) is not int or not 4096 <= self.max_input_bytes <= 1048576):
            raise ValueError('Invalid embedding preparation limits')

    @property
    def id(self):
        return digest(self.descriptor())

    def descriptor(self):
        return asdict(self)

    @classmethod
    def from_descriptor(cls, value):
        if not isinstance(value, dict):
            raise ValueError('Invalid embedding space descriptor')
        try:
            return cls(**value)
        except TypeError:
            raise ValueError('Invalid embedding space descriptor') from None


def resolved_model_matches(actual, expected):
    # An alias alone does not attest to the resolved upstream model.
    return isinstance(actual, str) and actual in {expected, expected.removeprefix('openai/')}
