"""Parent titles preserve ATX semantics without pathological whitespace backtracking."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest
from app.embeddings.normalized import parent_metadata


def document(heading, fmt='md', title=None):
    return {'original_format': fmt, 'text': heading, 'blocks': [
        {'kind': 'heading', 'text': heading}], 'file_metadata': {'title': title}}


@pytest.mark.parametrize('heading,expected', [
    ('# C# ', 'C#'), ('## Q3 ###', 'Q3'), ('#hashtag', '#hashtag'),
    ('#', '#'), ('# ', None), ('', None), ('   ### Heading ###\t', 'Heading'),
    ('    # Indented', '# Indented'), ('####### Seven', '####### Seven'),
    ('#\tTitle\t###\t', 'Title'), ('# ### ', '###'),
    ('# Q3 ###\n', 'Q3'), ('# Q3 ###\r', 'Q3 ###'),
    ('Setext title', 'Setext title'), ('# Q3 ### trailing', 'Q3 ### trailing'),
])
def test_markdown_parent_title_marker_boundaries(heading, expected):
    source = document(heading)
    before = deepcopy(source)
    assert parent_metadata(source, {})['title'] == expected
    assert source == before


def test_explicit_title_and_other_formats_are_not_reinterpreted():
    assert parent_metadata(document('# Raw', title='# Explicit'), {})['title'] == '# Explicit'
    assert parent_metadata(document('# Raw ', fmt='docx'), {})['title'] == '# Raw '


def test_markdown_title_with_200000_internal_spaces_is_bounded():
    # Isolate the hostile input so a regression is killed, never left occupying a worker.
    program = '''
import json,sys,time
from app.embeddings.normalized import parent_metadata
heading = '# a' + ' ' * 200000 + 'b'
document = {'original_format':'md','text':heading,'blocks':[{'kind':'heading','text':heading}],'file_metadata':{}}
started = time.perf_counter()
assert parent_metadata(document,{})['title'] == heading[2:]
print(json.dumps({'elapsed_seconds':time.perf_counter()-started}))
'''
    result = subprocess.run([sys.executable, '-B', '-c', program],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=5, check=True)
    assert json.loads(result.stdout)['elapsed_seconds'] < 2
