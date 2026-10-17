"""JSON-native deterministic chunk contracts; operational timestamps are separate."""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import NotRequired, TypedDict

CHUNKING_STRATEGY = 'structural_recursive'
CHUNKING_VERSION = '1.0.1'
POSITION_CONTRACT = {
    'normalized_text': 'unicode_codepoints:0-based:end-exclusive',
    'original_lines': '1-based:inclusive',
    'original_pages': '1-based',
    'table_rows_and_columns': '0-based:end-exclusive',
    'fragments': '1-based',
    'chunk_index': '0-based',
    'original_coordinates': 'only the extractor-declared coordinate_system; never converted implicitly',
}


def fingerprint(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class ChunkingConfig:
    target_tokens: int = 600
    max_tokens: int = 800
    overlap_ratio: float = 0.10

    def __post_init__(self):
        if (type(self.target_tokens) is not int or type(self.max_tokens) is not int
                or not 8 <= self.target_tokens <= self.max_tokens <= 800
                or isinstance(self.overlap_ratio, bool)
                or not isinstance(self.overlap_ratio, (int, float))
                or not math.isfinite(self.overlap_ratio) or not 0 <= self.overlap_ratio < 1):
            raise ValueError('Invalid chunking configuration')

    @property
    def overlap_tokens(self) -> int:
        return math.floor(self.target_tokens * self.overlap_ratio)

    def identity(self) -> dict:
        return {**asdict(self), 'overlap_ratio': float(self.overlap_ratio)}


class OriginalLocation(TypedDict, total=False):
    page: int
    source_lines: list[int]
    bbox: list[float]
    coordinate_system: str
    method: str
    row_range: list[int]
    column_range: list[int]


class SourceSpan(TypedDict):
    normalized_range: list[int]
    block_ref: str | None
    original: OriginalLocation
    section_path: list[str]
    heading_level: int | None
    content_type: NotRequired[str]
    language: NotRequired[str | None]
    list_depth: NotRequired[int | None]
    parent_normalized_range: NotRequired[list[int] | None]
    parent_block_ref: NotRequired[str | None]


class ContentSpan(TypedDict):
    normalized_range: list[int]
    content_range: list[int]


class Repetition(ContentSpan):
    reason: str
    token_count: int


class Fragment(TypedDict):
    fragment_group_id: str
    fragment_index: int
    fragment_count: int
    split_reason: str
    block_ref: str | None
    unit_range: list[int]


class OmittedText(TypedDict):
    normalized_range: list[int]
    text: str


class ReconstructionMetadata(TypedDict):
    schema_version: int
    document_characters: int
    document_text_sha256: str
    chunk_count: int
    omitted_spans: list[OmittedText]


class ChunkMetadata(TypedDict):
    content_type: str
    token_count: int
    chunk_hash: str
    chunking_strategy: str
    chunking_version: str
    chunking_fingerprint: str
    tokenizer_id: str
    configuration_fingerprint: str
    source_spans: list[SourceSpan]
    reconstruction: NotRequired[ReconstructionMetadata]
    primary_spans: list[ContentSpan]
    repetitions: list[Repetition]
    fragments: list[Fragment]
    warnings: list[str]
    section_path: NotRequired[list[str] | None]
    heading_level: NotRequired[int | None]


class DocumentChunk(TypedDict):
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: ChunkMetadata


def document_identity(document: dict) -> dict:
    """Only data that can affect cuts or their provenance, never upload timestamps."""
    if (not isinstance(document, dict) or type(document.get('schema_version')) is not int or document.get('schema_version') != 1
            or not isinstance(document.get('document_id'), str) or not document['document_id']
            or not isinstance(document.get('tenant_id'), str) or not document['tenant_id']
            or not isinstance(document.get('text'), str) or not isinstance(document.get('blocks', []), list)):
        raise ValueError('Invalid normalized document')
    document['text'].encode('utf-8')
    return {key: document.get(key, default) for key, default in (
        ('schema_version', 1), ('document_id', None), ('tenant_id', None),
        ('original_format', 'manual-text'), ('text', ''), ('blocks', []),
        ('extraction_method', None), ('file_metadata', {}))}


def generation_identity(document: dict, config: ChunkingConfig, tokenizer_id: str) -> dict:
    if not isinstance(tokenizer_id, str) or not tokenizer_id.strip():
        raise ValueError('Tokenizer identity is required')
    return {
        'chunking_strategy': CHUNKING_STRATEGY, 'chunking_version': CHUNKING_VERSION,
        'configuration': config.identity(), 'tokenizer_id': tokenizer_id,
        'input_fingerprint': fingerprint(document_identity(document)),
    }


def chunk_identity(document_id: str, generation: str, index: int) -> str:
    if (not isinstance(document_id, str) or not document_id or type(index) is not int or index < 0
            or not isinstance(generation, str) or len(generation) != 64
            or any(value not in '0123456789abcdef' for value in generation)):
        raise ValueError('Invalid chunk identity')
    return f'{document_id}:chunk:{generation}:{index}'
