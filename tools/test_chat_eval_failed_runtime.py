from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('recover', Path(__file__).with_name('chat-eval-recover-failed-runtime.py'))
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


def report(identifier, cost):
    return {'attempt_id': identifier, 'attempted_legs': 2, 'requests': [{'phase': 'draft'}, {'phase': 'final'}], 'observed': {'cost_usd': cost}}


class AttemptsTests(unittest.TestCase):
    def test_all_attempt_costs_and_legs_remain_in_accounting(self):
        legs, cost = r.attempt_totals({'attempt_ids': ['a','b']}, {'reports': [report('a','.0073093725'),report('b','.00197904')]})
        self.assertEqual(legs, 4)
        self.assertEqual(cost, Decimal('.0092884125'))

    def test_missing_repeated_or_unrelated_attempt_rejected(self):
        for reports in ([report('a','.1')], [report('a','.1'),report('a','.1')], [report('a','.1'),report('other','.1')]):
            with self.assertRaises(ValueError): r.attempt_totals({'attempt_ids': ['a','b']}, {'reports': reports})

    def test_invalid_cost_and_phase_count_rejected(self):
        for cost in ('NaN', '-1', 'Infinity'):
            with self.assertRaises(ValueError): r.attempt_totals({'attempt_ids': ['a']}, {'reports': [report('a',cost)]})
        bad = report('a','.1');bad['requests'].pop()
        with self.assertRaises(ValueError): r.attempt_totals({'attempt_ids': ['a']}, {'reports': [bad]})


if __name__ == '__main__': unittest.main()
