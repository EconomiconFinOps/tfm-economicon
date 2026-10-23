"""Controller CI is independent of release readiness; deployment remains strict."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import control
import prepare
import runner
from test_control import config


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        source = Path(__file__).parents[2]
        self.recipe = json.loads((source / 'infra/aws-cicd/release.json').read_text())
        # SHA256 of an empty application tree; no acceptance is invented for HEAD.
        self.recipe['application_sha256'] = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        paths = [entry['path'] for entry in self.recipe['evidence'].values()]
        paths += [command[1] for phase in ('bootstrap', 'checks') for command in self.recipe[phase]]
        for name in paths:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        target = self.root / 'infra/aws-cicd/release.json'
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(self.recipe))

    def change_application(self):
        app = self.root / 'apps/backend/main.py'
        app.parent.mkdir(parents=True)
        app.write_text('print("unaccepted application change")\n')

    def test_integrity_survives_application_drift_but_release_validation_rejects_it(self):
        control.validate_recipe_files(self.recipe, self.root)
        self.change_application()
        control.validate_recipe_evidence(self.recipe, self.root)
        with self.assertRaisesRegex(ValueError, 'application tree differs'):
            control.validate_recipe_files(self.recipe, self.root)

    def test_integrity_rejects_modified_missing_and_outside_evidence(self):
        for mode in ('modified', 'missing', 'outside'):
            recipe = copy.deepcopy(self.recipe)
            entry = recipe['evidence']['postgresql']
            path = self.root / entry['path']
            original = path.read_bytes()
            with self.subTest(mode=mode):
                if mode == 'modified':
                    path.write_bytes(original + b'changed')
                elif mode == 'missing':
                    path.unlink()
                else:
                    entry['path'] = '../outside.md'
                try:
                    with self.assertRaises(ValueError):
                        control.validate_recipe_evidence(recipe, self.root)
                finally:
                    path.write_bytes(original)

    def test_integrity_rejects_missing_and_invalid_release_scripts(self):
        path = self.root / self.recipe['bootstrap'][0][1]
        path.unlink()
        with self.assertRaises(ValueError):
            control.validate_recipe_evidence(self.recipe, self.root)
        path.write_text('def invalid syntax\n')
        with self.assertRaises(SyntaxError):
            control.validate_recipe_evidence(self.recipe, self.root)

    def test_prepare_reports_application_drift_as_not_deployable(self):
        with patch.object(prepare, 'ROOT', self.root):
            before = prepare.prepare(config(), self.root / '.work/before', 'a' * 40)
            self.assertTrue(before['aws_deployable'])
            self.change_application()
            after = prepare.prepare(config(), self.root / '.work/after', 'a' * 40)
        self.assertFalse(after['aws_deployable'])
        self.assertIn('Release evidence: Release evidence application tree differs', after['blockers'])
        self.assertFalse(after['aws_resources_created'])

    def test_runner_rejects_stale_recipe_before_any_cloud_operation(self):
        item = object.__new__(runner.Runner)
        item.config = config()
        self.change_application()
        with patch.object(runner, 'ROOT', self.root), patch.object(
                item, 'aws', side_effect=AssertionError('Unexpected AWS call')):
            with self.assertRaisesRegex(ValueError, 'application tree differs'):
                item.recipe()
