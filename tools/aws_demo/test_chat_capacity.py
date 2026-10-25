"""Reject the rehearsal's observed startup failure before any AWS operation."""
import ast
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import control

ROOT = Path(__file__).resolve().parents[2]


def runtime_capacity(value):
    # Execute the real, pure configuration reader without importing the ASGI app
    # or constructing clients. This catches drift between the gate and runtime.
    path = ROOT / 'apps/processor/app/chat.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'configured_capacity')
    module = ast.Module(body=[function], type_ignores=[])
    namespace = {'os': os, 'StartupError': ValueError}
    exec(compile(module, str(path), 'exec'), namespace)
    with patch.dict(os.environ, {'CHAT_MAX_ACTIVE': value}):
        return namespace['configured_capacity']()


class RecipeChatCapacityTests(unittest.TestCase):
    def setUp(self):
        self.recipe = json.loads((ROOT / 'infra/aws-cicd/release.json').read_text())

    def test_versioned_recipe_matches_actual_runtime_capacity(self):
        values = []
        for component in ('backend', 'processor'):
            environment = self.recipe['application_environment'][component]
            try:
                values.append(runtime_capacity(environment.get('CHAT_MAX_ACTIVE', '8')))
            except ValueError:
                self.fail('The versioned AWS recipe is rejected by the chat startup contract: ' + component)
        self.assertEqual(values[0], values[1])

    def test_invalid_enabled_capacity_is_rejected_by_preflight(self):
        for component in ('backend', 'processor'):
            for value in ('2', '4', '9', '', ' ', '5.0', '05', '+5', 'text'):
                recipe = copy.deepcopy(self.recipe)
                for name in ('backend', 'processor'):
                    recipe['application_environment'][name]['CHAT_MAX_ACTIVE'] = '5'
                recipe['application_environment'][component]['CHAT_MAX_ACTIVE'] = value
                with self.subTest(component=component, value=value), self.assertRaisesRegex(ValueError, 'Chat capacity'):
                    control.validate_recipe(recipe)

    def test_supported_capacities_match_runtime_and_preflight(self):
        for value in ('5', '6', '7', '8', ' 5 '):
            recipe = copy.deepcopy(self.recipe)
            for component in ('backend', 'processor'):
                recipe['application_environment'][component]['CHAT_MAX_ACTIVE'] = value
            with self.subTest(value=value):
                control.validate_recipe(recipe)
                self.assertEqual(runtime_capacity(value), int(value))

    def test_omitted_capacity_uses_the_runtime_default(self):
        for component in ('backend', 'processor'):
            self.recipe['application_environment'][component].pop('CHAT_MAX_ACTIVE', None)
        control.validate_recipe(self.recipe)

    def test_backend_and_processor_must_agree_when_chat_enabled(self):
        self.recipe['application_environment']['backend']['CHAT_MAX_ACTIVE'] = '5'
        self.recipe['application_environment']['processor']['CHAT_MAX_ACTIVE'] = '8'
        with self.assertRaisesRegex(ValueError, 'Chat capacity'):
            control.validate_recipe(self.recipe)

    def test_disabled_chat_does_not_validate_unused_capacity(self):
        for component in ('backend', 'processor'):
            self.recipe['application_environment'][component].update(CHAT_ENABLED='false', CHAT_MAX_ACTIVE='unused')
        control.validate_recipe(self.recipe)
