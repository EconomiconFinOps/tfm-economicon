import json
import pytest
from app.core.chat_segments import bind_segments, render_response, render_segments, quote_choices
from app.clients.chat_stream_parser import SegmentAnswerJSON

RECORDS=[{'id':'0','equation':'73 − 20 = 53','value':'53','unit':'','hypothetical':True}]

@pytest.mark.parametrize('size',[1,2,7,8192])
def test_segment_stream_matches_render_with_split_escapes_surrogates(size):
    segments=[{'text':'Resultado "😀": '},{'calculation_id':'0'},{'text':'. Fin.'}]
    raw=json.dumps({'evidence':[],'answer':segments,'next_actions':[]},ensure_ascii=True)
    parser=SegmentAnswerJSON(RECORDS)
    streamed=''.join(parser.feed(raw[i:i+size]) for i in range(0,len(raw),size))
    assert streamed==parser.finish()==render_segments(segments,RECORDS)

@pytest.mark.parametrize('segments',[
    [{'text':'1 +'}, {'text':' 1 = 3'}],
    [{'text':'[[ca'}, {'text':'lc:999]]'}],
    [{'calculation_id':'99'}], [{'calculation_id':0}],
    [{'text':'hello','calculation_id':'0'}], [],
    [{'text':'a'}]*129, [{'text':'a'*4001}],
    [{'text':'500 EUR - 100 EUR = 100 EUR'}],
])
def test_invalid_segments_fail_both_render_and_stream(segments):
    with pytest.raises(ValueError):render_segments(segments,RECORDS)
    parser=SegmentAnswerJSON(RECORDS)
    with pytest.raises(ValueError):
        parser.feed(json.dumps({'answer':segments}));parser.finish()

def test_duplicate_segment_keys_and_surrogate_rejected():
    for raw in ['{"answer":[{"text":"a","text":"b"}]}',
                '{"answer":[{"text":"\\ud800x"}]}',
                '{"answer":[{"text":"a"}],"answer":[{"text":"b"}]}']:
        with pytest.raises(ValueError):SegmentAnswerJSON(RECORDS).feed(raw)

def test_public_lengths_and_no_calculation_branch():
    from app.agents.schemas import chat_provider_schema
    schema=chat_provider_schema(authorized_evidence=[],calculations=[])
    assert len(schema['properties']['answer']['items']['anyOf'])==1
    with pytest.raises(ValueError):render_segments([{'calculation_id':'0'}],[])
    value={'answer':[{'text':'ok'}], 'assumptions':[[{'text':'a'*501}]],'limitations':[],'next_actions':[]}
    with pytest.raises(ValueError):render_response(value,[])

def test_quotes_are_exact_nonoverlapping_source_windows():
    content='á'*2048+'😀'*17
    assert quote_choices(content)==[content[:2048],content[2048:]]
    assert ''.join(quote_choices(content))==content
    assert quote_choices('A'*2048+'  ')==['A'*2048]


def test_escaped_emoji_limit_counts_decoded_characters():
    segments=[{'text':'😀'*4000}]
    parser=SegmentAnswerJSON([])
    assert parser.feed(json.dumps({'answer':segments},ensure_ascii=True))=='😀'*4000
    assert parser.finish()==render_segments(segments,[])


@pytest.mark.parametrize('width',[1,7,8192])
def test_public_whitespace_normalization_preserves_internal_separators(width):
    segments=[{'text':'  Hola '},{'text':' mundo '},{'calculation_id':'0'},{'text':' !  '}]
    raw=json.dumps({'answer':segments})
    parser=SegmentAnswerJSON(RECORDS)
    stream=''.join(parser.feed(raw[i:i+width]) for i in range(0,len(raw),width))
    assert stream==parser.finish()==render_segments(segments,RECORDS)=='Hola  mundo 73 − 20 = 53 !'


@pytest.mark.parametrize('segments',[[{'text':''}],[{'text':' '},{'text':'\n'}]])
def test_empty_public_result_is_rejected(segments):
    with pytest.raises(ValueError):render_segments(segments,[])
    parser=SegmentAnswerJSON([])
    with pytest.raises(ValueError):parser.feed(json.dumps({'answer':segments}));parser.finish()
