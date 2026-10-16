"""Canonical text coverage plus verified structure; blocks are never concatenated blindly."""
from dataclasses import dataclass, field
from bisect import bisect_right
from itertools import islice
import math
import re
from markdown_it import MarkdownIt
from app.embeddings.contracts import document_identity


@dataclass
class Annotation:
    start: int
    end: int
    kind: str
    block_ref: str | None = None
    original: dict = field(default_factory=dict)
    section_path: tuple[str, ...] = ()
    heading_level: int | None = None
    title: str | None = None
    list_depth: int | None = None
    language: str | None = None
    parent_normalized_range: tuple[int, int] | None = None
    parent_block_ref: str | None = None


@dataclass
class Unit:
    start: int
    end: int
    kind: str
    breaks: tuple[int, ...] = ()
    context: tuple[int, int] | None = None
    context_reason: str | None = None
    section_key: int = 0
    section_path: tuple[str, ...] = ()
    block_ref: str | None = None


@dataclass
class StructuredText:
    text: str
    units: list[Unit]
    annotations: list[Annotation]
    warnings: list[str]


def _location(block: dict) -> dict:
    original = {}
    for key in ('row_range', 'column_range'):
        if key in block:
            value = block[key]
            if (not isinstance(value, list) or len(value) != 2 or any(type(x) is not int for x in value)
                    or not 0 <= value[0] < value[1]):
                raise ValueError('Invalid table grid range')
            original[key] = list(value)
    if 'page' in block:
        if type(block['page']) is not int or block['page'] < 1:
            raise ValueError('Invalid original page')
        original['page'] = block['page']
    if 'source_lines' in block:
        lines = block['source_lines']
        if (not isinstance(lines, list) or len(lines) != 2 or any(type(x) is not int for x in lines)
                or not 1 <= lines[0] <= lines[1]):
            raise ValueError('Invalid original lines')
        original['source_lines'] = list(lines)
    if 'bbox' in block:
        box = block['bbox']
        if (not isinstance(box, list) or len(box) != 4
                or any(type(x) not in {int, float} or not math.isfinite(x) for x in box)
                or box[0] > box[2] or box[1] > box[3]
                or block.get('coordinate_system') not in {'pdf_points', 'render_pixels'}):
            raise ValueError('Invalid original coordinates')
        original.update(bbox=list(box), coordinate_system=block['coordinate_system'], bbox_scope='source_block')
    if block.get('method') is not None:
        original['method'] = block['method']
    return original


def _paragraphs(text: str, start=0, end=None) -> list[Unit]:
    end = len(text) if end is None else end
    cursor = start
    result = []
    for match in re.finditer(r'\n[ \t]*\n+', text[start:end]):
        boundary = start + match.end()
        if boundary > cursor:
            result.append(Unit(cursor, boundary, 'paragraph'))
            cursor = boundary
    if cursor < end:
        result.append(Unit(cursor, end, 'paragraph'))
    return result


