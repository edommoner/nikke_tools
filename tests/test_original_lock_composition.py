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
        from portable_charge_control_specs import WORDS
        self.assertEqual(m['_control_policy'],w[suite.L['WORLD_CONTROL_INPUT_BASE']:suite.L['WORLD_CONTROL_INPUT_BASE']+WORDS])
    def test_extended_banks_are_disjoint_and_unowned_tail_is_rejected(self):
        from portable_original_lock_layout import BASE,PULSES,PACKETS,END,OUTPUT,PULSE_CAPACITY,PACKET_CAPACITY,QUOTAS,QUOTA_CAPACITY,FRACTIONS,FRACTION_CAPACITY,TEAMS,TEAM_CAPACITY,banks_and_project
        from portable_packet_fates import END as old_end
        self.assertEqual(BASE,old_end);self.assertEqual(PACKETS,PULSES+PULSE_CAPACITY*16);self.assertEqual(QUOTAS,PACKETS+PACKET_CAPACITY*16);self.assertEqual(FRACTIONS,QUOTAS+QUOTA_CAPACITY*20);self.assertEqual(TEAMS,FRACTIONS+FRACTION_CAPACITY*8);self.assertEqual(END,TEAMS+TEAM_CAPACITY*8);self.assertLess(END,OUTPUT)
        n=dict(lock_pulses=[],lock_packet_trace=[],target_count_shots=[],battle=dict(fractional_hits=[],team_hits=[]))
        for pos in (PULSES,PACKETS,QUOTAS,FRACTIONS,TEAMS,END,OUTPUT-1):
            b=[0]*OUTPUT;b[pos]=1
            with self.subTest(pos=pos),self.assertRaisesRegex(AssertionError,'padding|tail'):banks_and_project(b,n)
    def test_native_budget_refuses_overflow_before_gpu_and_keeps_scope_explicit(self):
        from portable_original_lock_layout import history_budget
        n=dict(lock_pulses=[],lock_packet_trace=[],target_count_shots=[],lock_shots=[],skill_trace=[],receipt_fates=[],typed=dict(attacks=[]),battle=dict(fractional_hits=[],team_hits=[],projectile_shots=[],reload_events=[],enemy_spawn_notifications=[],manual_control=dict(notifications=[],arbitration=[])))
        self.assertEqual(len(history_budget(n)),13)
        for key,capacity in [('lock_pulses',256),('lock_packet_trace',512),('target_count_shots',2048),('skill_trace',128)]:
            bad=copy.deepcopy(n);bad[key]=[None]*(capacity+1)
            with self.subTest(history=key),self.assertRaisesRegex(ValueError,'exceeds declared capacity'):history_budget(bad)
        for key,capacity in [('fractional_hits',8192),('team_hits',4096)]:
            bad=copy.deepcopy(n);bad['battle'][key]=[None]*(capacity+1)
            with self.subTest(history=key),self.assertRaisesRegex(ValueError,'exceeds declared capacity'):history_budget(bad)

    def test_shared_cli_cache_profile_requires_paired_resident_generation(self):
        import nikke_gpu as cli
        normal=cli.SUITES['original-lock-composition'];cached=cli.SUITES['original-lock-composition-cache-only']
        for key in ('script','source','golden','inputs','native','input_words','output_words'):self.assertEqual(normal[key],cached[key])
        self.assertFalse(normal['development_only']);self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1');self.assertIs(cached['require_paired_generation'],True)

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
        self.assertGreater(len(n['target_count_shots']),100)
        self.assertLessEqual(len(n['target_count_shots']),2048)
        self.assertGreater(len(n['battle']['fractional_hits']),2048)
        self.assertGreater(len(n['battle']['team_hits']),1024)
if __name__=='__main__':unittest.main()
