"""Markdown blocks keep their own text and the extractor reads the source lines once."""
import pytest

from app.documents import extractors


@pytest.mark.parametrize('separator', ['\f', ' ', '\x85'])
def test_block_text_follows_markdown_it_line_numbers_with_unusual_separators(separator):
    source = f'primero{separator}medio\n\nsegundo parrafo\n\ntercero\n'.encode('utf-8')
    value, blocks, *_ = extractors.markdown(source)
    paragraphs = [block for block in blocks if block['kind'] == 'paragraph']
    assert [block['source_lines'] for block in paragraphs] == [[1, 1], [3, 3], [5, 5]]
    assert [block['text'] for block in paragraphs] == [f'primero{separator}medio', 'segundo parrafo', 'tercero']


def test_markdown_splits_the_source_into_lines_once_not_once_per_block(monkeypatch):
    calls = []

    class Counting(str):
        def splitlines(self, *args, **kwargs):
            calls.append(1)
            return super().splitlines(*args, **kwargs)

    original = extractors.text_content
    monkeypatch.setattr(extractors, 'text_content', lambda data: Counting(original(data)))
    source = '\n\n'.join(f'parrafo {index}' for index in range(300)).encode('utf-8')
    _, blocks, *_ = extractors.markdown(source)
    assert len(blocks) == 300
    assert len(calls) <= 1
