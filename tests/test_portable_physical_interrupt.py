"""Physical reach contracts from native execution, and strict current wire validation."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_physical_interrupt_cases import fixtures
from portable_parts_skill_contracts import verify as verify_native
from world_parts_skill_native import observe
import portable_backend

class PhysicalInterruptTests(unittest.TestCase):
    def test_literal_physical_contracts_require_no_gpu_or_packing(self):
        with patch.object(portable_backend,'build',side_effect=AssertionError('No GPU')),patch.object(portable_backend,'execute',side_effect=AssertionError('No GPU')):
            for c in fixtures():
                with self.subTest(case=c['name']):
                    native,_=observe(c);self.assertTrue(verify_native(c,native)['verified'])
    def test_charge_literals_match_native_down_charge_cadence(self):
        for c in fixtures():
            w=c['combat']['weapons'][0]
            if w['mode']=='charge':
                self.assertEqual(c['weapon_metadata']['fire_stance_hold'],0)
                self.assertEqual(w['min_cycle'],w['interval'])
                self.assertEqual(c['post_fire_delays'][0],0)

    def test_snapshot_range_and_integer_contracts_are_distinct(self):
        cases={c['name']:c for c in fixtures()}
        self.assertEqual(cases['interrupt-weapon-scatter-two-muzzles']['contract']['interrupt_damage'][0],4002)
        self.assertEqual(cases['interrupt-weapon-scatter-child-snapshot']['contract']['interrupt_damage'][0],19998)
        self.assertNotEqual(cases['interrupt-weapon-range-at-threshold']['contract']['damage'],cases['interrupt-weapon-range-before-threshold']['contract']['damage'])
