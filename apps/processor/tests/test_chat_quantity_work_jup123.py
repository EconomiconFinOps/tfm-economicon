"""Candidate work is bounded before semantic analysis, even for repeated values."""
import pytest
import subprocess
import sys
from pathlib import Path

from app.core.chat_expressions import MAX_MATCHES, quantities


@pytest.mark.parametrize('explicit_only', [False, True])
@pytest.mark.parametrize('entry', ['1 ', 'one ', 'uno ', 'a: 1 ', 'coste: 100 EUR; ',
                                 '999999999999999 EUR; ', '0.1234567890123 EUR; '])
def test_candidate_limit_counts_repeated_and_rejected_values(entry, explicit_only):
    # Rejected candidates must consume work too; limiting result cardinality alone
    # leaves repeated values and invalid magnitudes unbounded.
    assert quantities(entry * (MAX_MATCHES + 1), explicit_only=explicit_only) == {}


@pytest.mark.parametrize('count', [511, 512])
def test_boundary_keeps_admitted_repeated_values(count):
    assert quantities('1 ' * count) == {'1': {
        'value': '1', 'unit': '', 'source': '1', 'binding': 'bare', 'concept_anchors': []}}
    assert set(quantities('coste: 100 EUR; ' * count, explicit_only=True)) == {'100 EUR'}


def test_flood_returns_no_partial_catalog():
    assert quantities('1 ' * 513) == {}
    assert quantities('Coste 100 EUR; ' + 'one ' * MAX_MATCHES) == {}
    assert len(quantities(' '.join(str(i) for i in range(128)))) == 128
    assert quantities(' '.join(str(i) for i in range(129))) == {}


@pytest.mark.parametrize('size', [0, 1, 50, 200])
def test_whitespace_preserves_prefixes_and_concept_anchors(size):
    gap=' ' * size
    assert set(quantities('EUR'+gap+':'+gap+'10')) == {'10 EUR'}
    assert quantities('waste:'+gap+'10 EUR')['10 EUR']['concept_anchors'] == [['waste']]
    assert set(quantities('EUR'+gap+'X 1')) == {'1'}


def test_single_candidate_with_adversarial_whitespace_is_bounded():
    # Run away from pytest's process: the old ambiguous regex takes many seconds
    # on one candidate. A removed bound must fail this test, not hang the suite.
    app=Path(__file__).resolve().parents[1]
    code="""import sys
sys.path.insert(0,sys.argv[1])
from app.core.chat_expressions import quantities
for text in [prefix+' '*16000+'X 1' for prefix in ['EUR ', 'coste ', 'a: EUR ']]+['\\n '*8000+'? 1', '\\n '*6000+'? '+'1 '*512]:
    assert len(text)<=16384
    assert set(quantities(text))=={'1'}
"""
    result=subprocess.run([sys.executable,'-I','-S','-B','-c',code,str(app)],
                          text=True,capture_output=True,timeout=3)
    assert result.returncode==0,result.stderr
