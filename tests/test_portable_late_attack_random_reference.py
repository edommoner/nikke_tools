"""The observer preserves native calls; contracts detect cache, RNG and membership faults."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/p) for p in ('app', 'research', 'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from portable_late_attack_random_cases import fixtures
from portable_late_attack_random_contracts import verify
from world_late_attack_random_native import observe, plain_observe


class LateAttackRandomReferenceTests(unittest.TestCase):
    def test_observer_preserves_full_native_result_trace_and_call_count(self):
        getter = BuffManager.get_buffs
        for case in fixtures():
            counts = [0]
            def counted(*args, **kwargs):
                counts[-1] += 1
                return getter(*args, **kwargs)
            with self.subTest(case=case['name']), patch.object(BuffManager, 'get_buffs', counted):
                plain, trace = plain_observe(case)
                counts.append(0)
                actual, recorded = observe(case)
                self.assertTrue(verify(case, actual)['verified'])
                actual.pop('late_attack_random')
                self.assertEqual(actual, plain)
                self.assertEqual(recorded, trace)
                self.assertEqual(counts, [248, 248])

    def test_contract_detects_membership_cache_and_rng_faults(self):
        case = fixtures()[0]
        native, _ = observe(case)
        for kind in ('hit', 'sample', 'state', 'lazy', 'damage'):
            bad = copy.deepcopy(native)
            obs = bad['late_attack_random']
            if kind == 'hit':
                next(q for q in obs['queries'] if q['hit'])['sample_indices'] = [0]
            elif kind == 'sample':
                obs['samples'][0]['picked'] = [4]
            elif kind == 'state':
                obs['samples'][0]['after_sha256'] = '0'*64
            elif kind == 'lazy':
                obs['samples'][1]['lazy'] = True
            else:
                bad['projectile_shots'][0]['damage'] += 1
            with self.subTest(kind=kind), self.assertRaises(AssertionError):
                verify(case, bad)


if __name__ == '__main__':
    unittest.main()
