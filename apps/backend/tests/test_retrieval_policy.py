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



@pytest.mark.parametrize('comparison', ['> -20%', '> +20%', '> 20e3%', '> .20%', '> 20.5.1%', '> 20..5%', '> 20,,5%', '> 20.,5%', '> 20. .5%', '> 20 , ,5%'])
def test_unsupported_comparison_closes_rescue_even_with_identifier(comparison):
    policy=query_policy('JUP-125 utilization '+comparison)
    assert 'JUP-125' in policy['anchors'] and not policy['rescue']
    assert not lexical_eligible('JUP-125 utilization >= 200 USD',policy)


@pytest.mark.parametrize('expression', ['cost > 20 EUR','utilization >= 20 %','latency <= 20 ms','limit = 20 GB'])
def test_supported_comparison_with_identifier_preserves_all_literals(expression):
    question='JUP-125 '+expression
    policy=query_policy(question)
    assert policy['rescue'] and lexical_eligible(question,policy)
    assert not lexical_eligible(question.replace('20','200'),policy)
    assert not lexical_eligible(question.replace('JUP-125','JUP-1250'),policy)



@pytest.mark.parametrize('question,wrong', [
    ('JUP-125 cost > 20 EUR.', 'JUP-125 cost > 20 USD with EUR'),
    ('JUP-125 utilization >= 20 %.', 'JUP-125 utilization >= 20 USD'),
])
def test_terminal_punctuation_cannot_backtrack_and_drop_complete_unit(question, wrong):
    policy=query_policy(question)
    assert policy['rescue'] and lexical_eligible(question,policy)
    assert len(policy['anchors'])==2 and policy['anchors'][1]==question.removeprefix('JUP-125 ').removesuffix('.')
    assert not lexical_eligible(wrong,policy) and not anchors_match(wrong,policy)

@pytest.mark.parametrize('content,anchor', [
    ('rg-prod-01', 'RG-PROD-01'),
    ('Compa\u00f1\u00eda', 'Compan\u0303i\u0301a'),
    ('STRASSE', 'Stra\u00dfe'),
])
def test_literal_anchors_normalize_unicode_and_case_without_substring_rescue(content, anchor):
    assert contains_literal(content, anchor)
    assert not contains_literal(content + '0', anchor)
