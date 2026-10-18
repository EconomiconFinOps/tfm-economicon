"""Backend probe for the page rule of structured citations."""
from app.services.citations import structured_location


def test_page_is_not_claimed_when_unannotated_text_sits_between_two_annotated_spans():
    document = 'AAAAA UNKNOWN BBBBB'
    metadata = {'source_spans': [{'normalized_range': [0, 5], 'original': {'page': 1}},
                                 {'normalized_range': [14, 19], 'original': {'page': 1}}],
                'primary_spans': [{'normalized_range': [0, 19], 'content_range': [0, 19]}], 'section_path': None}
    assert structured_location(metadata, {}, document)['page'] is None


def test_page_is_published_when_every_visible_character_is_annotated_on_it():
    document = 'AAAAA BBBBB'
    metadata = {'source_spans': [{'normalized_range': [0, 5], 'original': {'page': 2}},
                                 {'normalized_range': [6, 11], 'original': {'page': 2}}],
                'primary_spans': [{'normalized_range': [0, 11], 'content_range': [0, 11]}], 'section_path': None}
    assert structured_location(metadata, {}, document)['page'] == 2
