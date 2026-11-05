"""Authored mechanics must not inherit the oracle actors' catalog reload time."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / d) for d in ('app', 'scripts')]
spec = importlib.util.spec_from_file_location('mode_return_verifier', ROOT / 'scripts/verify-portable-combat.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
from portable_specs import LIMITS


class AuthoredModeReload(unittest.TestCase):
    def test_reload_inheritance_and_explicit_override_without_cpu_execution(self):
        case = next(c for c in verifier.fixtures() if c['name'] == 'finite-timed-mode-stalls-on-empty')
        before = copy.deepcopy(verifier.engine_worker.META)
        for base_reload, explicit, expected in [(0.375, None, 0.375), (0.375, 0.625, 0.625), (None, None, 1.0)]:
            with self.subTest(base_reload=base_reload, explicit=explicit):
                authored = copy.deepcopy(case)
                if base_reload is None:
                    authored['combat']['weapons'][0].pop('reload', None)
                else:
                    authored['combat']['weapons'][0]['reload'] = base_reload
                if explicit is not None:
                    authored['effects'][1]['reload_time'] = explicit
                with patch('calculator.timeline.CharState.tick', side_effect=AssertionError('CPU battle executed during GPU input preparation')):
                    words, _ = verifier.compile_case(authored)
                at = LIMITS['MODE_BASE'] + LIMITS['MODE_WORDS'] + 8
                actual = struct.unpack('<d', struct.pack('<II', *words[at:at + 2]))[0]
                self.assertEqual(actual, expected)
        self.assertEqual(verifier.engine_worker.META, before)


if __name__ == '__main__':
    unittest.main()
