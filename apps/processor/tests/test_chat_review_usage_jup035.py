"""Two-phase usage must preserve observations without claiming missing totals."""
from decimal import Decimal

import pytest

from app.core.chat_review import review_usage


FIRST = {'prompt_tokens': 100, 'completion_tokens': 20, 'total_tokens': 120,
         'cost_usd': '0.0031'}
SECOND = {'prompt_tokens': 140, 'completion_tokens': 40, 'total_tokens': 180,
          'cost_usd': '0.0042'}


def test_complete_legs_sum_both_requests_without_rounding_cost():
    report = review_usage([FIRST, SECOND], attempted_legs=2)
    assert report['complete'] is True
    assert report['attempted_legs'] == report['reported_legs'] == 2
    assert {key: report['observed'][key] for key in
            ('prompt_tokens', 'completion_tokens', 'total_tokens')} == {
                'prompt_tokens': 240, 'completion_tokens': 60, 'total_tokens': 300}
    assert Decimal(report['observed']['cost_usd']) == Decimal('0.0073')


@pytest.mark.parametrize('legs', ([None, FIRST], [FIRST, None]))
def test_missing_leg_keeps_observed_usage_but_never_claims_complete_total(legs):
    report = review_usage(legs, attempted_legs=2)
    assert report['observed'] == FIRST
    assert report['complete'] is False
    assert report['attempted_legs'] == 2 and report['reported_legs'] == 1


def test_partial_fields_are_preserved_independently():
    report = review_usage([{'prompt_tokens': 11}, {'completion_tokens': 7}], attempted_legs=2)
    assert report['observed'] == {'prompt_tokens': 11, 'completion_tokens': 7}
    assert report['complete'] is False
    assert report['reported_legs'] == 2


def test_missing_cost_does_not_turn_into_zero_or_a_complete_usage_report():
    without_cost = {key: value for key, value in FIRST.items() if key != 'cost_usd'}
    report = review_usage([without_cost], attempted_legs=1)
    assert report['observed'] == without_cost
    assert report['complete'] is False
    assert report['attempted_legs'] == report['reported_legs'] == 1


def test_no_reports_does_not_invent_zero_usage():
    report = review_usage([None, None], attempted_legs=2)
    assert report == {'observed': {}, 'complete': False,
                      'attempted_legs': 2, 'reported_legs': 0}


def test_failure_before_final_admission_keeps_first_leg_complete():
    report = review_usage([FIRST], attempted_legs=1)
    assert report == {'observed': FIRST, 'complete': True,
                      'attempted_legs': 1, 'reported_legs': 1}


def test_final_admitted_without_report_keeps_first_leg_partial():
    report = review_usage([FIRST], attempted_legs=2)
    assert report['observed'] == FIRST
    assert report['complete'] is False
    assert report['attempted_legs'] == 2 and report['reported_legs'] == 1
