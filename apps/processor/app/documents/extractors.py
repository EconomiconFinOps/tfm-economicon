"""Local format extraction, used only inside the restricted extraction process."""
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import time

from app.documents.document_formats import FormatError, text_content, validate_format


def markdown(data):
    from markdown_it import MarkdownIt
    value = text_content(data)
    parser = MarkdownIt('js-default').enable('table')
    tokens = parser.parse(value)
    blocks = []
    lines = value.split('\n')
    for token in tokens:
        if token.type in {'heading_open', 'paragraph_open', 'bullet_list_open', 'ordered_list_open',
                          'list_item_open', 'table_open', 'fence', 'code_block'}:
            kind = {'heading_open': 'heading', 'paragraph_open': 'paragraph',
                    'bullet_list_open': 'list', 'ordered_list_open': 'list', 'list_item_open': 'list_item',
                    'table_open': 'table', 'fence': 'code', 'code_block': 'code'}[token.type]
            block = {'kind': kind, 'level': int(token.tag[1:]) if kind == 'heading' else token.level,
                     'source_lines': [token.map[0] + 1, token.map[1]] if token.map else None}
            if token.map:
                block['text'] = '\n'.join(lines[token.map[0]:token.map[1]])
            if kind == 'code':
                block['language'] = token.info
            blocks.append(block)
        if token.children:
            for child in token.children:
                if child.type == 'link_open':
                    blocks.append({'kind': 'link', 'target': child.attrGet('href'),
                                   'source_lines': [token.map[0] + 1, token.map[1]] if token.map else None})
    return value, blocks, {}, [], 'markdown-it'


def docx(data):
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    document = Document(io.BytesIO(data))
    blocks, text = [], []
    def content(container, depth=0):
        if depth > 20:
            raise FormatError('document_structure_limit')
        result = []
        for item in container.iter_inner_content():
            if isinstance(item, Paragraph):
                value = item.text
                style = item.style.name if item.style is not None else ''
                heading = style.lower().startswith('heading ')
                listed = style.lower().startswith('list ') or (item._p.pPr is not None and item._p.pPr.numPr is not None)
                block = {'kind': 'heading' if heading else 'list_item' if listed else 'paragraph', 'text': value}
                if heading and style.rsplit(' ', 1)[-1].isdigit():
                    block['level'] = int(style.rsplit(' ', 1)[-1])
                result.append(block)
            elif isinstance(item, Table):
                cells = [[content(cell, depth + 1) for cell in row.cells] for row in item.rows]
                result.append({'kind': 'table', 'rows': cells})
        return result
    blocks = content(document)
    def flatten(items):
        for block in items:
            if block['kind'] == 'table':
                for row in block['rows']:
                    yield '\t'.join('\n'.join(flatten(cell)) for cell in row)
            else:
                yield block['text']
    value = '\n'.join(flatten(blocks))
    core = document.core_properties
    metadata = {key: getattr(core, key) for key in ('title', 'subject', 'author', 'keywords') if getattr(core, key)}
    warnings = ['docx_visual_layout_and_unrecognized_objects_not_inferred']
    return value, blocks, metadata, warnings, 'python-docx'


def legacy_doc(data, directory):
    profile = directory / 'profile'
    profile.mkdir()
    (profile / 'user').mkdir()
    (profile / 'user/registrymodifications.xcu').write_text('''<?xml version="1.0"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry">
<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="DisableMacrosExecution" oor:op="fuse"><value>true</value></prop><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item>
<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="DisableActiveContent" oor:op="fuse"><value>true</value></prop></item>
</oor:items>''')
    source = directory / 'source.doc'
    source.write_bytes(data)
    converted = directory / 'converted'
    converted.mkdir()
    command = ['/usr/lib/libreoffice/program/soffice.bin', '-env:UserInstallation=' + profile.as_uri(),
                             '-env:OSL_SOCKET_PATH=' + str(directory), '--headless',
                             '--nologo', '--nodefault', '--norestore', '--convert-to', 'docx',
                             '--outdir', str(converted), str(source)]
    deadline = time.monotonic() + 60
    for startup in range(2):
        result = subprocess.run(command, env={**os.environ, 'OSL_SOCKET_PATH': str(directory)},
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=max(0.1, deadline-time.monotonic()), check=False)
        # Official EXITHELPER_NORMAL_RESTART: first-run profile initialization.
        # One restart shares the same absolute conversion deadline.
        if result.returncode != 81:
            break
    output = converted / 'source.docx'
    if result.returncode != 0 or not output.is_file() or output.stat().st_size > 20_000_000:
        raise FormatError('document_conversion_failed')
    payload = output.read_bytes()
    validate_format(payload, 'docx')
    value, blocks, metadata, warnings, _ = docx(payload)
    return value, blocks, metadata, ['legacy_doc_converted_to_docx', *warnings], 'libreoffice+python-docx'


