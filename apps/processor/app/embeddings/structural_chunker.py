"""Lossless primary spans, bounded token chunks and explicit structural repetition."""
from dataclasses import dataclass, field, replace
from bisect import bisect_right
import hashlib
import re
from app.embeddings.contracts import (
    CHUNKING_STRATEGY, CHUNKING_VERSION, POSITION_CONTRACT,
    ChunkingConfig, chunk_identity, fingerprint, generation_identity,
)
from app.embeddings.structure import structure
from app.embeddings.tokenization import EmbeddingTokenCounter


def reconstruct_normalized_text(chunks):
    """Recover exact normalized text using only a complete chunk set and its metadata."""
    try:
        if not chunks:
            raise ValueError('No chunks: document completeness cannot be established')
        if any(type(chunk['chunk_index']) is not int for chunk in chunks):
            raise ValueError('Invalid chunk order')
        ordered = sorted(chunks, key=lambda chunk:chunk['chunk_index'])
        descriptor = ordered[0]['metadata'].get('reconstruction')
        if not descriptor or type(descriptor.get('schema_version')) is not int or descriptor.get('schema_version') != 1:
            raise ValueError('Exact reconstruction metadata is unavailable')
        count, length = descriptor['chunk_count'], descriptor['document_characters']
        if type(count) is not int or type(length) is not int or count < 1 or length < 1 or count != len(ordered):
            raise ValueError('Incomplete chunk set or invalid reconstruction size')
        document_id = ordered[0]['document_id']
        generation = ordered[0]['metadata']['chunking_fingerprint']
        primary, repetitions, fragments = [], [], {}
        for number, chunk in enumerate(ordered):
            metadata, content = chunk['metadata'], chunk['content']
            if (chunk['chunk_index'] != number or chunk['document_id'] != document_id
                    or metadata['chunking_fingerprint'] != generation
                    or chunk['chunk_id'] != chunk_identity(document_id,generation,number)
                    or (number and 'reconstruction' in metadata)
                    or metadata['chunk_hash'] != hashlib.sha256(content.encode('utf-8')).hexdigest()):
                raise ValueError('Mixed, missing, duplicated or corrupt chunk')
            output = []
            for key in ('primary_spans','repetitions'):
                for span in metadata[key]:
                    start,end = span['normalized_range']; left,right = span['content_range']
                    if (any(type(value) is not int for value in (start,end,left,right))
                            or not 0 <= start < end <= length or not 0 <= left < right <= len(content)
                            or end-start != right-left):
                        raise ValueError('Invalid reconstruction span')
                    value = content[left:right]
                    output.append((left,right))
                    (primary if key == 'primary_spans' else repetitions).append((start,end,value))
            cursor = 0
            for left,right in sorted(output):
                if left != cursor:
                    raise ValueError('Untracked or duplicated chunk substring')
                cursor = right
            if cursor != len(content):
                raise ValueError('Untracked chunk suffix')
            for fragment in metadata['fragments']:
                group = fragment['fragment_group_id']
                signature = (fragment['fragment_count'],tuple(fragment['unit_range']),fragment['block_ref'])
                bounds = fragment['unit_range']
                if (len(bounds) != 2 or any(type(value) is not int for value in bounds)
                        or not 0 <= bounds[0] < bounds[1] <= length):
                    raise ValueError('Invalid structural fragment range')
                index = fragment['fragment_index']
                if (type(signature[0]) is not int or signature[0] < 1 or type(index) is not int
                        or not 1 <= index <= signature[0]):
                    raise ValueError('Invalid fragment sequence')
                previous, indices = fragments.setdefault(group,(signature,set()))
                if previous != signature or index in indices:
                    raise ValueError('Incoherent or duplicated fragment metadata')
                indices.add(index)
        for (count, _, _), indices in fragments.values():
            if len(indices) != count:
                raise ValueError('Incomplete structural fragment group')
        for span in descriptor['omitted_spans']:
            start,end = span['normalized_range']; value = span['text']
            if (type(start) is not int or type(end) is not int or not isinstance(value,str)
                    or not 0 <= start < end <= length or len(value) != end-start or value.strip()):
                raise ValueError('Invalid preserved whitespace metadata')
            primary.append((start,end,value))
        cursor, values = 0, []
        for start,end,value in sorted(primary):
            if start != cursor:
                raise ValueError('Normalized content is missing or duplicated')
            values.append(value); cursor = end
        if cursor != length:
            raise ValueError('Normalized document suffix is missing')
        reconstructed = ''.join(values)
        if hashlib.sha256(reconstructed.encode('utf-8')).hexdigest() != descriptor['document_text_sha256']:
            raise ValueError('Reconstructed normalized document hash mismatch')
        if any(reconstructed[start:end] != value for start,end,value in repetitions):
            raise ValueError('Repeated context does not match its normalized source')
        return reconstructed
    except (KeyError,TypeError,IndexError,AttributeError,UnicodeError) as error:
        raise ValueError('Invalid or unavailable chunk reconstruction metadata') from error


