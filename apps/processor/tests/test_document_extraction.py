"""Real document fixtures and Linux extraction-boundary regressions."""
import io
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from app.agents.guardrails import AgentInputError
from app.documents.document_processor import extract_local
from app.documents.document_formats import FormatError, validate_format


def docx_bytes():
    from docx import Document
    stream = io.BytesIO()
    document = Document()
    document.core_properties.title = 'Cost evidence'
    document.add_heading('Cloud budget', 1)
    document.add_paragraph('Before the table')
    table = document.add_table(rows=2, cols=2)
    for cell, value in zip([cell for row in table.rows for cell in row.cells], ['Service', 'USD', 'Compute', '42']):
        cell.text = value
    document.add_paragraph('After the table')
    document.save(stream)
    return stream.getvalue()


def pdf_bytes(kind='digital', pages=1):
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image, ImageDraw, ImageFont
    stream = io.BytesIO()
    document = canvas.Canvas(stream, pagesize=(612, 792))
    for index in range(pages):
        scanned = kind == 'scanned' or (kind == 'mixed' and index == 1) or kind == 'hybrid'
        if not scanned or kind == 'hybrid':
            document.setFont('Helvetica', 16)
            document.drawString(40, 740, f'Cloud costs page {index+1}')
            document.setFont('Helvetica', 12)
            document.drawString(40, 710, 'Compute budget is 42 USD.')
        if scanned:
            image = Image.new('RGB', (1500, 1200), 'white')
            drawing = ImageDraw.Draw(image)
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 60)
            drawing.text((80, 120), 'Scanned storage budget 73 USD', fill='black', font=font)
            document.drawImage(ImageReader(image), 40, 150, width=530, height=424)
        if kind == 'table':
            for y in (600, 630, 660):
                document.line(40, y, 340, y)
            for x in (40, 200, 340):
                document.line(x, 600, x, 660)
            for x, y, value in [(50,640,'Service'),(210,640,'USD'),(50,610,'Compute'),(210,610,'42')]:
                document.drawString(x, y, value)
        document.showPage()
    document.save()
    return stream.getvalue()


@pytest.mark.parametrize('extension,data', [('txt', b'\xef\xbb\xbfCloud budget\r\n42 USD'),
    ('md', b'# Budget\n\n- Compute\n\n| Service | USD |\n|---|---|\n| VM | 42 |\n\n```sql\nSELECT 1\n```\n\n[Reference](https://example.invalid)')])
def test_text_and_markdown_real_structure(extension, data):
    result = extract_local(data, extension)
    assert '42' in result['text']
    assert '\ufeff' not in result['text']
    assert result['result'] == 'extracted'
    if extension == 'md':
        assert {'heading', 'list', 'table', 'code', 'link'} <= {block['kind'] for block in result['blocks']}
        assert any(block.get('source_lines') for block in result['blocks'])


def test_docx_preserves_order_tables_and_available_metadata():
    result = extract_local(docx_bytes(), 'docx')
    assert result['file_metadata']['title'] == 'Cost evidence'
    assert [block['kind'] for block in result['blocks']] == ['heading', 'paragraph', 'table', 'paragraph']
    assert result['text'].index('Before') < result['text'].index('Compute') < result['text'].index('After')
    assert result['blocks'][0]['level'] == 1


@pytest.mark.parametrize('kind,pages', [('digital',2), ('table',1), ('scanned',1), ('mixed',2), ('hybrid',1)])
def test_pdf_real_pages_ocr_and_tables(kind, pages):
    result = extract_local(pdf_bytes(kind, pages), 'pdf')
    assert result['file_metadata']['page_count'] == pages
    assert {block['page'] for block in result['blocks']} == set(range(1,pages+1))
    if kind in {'scanned','mixed','hybrid'}:
        assert '73' in result['text'] and 'storage' in result['text'].lower()
        assert result['file_metadata']['ocr_pages']
    else:
        assert 'Compute' in result['text'] and not result['file_metadata']['ocr_pages']
    if kind == 'table':
        assert any(block['kind']=='table' and 'Compute' in str(block['rows']) for block in result['blocks'])


def test_legacy_doc_converts_locally_and_keeps_structure(tmp_path):
    source = tmp_path/'fixture.docx'
    source.write_bytes(docx_bytes())
    profile = tmp_path/'fixture-profile'
    result = subprocess.run(['libreoffice','-env:UserInstallation='+profile.as_uri(),'--headless',
                             '--convert-to','doc:MS Word 97','--outdir',str(tmp_path),str(source)],
                             capture_output=True,timeout=60)
    assert result.returncode==0 and source.with_suffix('.doc').is_file()
    extracted = extract_local(source.with_suffix('.doc').read_bytes(),'doc')
    assert 'Compute' in extracted['text']
    assert any(block['kind']=='table' for block in extracted['blocks'])
    assert extracted['extraction_method']=='libreoffice+python-docx'


@pytest.mark.parametrize('data,extension', [(b'', 'txt'),(b'\xff\xfe','txt'),(b'hello\x00world','md'),
    (b'%PDF-1.7\ninvalid\n%%EOF','pdf'),(b'not a doc','doc'),(b'PK\x03\x04broken','docx')])
def test_invalid_documents_are_rejected_without_parser_details(data,extension):
    with pytest.raises(AgentInputError,match='document_extraction_failed'):
        extract_local(data,extension)


def test_content_validation_rejects_disguised_pdf_and_macro_zip():
    with pytest.raises(FormatError):
        validate_format(pdf_bytes(),'txt')
    stream=io.BytesIO(docx_bytes())
    with zipfile.ZipFile(stream,'a') as archive:
        archive.writestr('word/vbaProject.bin',b'synthetic macro')
    with pytest.raises(FormatError,match='unsafe_document_container'):
        validate_format(stream.getvalue(),'docx')


def test_page_limit_is_enforced(monkeypatch):
    monkeypatch.setenv('DOCUMENT_MAX_PAGES','1')
    with pytest.raises(AgentInputError):
        extract_local(pdf_bytes(pages=2),'pdf')


def test_linux_sandbox_denies_network_and_unrelated_files(tmp_path, monkeypatch):
    allowed=tmp_path/'allowed'
    allowed.mkdir()
    outside=tmp_path/'outside'
    outside.write_text('synthetic inaccessible sentinel')
    code='''import os,socket,sys,sysconfig
from app.documents.extraction_sandbox import restrict
runtime_file=os.path.join(sysconfig.get_path('stdlib'),'encodings','utf_8_sig.py')
restrict(sys.argv[1],memory_mb=512,seconds=10,output_bytes=1000000)
assert open(runtime_file,'rb').read()
try:
    open(runtime_file,'r+b').close()
except PermissionError:
    pass
else:
    raise AssertionError('runtime write allowed')
try:
    socket.socket(socket.AF_INET,socket.SOCK_STREAM)
except PermissionError:
    pass
else:
    raise AssertionError('network allowed')
try:
    open(sys.argv[2]).read()
except PermissionError:
    pass
else:
    raise AssertionError('unrelated file allowed')
open(os.path.join(sys.argv[1],'own-data'),'w').write('allowed')
print('sandbox-pass')
'''
    # pytest's per-test cwd is temporary; the child cannot inherit sys.path.
    monkeypatch.delenv('PYTHONPATH', raising=False)
    environment={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])}
    result=subprocess.run([sys.executable,'-B','-c',code,str(allowed),str(outside)],
                          env=environment,capture_output=True,timeout=20)
    assert result.returncode==0, result.stderr.decode()
    assert result.stdout.strip()==b'sandbox-pass'
