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


from pathlib import Path
from app.core.chat_segments import validate_narrative_segments
REHEARSAL = json.loads((Path(__file__).resolve().parents[3] / 'docs/demo/JUP-065/regresiones-narrativa.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('case', REHEARSAL['cases'], ids=lambda case: case['id'])
def test_rehearsal_sentence_boundaries_render_and_stream(case):
    segments = [{'inference': part} for part in case['parts']]
    expected = 'Interpretación: ' + ' '.join(case['parts'])
    assert render_segments(segments, []) == expected
    raw = json.dumps({'basis': 'authorized_evidence', 'answer': segments})
    for size in (1, 7, len(raw)):
        parser = SegmentAnswerJSON([])
        emitted = ''.join(parser.feed(raw[i:i+size]) for i in range(0, len(raw), size))
        assert parser.finish() == expected
        assert emitted == expected

@pytest.mark.parametrize('text', REHEARSAL['unfinished'])
def test_rehearsal_transition_must_not_be_completed_by_a_quote(text):
    for tail in ([], [{'documentary': {'source_id': 'manual', 'passage': 'El actual cost se aproxima a la facturacion.'}}]):
        with pytest.raises(ValueError, match='Incomplete narrative'):
            validate_narrative_segments([{'inference': text}, *tail])
    parser = SegmentAnswerJSON([])
    with pytest.raises(ValueError, match='Incomplete narrative'):
        parser.feed(json.dumps({'basis': 'authorized_evidence', 'answer': [{'inference': text}]}))
        parser.finish()

@pytest.mark.parametrize(('parts', 'expected'), [
    (['Una frase. ', 'Otra frase.'], 'Una frase. Otra frase.'),
    (['Una frase.\n', 'Otra frase.'], 'Una frase.\nOtra frase.'),
    (['¿Falta contexto?', 'Ámbito desconocido.'], '¿Falta contexto? Ámbito desconocido.'),
    (['desco', 'nocido.'], 'desconocido.'),
])
def test_join_preserves_existing_whitespace_and_partial_words(parts, expected):
    assert render_segments([{'inference': text} for text in parts], []) == 'Interpretación: ' + expected


def test_complete_prose_keeps_documentary_passage_literal_in_stream():
    from app.core.chat_expressions import quantities, ExpressionRenderer
    from app.core.chat_rules import QuantityCatalog
    catalog = QuantityCatalog({})
    passage = 'El **actual cost** se aproxima a la vista de facturacion.'
    catalog.authorized_sources = [{'id': 'manual', 'kind': 'corpus', 'title': 'Manual', 'source': 'corpus', 'content': passage}]
    segments = [{'inference': 'La vista actual corresponde a facturación.'},
                {'documentary': {'source_id': 'manual', 'passage': passage}}]
    expected = render_segments(segments, [], expressions=ExpressionRenderer(catalog))
    parser = SegmentAnswerJSON([], quantities=catalog)
    parser.feed(json.dumps({'basis': 'authorized_evidence', 'answer': segments}))
    assert parser.finish() == expected
    assert passage in expected
    for transition in REHEARSAL['unfinished']:
        parser = SegmentAnswerJSON([], quantities=catalog)
        with pytest.raises(ValueError, match='Incomplete narrative'):
            parser.feed(json.dumps({'basis': 'authorized_evidence', 'answer': [{'inference': transition}, segments[1]]}))
            parser.finish()


def test_inserted_space_counts_towards_public_limit():
    segments = [{'inference': 'A.'}, {'inference': 'B.'}]
    with pytest.raises(ValueError, match='Rendered text limit'):
        render_segments(segments, [], limit=len('\nInterpretación: A.B.\n'))
