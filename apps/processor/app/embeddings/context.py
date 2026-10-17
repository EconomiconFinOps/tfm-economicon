"""Deterministic embedding-only context; canonical chunk evidence stays untouched."""
from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class PreparedEmbedding:
    text: str
    text_hash: str
    token_count: int
    preparation: str
    warnings: tuple[str, ...] = ()


def _field(value, warnings):
    normalized = ' '.join(value.split()) if isinstance(value, str) else ''
    if len(normalized) > 512:
        warnings.add('embedding_context_truncated')
    return normalized[:512]


def _common_path(metadata, warnings):
    spans = metadata.get('source_spans', [])
    if not spans:
        return []
    paths = [span.get('section_path') for span in spans]
    if any(not isinstance(path, list) or not path
           or any(not isinstance(p, str) or not p.strip() for p in path) for path in paths):
        return []
    # Establish the accredited common path before shortening any field: two
    # different long headings must not become equal just because their caps match.
    common = [' '.join(p.split()) for p in paths[0]]
    for path in paths[1:]:
        other = [' '.join(p.split()) for p in path]
        common = common[:next((i for i, (a, b) in enumerate(zip(common, other)) if a != b), min(len(common), len(other)))]
    return [_field(p, warnings) for p in common]


def prepare_embedding(chunk, parent_metadata, space, counter):
    content = chunk['content']
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Embedding content must be nonempty text')
    if counter.identity != space.tokenizer_id:
        raise ValueError('Embedding tokenizer identity mismatch')
    if len(content.encode('utf-8')) > space.max_input_bytes or counter.count(content) > space.max_input_tokens:
        raise ValueError('Chunk content exceeds the embedding recipe; content was not truncated')
    fields, warnings = [], set()
    if space.preparation == 'contextual_embedding_v1':
        title = _field(parent_metadata.get('title'), warnings)
        path = _common_path(chunk.get('metadata', {}), warnings)
        kind = chunk.get('metadata', {}).get('content_type')
        if title:
            fields.append('Documento: ' + title)
        if path:
            fields.append('Sección: ' + ' > '.join(path))
        if kind in {'table', 'code'}:
            fields.append('Tipo: ' + kind)
    while fields:
        prefix = '\n'.join(fields)
        prepared = prefix + '\n\n' + content
        if (counter.count(prefix) <= space.context_tokens and counter.count(prepared) <= space.max_input_tokens
                and len(prepared.encode('utf-8')) <= space.max_input_bytes):
            break
        warnings.add('embedding_context_truncated')
        # Drop lower priority fields first; truncate only the bounded title.
        if len(fields) > 1:
            fields.pop()
        elif len(fields[0]) > len('Documento: ') + 1 and fields[0].startswith('Documento: '):
            fields[0] = fields[0][:-1].rstrip()
        else:
            fields.clear()
    text = '\n'.join(fields) + '\n\n' + content if fields else content
    return PreparedEmbedding(text, hashlib.sha256(text.encode('utf-8')).hexdigest(), counter.count(text),
                             space.preparation, tuple(sorted(warnings)))
