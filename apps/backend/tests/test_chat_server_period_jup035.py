import pytest


def record(start='2026-09-01', end='2026-10-01'):
    return {'dataset': 0, 'record': {'period': {'start_date': start, 'end_date': end, 'timezone': 'UTC'}}}


def test_period_comes_only_from_unambiguous_verified_records():
    from app.services.chat_context import verified_response_period
    expected = {'from': '2026-09-01', 'to': '2026-10-01'}
    assert verified_response_period([]) is None
    assert verified_response_period([record()]) == expected
    assert verified_response_period([record(), record()]) == expected
    assert verified_response_period([record(), record('2026-08-01')]) is None
    with pytest.raises(ValueError):
        verified_response_period([record('2026-10-01', '2026-10-01')])
    with pytest.raises(ValueError):
        verified_response_period([{'record': {'period': {'start_date':'2026-09-01','end_date':'2026-10-01','timezone':'Europe/Madrid'}}}])


def test_backend_rejects_period_different_from_frozen_context():
    from app.schemas.chat import validate_response
    response = {'schema_version':'1.0','status':'no_data','answer':'No data',
        'scope':{'cloud':'azure','data_environment':'simulated','subscription_ids':[], 'period':None},
        'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}
    assert validate_response(response, [], expected_period=None) == response
    with pytest.raises(ValueError):
        validate_response(response, [], expected_period={'from':'2026-09-01','to':'2026-10-01'})
