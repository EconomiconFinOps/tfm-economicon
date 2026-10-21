import importlib.util
import io
import json
import tarfile
import unittest

from pathlib import Path

spec = importlib.util.spec_from_file_location('plan', Path(__file__).with_name('chat-eval-plan.py'))
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


class TokenizerPlanTests(unittest.TestCase):
    def archive(self, altered=None):
        data = io.BytesIO()
        root = 'apps/processor/app/agents/prompt_resources/jup035/'
        with tarfile.open(fileobj=data, mode='w') as archive:
            for bundle in ('chat/v3', 'summary/v3', 'chat/v4', 'summary/v4'):
                content = (plan.ROOT / (root + bundle + '/manifest.json')).read_bytes()
                if bundle == altered:
                    manifest = json.loads(content)
                    manifest['tokenizer']['sha256'] = '0' * 64
                    content = json.dumps(manifest).encode()
                item = tarfile.TarInfo(root + bundle + '/manifest.json')
                item.size = len(content)
                archive.addfile(item, io.BytesIO(content))
        data.seek(0)
        return tarfile.open(fileobj=data)

    def test_new_plan_pins_native_and_historical_assets(self):
        with self.archive() as archive:
            pins = plan.tokenizer_artifacts(archive)
        root = 'apps/processor/app/agents/prompt_resources/jup035/'
        self.assertEqual(set(pins), {root + 'chat/v4/tokenizer.json', root + 'chat/v2/tokenizer.json'})
        self.assertEqual(pins[root + 'chat/v4/tokenizer.json']['sha256'],
                         'c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b')
        self.assertEqual(pins[root + 'chat/v2/tokenizer.json']['sha256'],
                         '19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d')

    def test_mismatched_active_or_legacy_bundle_is_rejected(self):
        for altered in ('summary/v3', 'summary/v4'):
            with self.subTest(bundle=altered), self.archive(altered) as archive:
                with self.assertRaisesRegex(ValueError, 'tokenizer pins differ'):
                    plan.tokenizer_artifacts(archive)
