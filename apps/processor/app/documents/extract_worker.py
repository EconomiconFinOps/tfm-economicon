"""Restricted child entry point: no service credentials, no remote inference."""
import json
import os
from pathlib import Path
import sys

from app.documents.extractors import extract
from app.documents.extraction_sandbox import restrict


def main():
    directory = Path(sys.argv[1]).resolve()
    extension = sys.argv[2]
    limits = json.loads((directory / 'limits.json').read_text())
    try:
        try:
            restrict(directory, memory_mb=limits['memory_mb'], seconds=limits['seconds'], output_bytes=80_000_000)
        except Exception:
            (directory / 'output.json').write_text(json.dumps({'ok': False, 'error': 'document_extraction_environment_unavailable'}))
            return
        data = (directory / 'input').read_bytes()
        result = extract(data, extension, directory, limits)
        (directory / 'output.json').write_text(json.dumps({'ok': True, 'document': result}, ensure_ascii=False), encoding='utf-8')
    except Exception as error:
        # Only a closed vocabulary is permitted; never emit parser messages or document bytes.
        safe = str(error) if type(error).__name__ == 'FormatError' else 'document_extraction_failed'
        (directory / 'output.json').write_text(json.dumps({'ok': False, 'error': safe}), encoding='utf-8')


if __name__ == '__main__':
    main()
