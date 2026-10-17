import pytest
from app.services.retrieval_policy import anchors_match, contains_literal, lexical_eligible, query_policy, fuse


@pytest.mark.parametrize('literal,negative', [('cost > 20 EUR', 'cost >= 20 EUR'), ('20', '200'),
    ('EUR', 'EURO'), ('JUP-125', 'JUP-1250'), ('cost <= 20', 'cost < 20')])
def test_complete_literal_tokens_prevent_substring_contradictions(literal, negative):
    assert contains_literal('Before ' + literal + ' after', literal)
    assert not contains_literal(negative, literal)


def test_lexical_requires_discriminating_anchor_and_all_context_terms():
    assert lexical_eligible('JUP-125 storage', query_policy('JUP-125 storage'))
    assert not lexical_eligible('JUP-125 compute', query_policy('JUP-125 storage'))
    assert not lexical_eligible('storage cost 20', query_policy('storage cost 20'))
    assert not lexical_eligible('storage cost 20.5', query_policy('storage cost 20.5'))
    assert not lexical_eligible('JUP-125 JUP-124', query_policy('JUP-125 vs JUP-124'))


@pytest.mark.parametrize('expression', ['utilization > 20%', 'utilization > 20 %',
                                        'utilization > 20.5%', 'utilization > 20,5 %'])
def test_unquoted_percentage_keeps_its_unit_in_both_admission_lanes(expression):
    policy = query_policy(expression)
    assert policy['anchors'] == [expression] and policy['rescue']
    assert lexical_eligible(expression, policy) and anchors_match(expression, policy)
    for contradictory in ['utilization > 20 USD', 'utilization > 20',
                          'utilization >= 20%', 'utilization > 200%', 'utilization > 20.50%']:
        assert not lexical_eligible(contradictory, policy)
        assert not anchors_match(contradictory, policy)


def test_rrf_ranks_start_at_one_missing_lane_zero_and_stable_ties():
    a = {'revision_id': 'r', 'chunk_id': 'a', 'distance': .1, 'lexical_score': .2}
    b = {'revision_id': 'r', 'chunk_id': 'b', 'distance': .2, 'lexical_score': .3}
    result = fuse([a, b], [b, a])
    assert [item['chunk_id'] for item in result] == ['a', 'b']
    assert result[0]['rrf_score'] == 1/61 + 1/62
    assert fuse([a], [])[0]['rrf_score'] == 1/61