def pdf(data, directory, limits):
    import pdfplumber
    import pypdfium2
    blocks, texts, ocr_pages, warnings = [], [], [], []
    rendered = None
    try:
        with pdfplumber.open(io.BytesIO(data)) as document:
            if not 0 < len(document.pages) <= limits['max_pages']:
                raise FormatError('document_page_limit')
            metadata = {key: value for key, value in document.metadata.items()
                        if isinstance(value, (str, int, float, bool))}
            for index, page in enumerate(document.pages):
                page_number = index + 1
                native = page.extract_text(layout=False) or ''
                image_area = sum(abs((image['x1']-image['x0'])*(image['bottom']-image['top'])) for image in page.images)
                requires_ocr = not native.strip() or image_area > page.width * page.height * 0.15
                if requires_ocr:
                    if rendered is None:
                        rendered = pypdfium2.PdfDocument(data)
                    raster_page = rendered[index]
                    try:
                        scale = min(200/72, (limits['max_pixels'] / max(1, page.width * page.height)) ** 0.5)
                        bitmap = raster_page.render(scale=scale)
                        try:
                            image_path = directory / 'page.png'
                            bitmap.to_pil().save(image_path)
                        finally:
                            bitmap.close()
                    finally:
                        raster_page.close()
                    output = directory / 'ocr'
                    process = subprocess.run(['tesseract', str(image_path), str(output), '-l', 'spa+eng', 'tsv'],
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                             timeout=limits['page_seconds'], check=False)
                    if process.returncode != 0 or not output.with_suffix('.tsv').is_file():
                        raise FormatError('document_ocr_failed')
                    lines = {}
                    with output.with_suffix('.tsv').open() as stream:
                        for word in csv.DictReader(stream, delimiter='\t', quoting=csv.QUOTE_NONE):
                            if word.get('level') == '5' and word.get('text', '').strip():
                                key = tuple(word[k] for k in ('block_num', 'par_num', 'line_num'))
                                lines.setdefault(key, []).append(word)
                    page_lines = []
                    for words in lines.values():
                        content = ' '.join(word['text'] for word in words)
                        left, top = min(int(w['left']) for w in words), min(int(w['top']) for w in words)
                        right = max(int(w['left'])+int(w['width']) for w in words)
                        bottom = max(int(w['top'])+int(w['height']) for w in words)
                        blocks.append({'kind': 'text', 'page': page_number, 'method': 'ocr', 'text': content,
                                       'bbox': [left, top, right, bottom], 'coordinate_system': 'render_pixels'})
                        page_lines.append(content)
                    value = '\n'.join(page_lines)
                    if not value.strip():
                        raise FormatError('document_ocr_empty')
                    ocr_pages.append(page_number)
                    warnings.append(f'page_{page_number}_ocr_layout_is_approximate')
                    if native.strip():
                        warnings.append(f'page_{page_number}_native_text_replaced_by_full_page_ocr')
                else:
                    value = native
                    for line in page.extract_text_lines():
                        blocks.append({'kind': 'text', 'page': page_number, 'text': line['text'],
                                       'bbox': [line['x0'], line['top'], line['x1'], line['bottom']],
                                       'coordinate_system': 'pdf_points'})
                    for table in page.find_tables():
                        blocks.append({'kind': 'table', 'page': page_number, 'rows': table.extract(),
                                       'bbox': list(table.bbox), 'coordinate_system': 'pdf_points'})
                texts.append(value)
                page.close()
            metadata['page_count'] = len(document.pages)
            metadata['ocr_pages'] = ocr_pages
            warnings.append('pdf_reading_order_is_extractor_order_not_semantic_guarantee')
    finally:
        if rendered is not None:
            rendered.close()
    return '\n\n'.join(texts), blocks, metadata, warnings, 'pdfplumber+tesseract' if ocr_pages else 'pdfplumber'


def extract(data, extension, directory, limits):
    validate_format(data, extension)
    if extension == 'md':
        result = markdown(data)
    elif extension == 'txt':
        value = text_content(data)
        result = value, [{'kind': 'text', 'text': value, 'source_lines': [1, len(value.splitlines())]}], {}, [], 'utf-8'
    elif extension == 'docx':
        result = docx(data)
    elif extension == 'doc':
        result = legacy_doc(data, directory)
    else:
        result = pdf(data, directory, limits)
    value, blocks, metadata, warnings, method = result
    if not value.strip():
        raise FormatError('document_extraction_empty')
    if len(value) > limits['max_text_chars'] or len(blocks) > limits['max_blocks']:
        raise FormatError('document_structure_limit')
    return {'text': value, 'blocks': blocks, 'file_metadata': metadata, 'warnings': warnings,
            'extraction_method': method, 'result': 'extracted'}
