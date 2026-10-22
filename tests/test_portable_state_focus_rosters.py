"""Whole-profile fixtures must retain original effects and native battle behavior."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/p) for p in ('app', 'research', 'scripts')]
import engine_worker
import portable_backend
from calculator import timeline
from portable_state_focus_roster_cases import fixtures


def adapter():
    spec = importlib.util.spec_from_file_location(
        'state_focus_roster_test', ROOT/'research/verify-world-state-focus-rosters-short.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class StateFocusRosterTests(unittest.TestCase):
    def test_packing_preserves_complete_profiles_without_battle_or_gpu(self):
        module = adapter()
        def forbidden(*args, **kwargs):
            raise AssertionError('Static roster packing must not run battle/GPU')
        with patch.object(timeline, 'simulate', forbidden), patch.object(portable_backend, 'execute', forbidden):
            entries, data = module.prepare()
        self.assertEqual(len(entries), 6)
        self.assertEqual(len(data), 4 + sum(len(words)*4 for _, words, _ in entries))
        self.assertEqual([len(domain[1]['effects']) for _, _, domain in entries], [70, 70, 79, 79, 68, 68])
        for _, _, (case, prepared, words, metadata) in entries:
            original = engine_worker.evaluate(dict(copy.deepcopy(case['body']), _portable_static_inputs=True))
            self.assertEqual(prepared['effects'], original['effects'])
            self.assertEqual(len(metadata['effects']), len(original['effects']))
            self.assertEqual(case['body']['profile']['chars'][case['character']]['favorite_stage'], 0)

    def test_original_full_profile_native_contracts(self):
        module = adapter()
        for case, shots in zip(fixtures(), (85, 770, 85, 795, 155, 1422), strict=True):
            with self.subTest(case=case['name']):
                before = copy.deepcopy(case)
                native, trace = module.suite.inspect_native(case)
                self.assertEqual(len(trace), shots)
                self.assertEqual(case, before)
                self.assertTrue(native)


if __name__ == '__main__':
    unittest.main()
