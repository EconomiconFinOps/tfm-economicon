"""Non-executing admission checks shared as a contract by both deployments."""
import copy
import io
import lzma
from pathlib import PurePosixPath
import zipfile
import zlib
from xml.etree import ElementTree


FORMATS = {'md', 'txt', 'pdf', 'docx', 'doc'}


class FormatError(ValueError):
    pass


class _DocumentTreeBuilder(ElementTree.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise FormatError('unsafe_document_xml')


def _read_member(archive, member, remaining, *, retain=False):
    # ZipExtFile otherwise clips output to the untrusted declared length. Read
    # one actual byte beyond it, with bounded DEFLATE output and CRC checking.
    limit = min(member.file_size, 20_000_000, remaining)
    bounded = copy.copy(member)
    bounded.file_size = limit + 1
    size, parts = 0, []
    with archive.open(bounded) as stream:
        while True:
            block = stream.read(min(65536, limit - size + 1))
            if not block:
                break
            size += len(block)
            if size > limit:
                raise FormatError('document_expansion_limit')
            if retain:
                parts.append(block)
    if size != member.file_size:
        raise FormatError('invalid_document_container')
    return size, b''.join(parts)


def filename_format(filename):
    if (not filename or len(filename) > 240 or '/' in filename or '\\' in filename
            or any(ord(c) < 32 or ord(c) == 127 for c in filename)):
        raise FormatError('invalid_filename')
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension not in FORMATS:
        raise FormatError('unsupported_document_format')
    return extension


def text_content(data):
    try:
        value = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise FormatError('invalid_document_encoding') from None
    if not value.strip() or any(ord(c) < 32 and c not in '\r\n\t\f' for c in value):
        raise FormatError('empty_or_binary_document')
    # Text extensions are not an escape hatch for binary/container formats.
    if data.startswith((b'%PDF-', b'PK\x03\x04', b'\xd0\xcf\x11\xe0')):
        raise FormatError('document_format_mismatch')
    return value.replace('\r\n', '\n').replace('\r', '\n')


def validate_format(data, extension):
    if extension in {'txt', 'md'}:
        text_content(data)
    elif extension == 'pdf':
        if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-2048:]:
            raise FormatError('invalid_pdf_document')
    elif extension == 'docx':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                members = archive.infolist()
                names = [member.filename for member in members]
                if (len(members) > 2000 or len(set(names)) != len(names)
                        or sum(member.file_size for member in members) > 80_000_000):
                    raise FormatError('document_expansion_limit')
                extracted, actual_total = {}, 0
                for member in members:
                    path = PurePosixPath(member.filename)
                    if (path.is_absolute() or '..' in path.parts or '\\' in member.filename
                            or member.flag_bits & 1 or member.file_size > 20_000_000
                            or member.file_size > max(1, member.compress_size) * 1000
                            or 'vbaproject' in member.filename.lower()):
                        raise FormatError('unsafe_document_container')
                    # OPC uses stored/DEFLATE entries. BZip2/LZMA in older
                    # ZipExtFile runtimes can allocate unbounded output per read.
                    if member.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                        raise FormatError('invalid_docx_document')
                    retain = member.filename in {'word/document.xml', '[Content_Types].xml'}
                    size, value = _read_member(archive, member, 80_000_000 - actual_total, retain=retain)
                    actual_total += size
                    if retain:
                        extracted[member.filename] = value
                document = extracted['word/document.xml']
                content_types = extracted['[Content_Types].xml']
                root = ElementTree.fromstring(document, parser=ElementTree.XMLParser(target=_DocumentTreeBuilder()))
                if (root.tag != '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document'
                        or b'wordprocessingml.document.main+xml' not in content_types):
                    raise FormatError('document_format_mismatch')
        except FormatError:
            raise
        except (zipfile.BadZipFile, KeyError, ValueError, ElementTree.ParseError, RuntimeError,
                zlib.error, lzma.LZMAError, OSError, EOFError):
            raise FormatError('invalid_docx_document') from None
    elif extension == 'doc':
        import olefile
        try:
            with olefile.OleFileIO(io.BytesIO(data)) as document:
                if not document.exists('WordDocument') or not (document.exists('0Table') or document.exists('1Table')):
                    raise FormatError('document_format_mismatch')
                if any(part.lower() in {'vba', 'macros', 'encryptedpackage'}
                       for stream in document.listdir() for part in stream):
                    raise FormatError('active_or_encrypted_document')
        except FormatError:
            raise
        except (OSError, ValueError):
            raise FormatError('invalid_doc_document') from None
    else:
        raise FormatError('unsupported_document_format')
    return extension
