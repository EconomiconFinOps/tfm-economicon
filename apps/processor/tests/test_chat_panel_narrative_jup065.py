"""Reproduce the missing numeric slots observed in the real JUP-065 rehearsal."""
import json
import pytest
from app.core.chat_segments import render_segments
from app.clients.chat_stream_parser import SegmentAnswerJSON


@pytest.mark.parametrize('text', [
    'El gasto total del período es ',
    'El aumento de septiembre frente a agosto es de ',
    'Networking aparece con ',
    ' EUR, seguido de Database con ',
])
def test_unfinished_narrative_cannot_be_confirmed(text):
    segments = [{'inference': text}]
    with pytest.raises(ValueError, match='Incomplete narrative'):
        render_segments(segments, [])
    parser = SegmentAnswerJSON([])
    with pytest.raises(ValueError, match='Incomplete narrative'):
        parser.feed(json.dumps({'basis': 'missing_data', 'answer': segments}))
        parser.finish()


def test_typed_calculation_may_complete_a_sentence():
    records = [{'id': '0', 'equation': '73 − 20 = 53'}]
    value = render_segments([{'inference': 'La diferencia es '},
                             {'calculation_id': '0'}, {'inference': '. Fin.'}], records)
    assert '73 − 20 = 53' in value


def test_complete_clarification_remains_usable():
    assert 'Indica período y ámbito.' in render_segments([
        {'inference': 'Indica período y ámbito.'}], [])


def test_documentary_quote_is_not_a_numeric_continuation():
    with pytest.raises(ValueError, match='Incomplete narrative'):
        render_segments([{'inference': 'El aumento es de '},
                         {'documentary': {'source_id': 'manual', 'passage': 'Revisar costes.'}}], [])


def test_adjacent_prose_can_complete_a_sentence_without_inventing_a_quantity():
    assert 'El período es desconocido.' in render_segments([
        {'inference': 'El período es '}, {'inference': 'desconocido.'}], [])
