"""Actual decompression and XML limits for both deployed admission copies."""
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import zipfile
import zlib

import pytest


ROOT=Path(__file__).resolve().parents[3]
MODULES=[ROOT/'apps/backend/app/services/document_formats.py',
         ROOT/'apps/processor/app/documents/document_formats.py']
DOCUMENT=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'


def container(compression=zipfile.ZIP_DEFLATED,document=DOCUMENT,*,extra_bytes=0,forged=False):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=compression) as archive:
        archive.writestr('[Content_Types].xml',b'wordprocessingml.document.main+xml')
        with archive.open('word/document.xml','w') as member:
            member.write(document)
            block=b'x'*65536
            for _ in range(extra_bytes//len(block)):member.write(block)
    raw=bytearray(stream.getvalue())
    if forged:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            info=archive.getinfo('word/document.xml')
        # Forge both headers and the prefix CRC, not merely the directory ratio.
        struct.pack_into('<I',raw,info.header_offset+22,len(document))
        struct.pack_into('<I',raw,info.header_offset+14,zlib.crc32(document))
        cursor=0
        while (cursor:=raw.find(b'PK\x01\x02',cursor))>=0:
            name_size,extra_size,comment_size=struct.unpack_from('<HHH',raw,cursor+28)
            name=raw[cursor+46:cursor+46+name_size]
            if name==b'word/document.xml':
                struct.pack_into('<I',raw,cursor+24,len(document))
                struct.pack_into('<I',raw,cursor+16,zlib.crc32(document))
            cursor+=46+name_size+extra_size+comment_size
    return bytes(raw)


def load(path):
    spec=importlib.util.spec_from_file_location('bounded_format_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('module_path',MODULES,ids=['backend','processor'])
@pytest.mark.parametrize('compression',[zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED])
def test_supported_docx_container_still_passes(module_path,compression):
    assert load(module_path).validate_format(container(compression),'docx')=='docx'


@pytest.mark.parametrize('module_path',MODULES,ids=['backend','processor'])
def test_actual_deflate_bytes_cannot_hide_behind_forged_size_and_crc(module_path):
    module=load(module_path)
    raw=container(extra_bytes=1024*1024,forged=True)
    with pytest.raises(module.FormatError):module.validate_format(raw,'docx')


@pytest.mark.parametrize('module_path',MODULES,ids=['backend','processor'])
@pytest.mark.parametrize('encoding',['utf-8','utf-16','utf-16-be'])
def test_dtd_is_rejected_independently_of_xml_encoding(module_path,encoding):
    module=load(module_path)
    document=('<?xml version="1.0"?><!DOCTYPE w:document [<!ENTITY a "fixture">]>'
              '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">&a;</w:document>').encode(encoding)
    if encoding=='utf-16-be':document=b'\xfe\xff'+document
    with pytest.raises(module.FormatError,match='unsafe_document_xml'):
        module.validate_format(container(document=document),'docx')


@pytest.mark.skipif(sys.platform!='linux',reason='Linux peak RSS measured in the isolated test container')
@pytest.mark.parametrize('module_path',MODULES,ids=['backend','processor'])
def test_forged_bzip2_container_has_bounded_peak_memory(module_path,tmp_path):
    # Stream creation in the owned container: never allocate the32MiB expansion.
    source=tmp_path/'forged.docx'
    source.write_bytes(container(zipfile.ZIP_BZIP2,extra_bytes=32*1024*1024,forged=True))
    script='''import importlib.util,json,resource,sys
spec=importlib.util.spec_from_file_location("formats",sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
raw=open(sys.argv[2],"rb").read()
before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
rejected=False
try:module.validate_format(raw,"docx")
except module.FormatError:rejected=True
after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({"rejected":rejected,"peak_delta_kib":after-before}))
'''
    result=subprocess.run([sys.executable,'-B','-c',script,str(module_path),str(source)],
                          capture_output=True,timeout=20,check=True)
    observed=json.loads(result.stdout)
    print(json.dumps({'copy':str(module_path.relative_to(ROOT)),**observed}))
    assert observed['rejected']
    assert observed['peak_delta_kib']<16*1024,observed
