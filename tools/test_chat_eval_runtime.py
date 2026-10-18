import importlib.util
import copy
import hashlib
import json
from pathlib import Path
import tempfile
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

    def generated_plan(self):
        result=copy.deepcopy(self.plan)
        result['file_hashes'].pop(r.TOKENIZER)
        result['file_hashes'][r.TOKENIZER_BUILDER]='builder'
        result['generated_artifacts']={r.TOKENIZER:{'sha256':'a'*64,'revision':'b'*40,'bytes':17}}
        return result

    def test_generated_tokenizer_is_verified_in_both_runtime_locations(self):
        plan=self.generated_plan()
        for service,target in [('backend','/opt/economicon/chat/v3/tokenizer.json'),
                               ('processor','/app/app/agents/prompt_resources/jup035/chat/v2/tokenizer.json')]:
            with self.subTest(service=service):
                requested=[]
                expected={**plan['file_hashes'],r.TOKENIZER:'a'*64}
                def transport(args,data=None):
                    if args[1]=='inspect':return self.identity
                    paths=json.loads(data);requested.append(paths)
                    return {key:expected[key] for key in paths}
                result=r.verify_container(plan,service,'container','isolated-b',transport)
                self.assertEqual(requested[0][r.TOKENIZER],target)
                self.assertEqual(result['verified_file_hashes'][r.TOKENIZER],'a'*64)
                # A matching build helper/source manifest never excuses a wrong
                # generated asset in the running container.
                def changed(args,data=None):
                    result=transport(args,data)
                    if args[1]!='inspect':result[r.TOKENIZER]='c'*64
                    return result
                with self.assertRaisesRegex(ValueError,'differs'):
                    r.verify_container(plan,service,'container','isolated-b',changed)

    def test_new_builder_plan_cannot_omit_its_generated_asset(self):
        plan=self.generated_plan();plan.pop('generated_artifacts')
        with self.assertRaisesRegex(ValueError,'generated runtime artifact'):
            r.container_paths(plan,'backend')

    def test_generated_metadata_never_admits_arbitrary_paths_or_ambiguous_identity(self):
        for patch in ('unknown','duplicate','no-builder','bad-hash','bad-revision','bad-size'):
            with self.subTest(patch=patch):
                plan=self.generated_plan()
                if patch=='unknown':plan['generated_artifacts']['../../secret']=plan['generated_artifacts'][r.TOKENIZER]
                elif patch=='duplicate':plan['file_hashes'][r.TOKENIZER]='a'*64
                elif patch=='no-builder':plan['file_hashes'].pop(r.TOKENIZER_BUILDER)
                else:plan['generated_artifacts'][r.TOKENIZER][{'bad-hash':'sha256','bad-revision':'revision','bad-size':'bytes'}[patch]]=None
                with self.assertRaises(ValueError):r.container_paths(plan,'backend')

    def test_source_archive_does_not_require_the_generated_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);file=root/r.TOKENIZER_BUILDER
            file.parent.mkdir(parents=True);file.write_bytes(b'fixed build helper')
            plan=self.generated_plan();plan['file_hashes']={r.TOKENIZER_BUILDER:hashlib.sha256(file.read_bytes()).hexdigest()}
            self.assertFalse((root/r.TOKENIZER).exists())
            self.assertEqual(r.source_hashes(plan,root),plan['file_hashes'])


if __name__ == '__main__':
    unittest.main()
