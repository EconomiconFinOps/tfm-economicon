import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('campaign', Path(__file__).with_name('chat-eval-campaign-runtime.py'))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


def result(code=0, output=''):
    return SimpleNamespace(returncode=code, stdout=output)


class CampaignTests(unittest.TestCase):
    def test_additional_plan_requires_audited_step(self):
        with patch.object(c.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                c.main(Path('/isolated'), additional_plans=[Path('/candidate.json')])
        run.assert_not_called()

    def test_additional_plan_reaches_coverage_check(self):
        with patch.object(c.subprocess, 'run', side_effect=[result(), result(), result(output='{"state":"COLLECTED"}')]) as run, patch('builtins.print'):
            c.main(Path('/isolated'), covered_step=True, additional_plans=[Path('/candidate.json')])
        self.assertEqual(run.call_args.args[0][-2:], ['--additional-plan', str(Path('/candidate.json'))])

    def test_reconciliation_failure_prevents_dispatch(self):
        with patch.object(c.subprocess, 'run', side_effect=[result(), result(1)]) as run, patch('builtins.print'):
            c.main(Path('/isolated'))
        self.assertEqual(run.call_count, 2)
        self.assertFalse(any('live-step.py' in str(call) for call in run.call_args_list))

    def test_completed_campaign_stops_without_more_dispatch(self):
        with patch.object(c.subprocess, 'run', side_effect=[result(), result(), result(output='{"state":"COLLECTED"}')]) as run, patch('builtins.print'):
            c.main(Path('/isolated'))
        self.assertEqual(run.call_count, 3)

    def test_observation_continues_only_after_both_reconciliations(self):
        responses = [result(), result(), result(output='{"state":"OBSERVING"}'),
                     result(), result(1)]
        with patch.object(c.subprocess, 'run', side_effect=responses) as run, patch.object(c.time, 'sleep') as sleep, patch('builtins.print'):
            c.main(Path('/isolated'))
        self.assertEqual(run.call_count, 5)
        sleep.assert_called_once_with(10)


if __name__ == '__main__': unittest.main()
