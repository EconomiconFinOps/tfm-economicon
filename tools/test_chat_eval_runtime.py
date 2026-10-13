import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('runtime', Path(__file__).with_name('chat-eval-runtime.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'file_hashes': {'apps/backend/app/main.py': 'code',
                     'apps/processor/app/agents/prompt_resources/jup035/chat/v3/system.md': 'prompt',
                     'apps/processor/app/agents/prompt_resources/jup035/chat/v2/tokenizer.json': 'tokenizer'}}
        self.identity = {'id': 'container', 'image': 'immutable-image', 'running': True,
                         'started_at': 'time', 'project': 'isolated-b'}

    def test_backend_verifies_both_code_and_copied_prompt_tokenizer(self):
        paths = r.container_paths(self.plan, 'backend')
        self.assertEqual(set(paths), set(self.plan['file_hashes']))
        self.assertIn('/opt/economicon/chat/v3/tokenizer.json', paths.values())
        calls = []
        def transport(args, data=None):
            calls.append(args)
            return self.identity if args[1] == 'inspect' else self.plan['file_hashes']
        result = r.verify_container(self.plan, 'backend', 'container', 'isolated-b', transport)
        self.assertEqual(result['verified_file_hashes'], self.plan['file_hashes'])
        self.assertEqual([c[1] for c in calls], ['inspect', 'exec', 'inspect'])

    def test_wrong_project_and_modified_code_are_rejected(self):
        for project, hashes in [('other', self.plan['file_hashes']), ('isolated-b', {})]:
            def transport(args, data=None):
                return {**self.identity, 'project': project} if args[1] == 'inspect' else hashes
            with self.assertRaises(ValueError):
                r.verify_container(self.plan, 'backend', 'container', 'isolated-b', transport)

    def test_restart_during_probe_is_rejected(self):
        calls = []
        def transport(args, data=None):
            calls.append(args)
            if args[1] != 'inspect':
                return self.plan['file_hashes']
            return {**self.identity, 'started_at': str(len(calls))}
        with self.assertRaisesRegex(ValueError, 'changed during'):
            r.verify_container(self.plan, 'backend', 'container', 'isolated-b', transport)

    def test_unknown_service_and_path_escape_rejected(self):
        with self.assertRaises(ValueError):
            r.container_paths(self.plan, 'database')
        with self.assertRaises(ValueError):
            r.source_hashes({'file_hashes': {'../outside': 'hash'}}, '.')


if __name__ == '__main__':
    unittest.main()
