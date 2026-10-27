"""Every original definition/weapon survives; extended histories own their banks."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('original_lock_suite',ROOT/'research/verify-original-lock-composition.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class OriginalLocks(unittest.TestCase):
    def test_all_original_definitions_and_static_weapon_controls_survive(self):
        from portable_heavyarms_lock_cases import source_definitions,NAME
        from portable_heavyarms_original_composition import prepare_case
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No native battle in packing')):
            c,p=prepare_case(3,3);before=copy.deepcopy(c);w,m,b=suite.compile_case(c)
        self.assertEqual(c,before);self.assertEqual(len(c['effects']),91)
        self.assertEqual(set(m['binding_source_indices']),set(range(91)))
        owned=[e for e,o in zip(c['effects'],c['owners']) if c['names'][o]==NAME]
        for e in source_definitions():self.assertIn(e,owned)
        self.assertEqual(c['controls'],[char['control'] for char in p['chars']])
        self.assertEqual(c['original_run']['prepared']['chars'],p['chars'])
        self.assertEqual(len(w),109536)
    def test_extended_banks_are_disjoint_and_unowned_tail_is_rejected(self):
        from portable_original_lock_layout import BASE,PULSES,PACKETS,END,OUTPUT,PULSE_CAPACITY,PACKET_CAPACITY,banks_and_project
        from portable_packet_fates import END as old_end
        self.assertEqual(BASE,old_end);self.assertEqual(PACKETS,PULSES+PULSE_CAPACITY*16);self.assertEqual(END,PACKETS+PACKET_CAPACITY*16);self.assertLess(END,OUTPUT)
        n=dict(lock_pulses=[],lock_packet_trace=[])
        for pos in (PULSES,PACKETS,END,OUTPUT-1):
            b=[0]*OUTPUT;b[pos]=1
            with self.subTest(pos=pos),self.assertRaisesRegex(AssertionError,'padding|tail'):banks_and_project(b,n)
    def test_exact_source_inverse_preserves_every_shared_dependency(self):
        from portable_original_lock_source_contract import project_sources
        d=json.loads((ROOT/'tests/fixtures/portable-original-lock-source-delta.json').read_text());old=project_sources(ROOT)
        for name,row in d['sources'].items():
            self.assertEqual(old[name],row['baseline'])
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n// mutation'})
    def test_actual_30s_native_history_requires_extension_without_omitting_rows(self):
        from portable_heavyarms_original_composition import prepare_case
        c,_=prepare_case(30,0);w,m,b=suite.compile_case(c);n=suite.native_reference((c,m,b))
        self.assertEqual(n['original_input_identity']['definitions'],91)
        self.assertGreater(len(n['lock_pulses']),63);self.assertGreater(len(n['lock_packet_trace']),38)
        self.assertLessEqual(len(n['skill_trace']),128)
        self.assertEqual(len(n['receipt_fates']),len(n['skill_trace']))
        self.assertTrue(n['typed']['attacks'])
if __name__=='__main__':unittest.main()