def _markdown(document):
    text, blocks = document['text'], document.get('blocks', [])
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    source = text
    units, annotations, warnings = [], [], []
    front_end = 0
    if lines and lines[0].strip() == '---':
        for index, line in enumerate(lines[1:], 1):
            if line.strip() in {'---', '...'}:
                front_end = offsets[index + 1]
                source = ''.join('\n' if char == '\n' else ' ' for char in text[:front_end]) + text[front_end:]
                units.append(Unit(0, front_end, 'mixed'))
                annotations.append(Annotation(0, front_end, 'frontmatter'))
                break
    tokens = MarkdownIt('js-default').enable('table').parse(source)
    covered_until = front_end
    list_parents = []
    block_locations = {(block.get('kind'), tuple(block.get('source_lines', []))):i
                       for i,block in reversed(list(enumerate(blocks)))}
    for index, token in enumerate(tokens):
        if token.map is None:
            continue
        start, end = offsets[token.map[0]], offsets[min(token.map[1], len(lines))]
        if not start < end:
            continue
        mapping = {'heading_open':'heading', 'paragraph_open':'paragraph', 'bullet_list_open':'list',
                   'ordered_list_open':'list', 'list_item_open':'list_item', 'table_open':'table',
                   'fence':'code', 'code_block':'code', 'hr':'mixed', 'html_block':'mixed', 'blockquote_open':'mixed'}
        kind = mapping.get(token.type)
        if kind is None:
            continue
        existing_kind = 'list' if kind == 'list' else kind
        block_index = block_locations.get((existing_kind, (token.map[0] + 1, token.map[1])))
        ref = f'blocks/{block_index}' if block_index is not None else None
        original = _location(blocks[int(ref.split('/')[1])]) if ref else {}
        annotation = Annotation(start, end, kind, ref, original)
        if kind == 'heading':
            annotation.heading_level = int(token.tag[1:])
            inline = tokens[index + 1] if index + 1 < len(tokens) else None
            annotation.title = (''.join(child.content for child in inline.children if child.type in {'text', 'code_inline'})
                                if inline is not None and inline.children else text[start:end].strip())
        if kind == 'list_item':
            annotation.list_depth = max(0, token.level // 2)
            while list_parents and not (list_parents[-1].start <= start and end <= list_parents[-1].end
                                        and list_parents[-1].list_depth < annotation.list_depth):
                list_parents.pop()
            if list_parents:
                annotation.parent_normalized_range = (list_parents[-1].start,list_parents[-1].end)
                annotation.parent_block_ref = list_parents[-1].block_ref
            list_parents.append(annotation)
        if kind == 'code':
            annotation.language = token.info.strip().split()[0] if token.info.strip() else None
        annotations.append(annotation)
        if start < covered_until or kind == 'list_item':
            continue  # Annotations may nest; primary units never overlap.
        unit = Unit(start, end, kind, block_ref=ref)
        if kind == 'table':
            row_index = 0
            for child in islice(tokens, index + 1, None):
                if child.type == 'table_close':
                    break
                if child.type == 'tr_open' and child.map is not None:
                    left,right = offsets[child.map[0]], offsets[child.map[1]]
                    location = {'row_range':[row_index,row_index + 1]}
                    if original.get('source_lines'):
                        location['source_lines'] = [child.map[0] + 1,child.map[1]]
                    annotations.append(Annotation(left,right,'table',ref,location))
                    row_index += 1
            unit.breaks = tuple(offsets[line] for line in range(token.map[0] + 2, token.map[1] + 1))
            if token.map[0] + 2 <= len(lines):
                unit.context = (start, offsets[token.map[0] + 2])
                unit.context_reason = 'table_header'
        elif kind == 'list':
            boundaries = set()
            for child in islice(tokens, index + 1, None):
                if child.type in {'bullet_list_close','ordered_list_close'} and child.level == token.level:
                    break
                if child.type == 'list_item_open' and child.map is not None and child.level == token.level + 1:
                    boundaries.add(offsets[min(child.map[1],len(lines))])
            unit.breaks = tuple(sorted(boundaries))
        elif kind == 'code':
            unit.breaks = tuple(offsets[line] for line in range(token.map[0] + 1, token.map[1] + 1))
        units.append(unit)
        covered_until = end
    return units, annotations, warnings


def _word(document):
    annotations, tables = [], {}
    def render(block, start, path):
        kind = block.get('kind', 'paragraph')
        if kind != 'table':
            value = block.get('text', '')
            if not isinstance(value, str):
                raise ValueError('Invalid normalized Word block')
            annotations.append(Annotation(start, start + len(value), kind, path, _location(block),
                heading_level=block.get('level') if kind == 'heading' else None,
                title=value if kind == 'heading' else None))
            return value
        rows = block.get('rows', [])
        if not isinstance(rows, list):
            raise ValueError('Invalid normalized Word rows')
        output, ends, cursor = [], [], start
        first_row = None
        for ri, row in enumerate(rows):
            if ri:
                output.append('\n'); cursor += 1
            row_start = cursor
            for ci, cell in enumerate(row):
                if ci:
                    output.append('\t'); cursor += 1
                if not isinstance(cell, list):
                    raise ValueError('Invalid normalized Word cell')
                cell_start = cursor
                for bi, nested in enumerate(cell):
                    if bi:
                        output.append('\n'); cursor += 1
                    value = render(nested, cursor, f'{path}/rows/{ri}/{ci}/{bi}')
                    output.append(value); cursor += len(value)
                if cursor > cell_start:
                    annotations.append(Annotation(cell_start,cursor,'table',f'{path}/rows/{ri}/{ci}',
                        {'row_range':[ri,ri + 1],'column_range':[ci,ci + 1]}))
            annotations.append(Annotation(row_start, cursor, 'table', f'{path}/rows/{ri}',
                                          {'row_range':[ri, ri + 1], 'column_range':[0, len(row)]}))
            ends.append(cursor)
            if first_row is None:
                first_row = (row_start, cursor)
        value = ''.join(output)
        annotations.append(Annotation(start, start + len(value), 'table', path, _location(block)))
        tables[path] = (tuple(ends), first_row)
        return value
    units, parts, cursor = [], [], 0
    for index, block in enumerate(document.get('blocks', [])):
        if index:
            parts.append('\n'); cursor += 1
        ref = f'blocks/{index}'
        value = render(block, cursor, ref)
        unit = Unit(cursor, cursor + len(value), block.get('kind', 'paragraph'), block_ref=ref)
        if unit.kind == 'table':
            unit.breaks, unit.context = tables[ref]
            unit.context_reason = 'table_first_row_context'  # Extraction did not label a header.
        parts.append(value); units.append(unit); cursor += len(value)
    if ''.join(parts) != document['text']:
        return [], [], ['word_structure_not_aligned_with_canonical_text']
    return units, annotations, []


def _find_text(text, value, start=0, end=None, unique=True):
    end = len(text) if end is None else end
    words = re.split(r'\s+', value.strip())
    if not words or not words[0]:
        return None
    pattern = re.compile(r'\s+'.join(re.escape(word) for word in words))
    match = pattern.search(text, start, end)
    if match is None or (unique and pattern.search(text, match.end(), end) is not None):
        return None
    return match.start(), match.end()


def _plain_lists(text):
    """Use explicit marker indentation for parents, without inventing headings."""
    units, annotations, parents = [], [], []
    start, end, boundaries, stack = None, 0, [], []

    def close_items(until, indentation=None):
        while stack and (indentation is None or stack[-1][0] >= indentation):
            _, item = stack.pop()
            item.end = until
            if not stack:
                boundaries.append(until)

    cursor = 0
    for line in text.splitlines(keepends=True):
        finish = cursor + len(line)
        marker = re.match(r'^([ \t]*)(?:[-+*]|\d+[.)])[ \t]+\S',line)
        continuation = start is not None and bool(re.match(r'^[ \t]+\S',line))
        if marker:
            if start is None:
                start = cursor
            indentation = len(marker[1].expandtabs(8))
            close_items(cursor, indentation)
            item = Annotation(cursor,finish,'list_item',list_depth=len(stack))
            if stack:
                parents.append((item,stack[-1][1]))
            annotations.append(item)
            stack.append((indentation,item))
            end = finish
        elif continuation:
            end = finish
        elif start is not None:
            close_items(end)
            units.append(Unit(start,end,'list',tuple(boundaries)))
            start, boundaries = None, []
        cursor = finish
    if start is not None:
        close_items(end)
        units.append(Unit(start,end,'list',tuple(boundaries)))
    for child,parent in parents:
        child.parent_normalized_range = (parent.start,parent.end)
    return units, annotations


def _pdf(document):
    text, blocks = document['text'], document.get('blocks', [])
    lines = [(i, block) for i, block in enumerate(blocks)
             if block.get('kind') in {'text','paragraph','heading','list','list_item','code'} and block.get('text')]
    complete = re.sub(r'\s+', '', ''.join(block['text'] for _, block in lines)) == re.sub(r'\s+', '', text)
    cursor, annotations, units, warnings = 0, [], [], []
    for index, block in lines:
        location = _location(block)
        found = _find_text(text, block['text'], cursor if complete else 0, unique=not complete)
        if found is None:
            warnings.append('pdf_source_block_not_aligned')
            continue
        start, end = found
        if complete:
            cursor = end
        kind = block.get('kind', 'text')
        annotations.append(Annotation(start, end, kind, f'blocks/{index}', location,
            heading_level=block.get('level') if kind == 'heading' else None,
            title=block['text'] if kind == 'heading' else None))
    for index, block in enumerate(blocks):
        if block.get('kind') != 'table':
            continue
        location = _location(block)
        available = [item for item in annotations if item.original.get('page') == location.get('page')]
        if 'bbox' in location:
            box = location['bbox']
            available = [item for item in available if item.original.get('coordinate_system') == location.get('coordinate_system')
                and 'bbox' in item.original and item.original['bbox'][0] >= box[0] - 1
                and item.original['bbox'][1] >= box[1] - 1 and item.original['bbox'][2] <= box[2] + 1
                and item.original['bbox'][3] <= box[3] + 1]
        if not available:
            warnings.append('pdf_table_not_aligned'); continue
        lower, upper = min(item.start for item in available), max(item.end for item in available)
        spans, row_annotations = [], []
        for ri, row in enumerate(block.get('rows', [])):
            value = ' '.join(str(cell) for cell in row if cell is not None and str(cell).strip())
            found = _find_text(text, value, spans[-1][1] if spans else lower, upper)
            if found is None:
                spans = []; break
            spans.append(found)
            row_annotations.append(Annotation(*found, 'table', f'blocks/{index}/rows/{ri}',
                {**location, 'row_range':[ri, ri + 1], 'column_range':[0, len(row)]}))
        if (not spans or any(text[left[1]:right[0]].strip() for left, right in zip(spans, spans[1:]))):
            warnings.append('pdf_table_not_aligned'); continue
        start, end = spans[0][0], spans[-1][1]
        if any(start < item.end and item.start < end for item in units):
            warnings.append('pdf_table_overlapping_annotations'); continue
        units.append(Unit(start, end, 'table', tuple(item[1] for item in spans), spans[0],
                          'table_first_row_context', block_ref=f'blocks/{index}'))
        annotations.extend(row_annotations)
        annotations.append(Annotation(start, end, 'table', f'blocks/{index}', location))
    for item in annotations:
        if item.kind in {'heading','paragraph','code','list','list_item'} and not any(
                item.start < unit.end and unit.start < item.end for unit in units):
            units.append(Unit(item.start, item.end, item.kind, block_ref=item.block_ref))
    return units, annotations, warnings


def structure(document: dict) -> StructuredText:
    document_identity(document)
    fmt, text = document.get('original_format', 'manual-text'), document['text']
    if fmt == 'md':
        units, annotations, warnings = _markdown(document)
    elif fmt in {'doc', 'docx'} and document.get('blocks'):
        units, annotations, warnings = _word(document)
    elif fmt == 'pdf' and document.get('blocks'):
        units, annotations, warnings = _pdf(document)
    else:
        units, annotations = _plain_lists(text)
        warnings = [] if fmt in {'txt', 'manual-text'} else ['plain_text_fallback_structure_unavailable']
        for index, block in enumerate(document.get('blocks', [])):
            _location(block)
            if block.get('text') == text:
                location = _location(block)
                lines = text.splitlines(keepends=True)
                if (location.get('source_lines') and len(lines) == location['source_lines'][1] - location['source_lines'][0] + 1):
                    cursor = 0
                    for line_number,line in enumerate(lines,location['source_lines'][0]):
                        annotations.append(Annotation(cursor,cursor + len(line),'text',f'blocks/{index}',
                            {**location,'source_lines':[line_number,line_number]}))
                        cursor += len(line)
                else:
                    annotations.append(Annotation(0, len(text), 'text', f'blocks/{index}', location))
    # Fill gaps from canonical text; never use annotations as another content copy.
    ordered, cursor = [], 0
    for unit in sorted(units, key=lambda item:(item.start, item.end)):
        if unit.start < cursor or unit.end > len(text) or unit.start > unit.end:
            raise ValueError('Overlapping or invalid primary structure')
        ordered.extend(_paragraphs(text, cursor, unit.start))
        if unit.start < unit.end:
            ordered.append(unit)
        cursor = unit.end
    ordered.extend(_paragraphs(text, cursor))
    root_headings = {(unit.start, unit.end) for unit in ordered if unit.kind == 'heading'}
    headings = sorted((item for item in annotations if item.kind == 'heading' and item.title
                       and (item.start, item.end) in root_headings), key=lambda item:item.start)
    stack, group, current, hi = [], 0, (), 0
    for unit in ordered:
        while hi < len(headings) and headings[hi].start <= unit.start:
            heading = headings[hi]
            level = heading.heading_level
            if type(level) is not int or level < 1:
                raise ValueError('Invalid heading hierarchy')
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, heading.title))
            current = tuple(value for _, value in stack)
            if level <= 2:
                group = heading.start + 1
            hi += 1
        unit.section_key, unit.section_path = group, current
    unit_starts = [unit.start for unit in ordered]
    for item in annotations:
        position = bisect_right(unit_starts,item.start) - 1
        matching = ordered[position] if position >= 0 and item.start < ordered[position].end else None
        if matching:
            item.section_path = matching.section_path
    # Consecutive Word list items are one recoverable logical list, without invented depth.
    merged = []
    for unit in ordered:
        if (unit.kind == 'list_item' and len(merged) >= 2 and merged[-2].kind == 'list'
                and merged[-2].section_key == unit.section_key
                and not text[merged[-1].start:merged[-1].end].strip()):
            gap = merged.pop()
            merged[-1].end = gap.end
        if (merged and unit.kind == 'list_item' and merged[-1].kind == 'list'
                and merged[-1].section_key == unit.section_key and not text[merged[-1].end:unit.start].strip()):
            prior = merged[-1]; prior.end = unit.end; prior.breaks += (unit.end,)
        else:
            if unit.kind == 'list_item':
                unit.kind = 'list'; unit.breaks = (unit.end,)
            merged.append(unit)
    return StructuredText(text, merged, annotations, sorted(set(warnings)))