@dataclass
class Piece:
    start: int
    end: int
    kind: str
    section_key: int
    repetitions: list[tuple[int, int, str]] = field(default_factory=list)
    fragments: list[dict] = field(default_factory=list)


class AnnotationIndex:
    """Static interval index: nested annotations do not cause a full scan per chunk."""
    def __init__(self, annotations):
        values = [item for item in annotations if item.start < item.end]
        self.center = None
        if not values:
            return
        self.center = sorted((item.start + item.end)//2 for item in values)[len(values)//2]
        left, right, middle = [], [], []
        for item in values:
            (left if item.end <= self.center else right if item.start > self.center else middle).append(item)
        self.by_start = sorted(middle, key=lambda item:(item.start, item.end, item.block_ref or ''))
        self.by_end = sorted(middle, key=lambda item:(-item.end, item.start, item.block_ref or ''))
        self.left = AnnotationIndex(left) if left else None
        self.right = AnnotationIndex(right) if right else None

    def intersect(self, start, end):
        if self.center is None or start >= end:
            return []
        if end <= self.center:
            own = []
            for item in self.by_start:
                if item.start >= end:
                    break
                own.append(item)
            return own + (self.left.intersect(start, end) if self.left else [])
        if start > self.center:
            own = []
            for item in self.by_end:
                if item.end <= start:
                    break
                own.append(item)
            return own + (self.right.intersect(start, end) if self.right else [])
        return self.by_start + (self.left.intersect(start, end) if self.left else []) + (self.right.intersect(start, end) if self.right else [])


class StructuredChunker:
    def __init__(self, config: ChunkingConfig | None = None, counter=None):
        self.config = config or ChunkingConfig()
        self.counter = counter or EmbeddingTokenCounter()

    def _fits(self, text, limit):
        # Use the pinned vocabulary's actual longest token. Avoid encoding an
        # entire pathological multi-megabyte word just to learn that it cannot fit.
        return len(text) <= limit * self.counter.max_token_bytes and self.counter.count(text) <= limit

    def _prefix_end(self, text, start, end, limit):
        upper = min(end, start + max(128, limit * 16))
        while self._fits(text[start:upper], limit):
            if upper == end:
                return upper
            following = min(end, start + min(limit * self.counter.max_token_bytes, (upper - start) * 2))
            if following <= upper:
                return upper
            upper = following
        lower, best = start + 1, start
        while lower <= upper:
            middle = (lower + upper)//2
            if self.counter.count(text[start:middle]) <= limit:
                best = middle; lower = middle + 1
            else:
                upper = middle - 1
        if best == start:
            raise ValueError('Configured token budget cannot represent the next Unicode codepoint')
        return best

    def _suffix_start(self, text, start, end, limit):
        if limit <= 0:
            return end
        lower = max(start, end - limit * 16)
        if self._fits(text[lower:end], limit):
            return lower
        upper, best = end, end
        while lower <= upper:
            middle = (lower + upper)//2
            if self.counter.count(text[middle:end]) <= limit:
                best = middle; upper = middle - 1
            else:
                lower = middle + 1
        # Prefer a whole word/line/sentence over a partial suffix when available.
        for match in re.finditer(r'\s+', text[best:end]):
            candidate = best + match.end()
            if candidate < end and self.counter.count(text[candidate:end]) <= limit:
                return candidate
        return best

    def _boundary(self, text, start, end, budget, unit):
        limit = self._prefix_end(text, start, end, budget)
        if limit == end:
            return end, 'complete'
        position = bisect_right(unit.breaks, limit) - 1
        if position >= 0 and unit.breaks[position] > start:
            return unit.breaks[position], {'table':'table_rows','list':'list_items','code':'code_lines'}.get(unit.kind, 'structural_boundary')
        value = text[start:limit]
        for pattern, reason in [(r'\n[ \t]*\n+', 'paragraphs'),
                                (r'[.!?。！？][\"\'”’\)\]]*\s+', 'sentences'), (r'\s+', 'words')]:
            ends = [start + match.end() for match in re.finditer(pattern, value)]
            if ends and ends[-1] > start:
                return ends[-1], reason if unit.kind not in {'table','code','list'} else unit.kind + '_unit_' + reason
        return limit, {'table':'table_row_tokens','code':'code_line_tokens','list':'list_item_tokens'}.get(unit.kind, 'unicode_codepoint_tokens')

    def _split_unit(self, unit, text, generation):
        if self._fits(text[unit.start:unit.end], self.config.max_tokens):
            return [Piece(unit.start, unit.end, unit.kind, unit.section_key)]
        pieces, cursor, previous_start = [], unit.start, unit.start
        while cursor < unit.end:
            repetitions = []
            if unit.context is not None and cursor >= unit.context[1]:
                left, right = unit.context
                # Preserve an existing row separator; never synthesize untracked text.
                if right < len(text) and text[right] == '\n' and text[cursor:cursor + 1] != '\n':
                    right += 1
                reason = unit.context_reason or 'table_header'
                if not self._fits(text[left:right], self.config.max_tokens - 4):
                    right = self._prefix_end(text, left, right, max(4, min(self.config.overlap_tokens or 16, self.config.max_tokens//4)))
                    reason += '_partial'
                repetitions.append((left, right, reason))
            elif pieces and self.config.overlap_tokens and unit.kind != 'table':
                left = self._suffix_start(text, previous_start, cursor,
                    min(self.config.overlap_tokens, self.config.max_tokens - 4))
                if left < cursor:
                    repetitions.append((left, cursor, 'overlap'))
            prefix = ''.join(text[left:right] for left, right, _ in repetitions)
            prefix_tokens = self.counter.count(prefix)
            budget = max(4, self.config.target_tokens - prefix_tokens)
            budget = min(budget, self.config.max_tokens - prefix_tokens)
            finish, reason = self._boundary(text, cursor, unit.end, budget, unit)
            while self.counter.count(prefix + text[cursor:finish]) > self.config.max_tokens:
                finish -= 1
                if finish <= cursor:
                    raise ValueError('Repeated context leaves no primary content budget')
            fragment = {'fragment_group_id':fingerprint({'generation':generation,'unit_range':[unit.start,unit.end],'kind':unit.kind}),
                'fragment_index':len(pieces) + 1, 'fragment_count':0, 'split_reason':reason,
                'block_ref':unit.block_ref, 'unit_range':[unit.start,unit.end]}
            pieces.append(Piece(cursor, finish, unit.kind, unit.section_key, repetitions, [fragment]))
            previous_start, cursor = cursor, finish
        for piece in pieces:
            piece.fragments[0]['fragment_count'] = len(pieces)
        return pieces

    def _pack(self, pieces, text):
        groups, current = [], []
        def content(items):
            return ''.join(''.join(text[a:b] for a,b,_ in item.repetitions) + text[item.start:item.end] for item in items)
        for piece in pieces:
            same_section = not current or current[-1].section_key == piece.section_key
            same_fragmented_unit = current and piece.fragments and any(
                left['fragment_group_id'] == right['fragment_group_id']
                for item in current for left in item.fragments for right in piece.fragments)
            heading_prefix = current and all(item.kind == 'heading' or not text[item.start:item.end].strip() for item in current)
            candidate = content(current + [piece])
            limit = self.config.max_tokens if heading_prefix else self.config.target_tokens
            if current and (same_fragmented_unit or not (same_section or heading_prefix) or not self._fits(candidate, limit)):
                groups.append(current); current = []
            current.append(piece)
        if current:
            groups.append(current)
        return groups

    def _section_pieces(self, section, text, generation, heading_levels):
        """Preserve fitting child sections before falling back to individual blocks."""
        left, right = section[0].start, section[-1].end
        if self._fits(text[left:right], self.config.max_tokens):
            kinds = {unit.kind for unit in section if text[unit.start:unit.end].strip()}
            kind = next(iter(kinds)) if len(kinds) == 1 else 'mixed'
            return [Piece(left, right, kind, section[-1].section_key)]
        headings = [(index, heading_levels[unit.start]) for index, unit in enumerate(section)
                    if unit.kind == 'heading' and unit.start in heading_levels]
        if headings and headings[0][0] == 0:
            headings = headings[1:]  # Recurse into children, never into this same section.
        if headings:
            level = min(value for _, value in headings)
            boundaries = [index for index, value in headings if value == level]
            pieces, start = [], 0
            for end in boundaries + [len(section)]:
                if start < end:
                    pieces.extend(self._section_pieces(section[start:end], text, generation, heading_levels))
                start = end
            return pieces
        return [piece for unit in section for piece in self._split_unit(unit, text, generation)]


    def chunk_document(self, document):
        source = structure(document)
        text = source.text
        identity = generation_identity(document, self.config, self.counter.identity)
        generation = fingerprint(identity)
        # Only non-structural trailing whitespace may be omitted from embeddings;
        # its exact range is retained in the manifest and canonical parent text.
        effective_end = len(text)
        if text.strip() and source.units and source.units[-1].kind == 'paragraph':
            effective_end = max(len(text.rstrip()), max((unit.end for unit in source.units if unit.kind != 'paragraph'), default=0))
        ignored = [[effective_end, len(text)]] if effective_end < len(text) else []
        clipped = []
        for unit in source.units:
            if unit.start >= effective_end:
                break
            if unit.end > effective_end:
                unit = replace(unit, end=effective_end, breaks=tuple(x for x in unit.breaks if x <= effective_end))
            clipped.append(unit)
        sections = []
        for unit in clipped:
            prefix_only = sections and all(item.kind == 'heading' or not text[item.start:item.end].strip() for item in sections[-1])
            if not sections or (sections[-1][-1].section_key != unit.section_key and not prefix_only):
                sections.append([])
            sections[-1].append(unit)
        pieces = []
        heading_levels = {item.start:item.heading_level for item in source.annotations
                          if item.kind == 'heading' and type(item.heading_level) is int}
        for section in sections:
            pieces.extend(self._section_pieces(section, text, generation, heading_levels))
        index = AnnotationIndex(source.annotations)
        chunks = []
        previous_group = None
        for group in self._pack(pieces, text):
            # Related paragraphs also need context at packed-chunk boundaries.
            # Never carry it across independent sections or duplicate table context.
            if (previous_group and self.config.overlap_tokens and not group[0].repetitions
                    and group[0].kind != 'table'
                    and previous_group[-1].section_key == group[0].section_key):
                raw = ''.join(text[item.start:item.end] for item in group)
                spare = self.config.max_tokens - self.counter.count(raw)
                budget = min(self.config.overlap_tokens, max(0, spare))
                end = previous_group[-1].end
                start = self._suffix_start(text, previous_group[0].start, end, budget)
                while start < end and self.counter.count(text[start:end] + raw) > self.config.max_tokens:
                    start += 1
                if start < end:
                    group[0].repetitions.append((start, end, 'overlap'))
            previous_group = group
            content, primary, repetitions, fragments, spans = '', [], [], [], []
            kinds = set()
            for piece in group:
                kinds.add(piece.kind)
                for start, end, reason in piece.repetitions:
                    offset = len(content); content += text[start:end]
                    repetitions.append({'normalized_range':[start,end],'content_range':[offset,len(content)],
                                        'reason':reason,'token_count':self.counter.count(text[start:end])})
                offset = len(content); content += text[piece.start:piece.end]
                primary.append({'normalized_range':[piece.start,piece.end],'content_range':[offset,len(content)]})
                fragments.extend(piece.fragments)
            if not content.strip() and kinds != {'code'} and text.strip():
                # A whitespace-only separator can occur between separate sections.
                ignored.extend(item['normalized_range'] for item in primary)
                continue
            ranges = [item['normalized_range'] for item in primary + repetitions]
            for start, end in ranges:
                found = index.intersect(start, end)
                cursor = start
                for item in sorted(found, key=lambda value:(value.start,value.end)):
                    if item.start > cursor:
                        spans.append({'normalized_range':[cursor,min(end,item.start)],'block_ref':None,
                                      'original':{},'section_path':[],'heading_level':None})
                    cursor = max(cursor, min(end,item.end))
                if cursor < end:
                    spans.append({'normalized_range':[cursor,end],'block_ref':None,'original':{},
                                  'section_path':[],'heading_level':None})
                for item in sorted(found,key=lambda value:(value.start,value.end,value.block_ref or '')):
                    spans.append({'normalized_range':[max(start,item.start),min(end,item.end)],
                        'block_ref':item.block_ref,'original':{key:list(value) if isinstance(value,list) else value for key,value in item.original.items()},'section_path':list(item.section_path),
                        'heading_level':item.heading_level, 'list_depth':item.list_depth,
                        'content_type':item.kind, 'language':item.language,
                        'parent_normalized_range':list(item.parent_normalized_range) if item.parent_normalized_range else None,
                        'parent_block_ref':item.parent_block_ref})
            paths = [span['section_path'] for span in spans if span['section_path']]
            common = list(paths[0]) if paths else []
            for path in paths[1:]:
                while common and path[:len(common)] != common:
                    common.pop()
            if any(not span['section_path'] and text[slice(*span['normalized_range'])].strip() for span in spans):
                common = []
            content_type = next(iter(kinds)) if len(kinds) == 1 else 'mixed'
            if content_type in {'heading','text','list_item'}:
                content_type = 'list' if content_type == 'list_item' else 'paragraph'
            metadata = {'content_type':content_type,'token_count':self.counter.count(content),
                'chunk_hash':hashlib.sha256(content.encode('utf-8')).hexdigest(),
                'chunking_strategy':CHUNKING_STRATEGY,'chunking_version':CHUNKING_VERSION,
                'chunking_fingerprint':generation,'configuration_fingerprint':fingerprint(self.config.identity()),
                'tokenizer_id':self.counter.identity,'source_spans':spans,'primary_spans':primary,
                'repetitions':repetitions,'fragments':fragments,'warnings':list(source.warnings),
                'section_path':common or None,'heading_level':None,
                'effective_overlap_tokens':sum(item['token_count'] for item in repetitions if item['reason']=='overlap')}
            chunk_index = len(chunks)
            chunks.append({'chunk_id':chunk_identity(document['document_id'],generation,chunk_index),
                'document_id':document['document_id'],'chunk_index':chunk_index,'content':content,'metadata':metadata})
        # Fragment sequences describe persisted primary pieces. Whitespace-only
        # groups omitted above remain exact reconstruction data, not missing
        # chunk fragments; keep completeness checks strict for retained records.
        fragment_groups = {}
        for chunk in chunks:
            for fragment in chunk['metadata']['fragments']:
                fragment_groups.setdefault(fragment['fragment_group_id'], []).append(fragment)
        for group in fragment_groups.values():
            for number, fragment in enumerate(group, start=1):
                fragment['fragment_index'] = number
                fragment['fragment_count'] = len(group)
        result = {'chunks':chunks,'manifest':{'schema_version':1,**identity,'fingerprint':generation,
            'position_contract':dict(POSITION_CONTRACT),'ignored_whitespace_ranges':sorted(ignored),
            'chunk_count':len(chunks),'warnings':source.warnings}}
        if chunks:
            chunks[0]['metadata']['reconstruction'] = {
                'schema_version':1, 'document_characters':len(text), 'chunk_count':len(chunks),
                'document_text_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'omitted_spans':[{'normalized_range':[start,end], 'text':text[start:end]}
                                 for start,end in sorted(ignored)]}
        self.validate(document, result)
        return result

    def validate(self, document, result):
        text = document['text']
        covered, ids = [], set()
        expected_generation = fingerprint(generation_identity(document, self.config, self.counter.identity))
        if result['manifest']['fingerprint'] != expected_generation:
            raise ValueError('Chunk generation does not match its input or configuration')
        for number, chunk in enumerate(result['chunks']):
            metadata = chunk['metadata']
            if (chunk['document_id'] != document['document_id'] or chunk['chunk_index'] != number
                    or chunk['chunk_id'] in ids or not chunk['content']
                    or chunk['chunk_id'] != chunk_identity(document['document_id'], expected_generation, number)
                    or metadata['chunking_fingerprint'] != expected_generation
                    or metadata['chunk_hash'] != hashlib.sha256(chunk['content'].encode('utf-8')).hexdigest()
                    or metadata['token_count'] != self.counter.count(chunk['content'])
                    or metadata['token_count'] > self.config.max_tokens):
                raise ValueError('Invalid chunk content, identity or token budget')
            ids.add(chunk['chunk_id'])
            for span in metadata['source_spans']:
                start,end = span['normalized_range']
                if not 0 <= start < end <= len(text):
                    raise ValueError('Invalid source annotation range')
                ref = span.get('block_ref')
                if ref is not None:
                    value = document
                    try:
                        for key in ref.split('/'):
                            value = value[int(key)] if isinstance(value,list) else value[key]
                    except (KeyError,IndexError,TypeError,ValueError):
                        raise ValueError('Source annotation refers to a missing block') from None
                from app.embeddings.structure import _location
                _location(span['original'])
            output_ranges = []
            for key in ('primary_spans','repetitions'):
                for item in metadata[key]:
                    start,end = item['normalized_range']; left,right = item['content_range']
                    if not (0 <= start < end <= len(text) and 0 <= left < right <= len(chunk['content'])
                            and text[start:end] == chunk['content'][left:right]):
                        raise ValueError('Invalid chunk provenance')
                    output_ranges.append((left,right))
                    if key == 'primary_spans':
                        if covered and start < covered[-1][1]:
                            raise ValueError('Primary document order is incorrect')
                        covered.append((start,end))
            cursor = 0
            for left,right in sorted(output_ranges):
                if left != cursor:
                    raise ValueError('Untracked or duplicated chunk content')
                cursor = right
            if cursor != len(chunk['content']):
                raise ValueError('Untracked chunk suffix')
        for start,end in result['manifest']['ignored_whitespace_ranges']:
            if not 0 <= start < end <= len(text) or text[start:end].strip():
                raise ValueError('Only explicit whitespace ranges may be excluded')
            covered.append((start,end))
        cursor = 0
        for start,end in sorted(covered):
            if start != cursor:
                raise ValueError('Primary document coverage is lost, duplicated or reordered')
            cursor = end
        if cursor != len(text):
            raise ValueError('Primary document suffix is missing')

        if text and reconstruct_normalized_text(result['chunks']) != text:
            raise ValueError('Chunk-only reconstruction does not match the normalized document')
