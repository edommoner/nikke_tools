"""Disjoint ownership, unchanged originals and strict opt-in composition."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator.boss_pattern import BossScript,validate
from portable_coordinate_original_cases import prepare_case
from portable_enemy_ammo_self_destruct_cases import fixtures
from portable_enemy_ammo_self_destruct_wire import LAYOUT,compile_battle,check_schema
from portable_enemy_ammo_wire import LAYOUT as E,pack


class CombinedWireTests(unittest.TestCase):
    def test_all_originals_lower_without_runtime_state_and_old_packer_stays_closed(self):
        from portable_coordinate_kind_admission import KindAdmission
        for case in fixtures():
            _,prepared=prepare_case(case);before=copy.deepcopy(prepared)
            with patch.object(BossScript,'begin_frame',side_effect=AssertionError('No CPU schedule in input')):
                words,meta,bindings,_=compile_battle(prepared,case['logical_geometry'],case['enemy_ammo'])
            self.assertEqual(before,prepared);self.assertEqual(len(words),117632);self.assertEqual(len(prepared['effects']),76)
            self.assertFalse(meta['enemy_ammo_declarations']['CPU_state_or_schedule_as_input'])
            self.assertEqual(KindAdmission(ROOT,'gpu/world_enemy_ammo_self_destruct_entry.slang').inspect(words)['unsupported'],[])
            with self.assertRaisesRegex(ValueError,'Self-destruct'):pack(case['enemy_ammo'],validate(case['patterns'],coord=True),bindings)

    def test_ownership_and_stride_are_shared_without_overlap(self):
        from portable_backend import validate_composed_stride
        check_schema(ROOT)
        self.assertEqual(LAYOUT['OUTPUT_BASE'],E['OUTPUT_BASE']+E['RESOURCE_BASE']+(E['RESOURCE_CAPACITY']-128)*8)
        self.assertLessEqual(LAYOUT['OUTPUT_BASE']+LAYOUT['HEADER']+LAYOUT['ROWS']*LAYOUT['ROW_WORDS'],E['OUTPUT_WORDS'])
        validate_composed_stride('gpu/world_enemy_ammo_self_destruct_entry.slang',117632,2032000)
        with self.assertRaises(ValueError):validate_composed_stride('gpu/world_enemy_ammo_self_destruct_entry.slang',116464,2032000)


    def test_full_case_and_raw_rejection_inventory(self):
        spec=importlib.util.spec_from_file_location('combined_wire_verifier',ROOT/'research/verify-enemy-ammo-self-destruct.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);rows,raw=m.prepare()
        self.assertEqual((len(rows),len(raw)),(16,4+16*117632*4))
        self.assertEqual(len({name for name,_,_ in rows}),16)
        for name,words,domain in rows[:8]:
            with self.subTest(case=name):self.assertEqual(len(domain[0]['effects']),76)
        self.assertTrue(all(domain is None for _,_,domain in rows[8:]))


if __name__=='__main__':unittest.main()
