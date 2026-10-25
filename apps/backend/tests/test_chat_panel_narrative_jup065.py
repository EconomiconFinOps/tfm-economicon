import json
from pathlib import Path
import pytest
from app.core.chat_segments import render_segments, validate_narrative_segments

FIXTURE = json.loads((Path(__file__).resolve().parents[3] / 'docs/demo/JUP-065/regresiones-narrativa.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('case', FIXTURE['cases'], ids=lambda c: c['id'])
def test_backend_replays_rehearsal_sentence_spacing(case):
    assert render_segments([{'inference': p} for p in case['parts']], []) == ' '.join(case['parts'])

@pytest.mark.parametrize('text', FIXTURE['unfinished'])
def test_backend_rejects_quote_as_completion(text):
    with pytest.raises(ValueError, match='Incomplete narrative'):
        validate_narrative_segments([{'inference': text}, {'documentary': {'source_id': 'manual', 'passage': 'Coste actual.'}}])
