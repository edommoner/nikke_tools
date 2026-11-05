"""Physical reach contracts from native execution, plus exact source-delta faults."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_physical_interrupt_cases import fixtures
from portable_parts_skill_contracts import verify as verify_native
from world_parts_skill_native import observe
from portable_physical_interrupt_contract import verify_sources,baseline_event,baseline_phase
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
    def test_exact_sampling_hook_flags_and_metadata_bank_faults_reject(self):
        for name,old,new in [('gpu/event_runtime.slang','w.pellets)),WORLD_PACKET_NORMAL','w.muzzles)),WORLD_PACKET_NORMAL'),('gpu/weapon_frame_phases.slang','coefficient,when,damageValue','coefficient,when,ONE+damageValue'),('gpu/counter_landing_runtime.slang','storeNumber(out+4,damageFromFactors','storeNumber(out+6,damageFromFactors'),('gpu/damage_runtime.slang','sampledFlags=flags','sampledFlags=0')]:
            source=(ROOT/name).read_text();self.assertIn(old,source);changed=source.replace(old,new,1)
            with self.subTest(name=name),self.assertRaises(AssertionError):verify_sources(ROOT,{name:changed})
            if name.endswith('event_runtime.slang'):
                with self.assertRaises(AssertionError):baseline_event(ROOT,changed)
            if name.endswith('weapon_frame_phases.slang'):
                with self.assertRaises(AssertionError):baseline_phase(ROOT,changed)
