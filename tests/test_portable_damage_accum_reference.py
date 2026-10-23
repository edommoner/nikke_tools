"""Literal boss-damage accumulation contracts and observer invariance."""
import copy,sys,unittest,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,damage_accum_runtime
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_damage_accum_cases import fixtures
from portable_damage_accum_contracts import verify
from world_damage_accum_native import observe,plain
class DamageAccumReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.answers=[observe(c) for c in cls.cases]
    def test_literal_quantities_rates_caps_archive_and_emission(self):
        self.assertEqual(len(self.cases),52)
        for c,(n,t) in zip(self.cases,self.answers):
            with self.subTest(case=c['name']):verify(c,n)
    def test_complete_battle_trace_and_rng_are_unchanged(self):
        for c,(n,t) in zip(self.cases,self.answers):
            baseline=copy.deepcopy(n);baseline.pop('damage_accumulation')
            with self.subTest(case=c['name']):self.assertEqual((baseline,t),plain(c))
    def test_factory_does_not_simulate_or_pack_runtime_values(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle')),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No GPU packing')):self.assertEqual(fixtures(),self.cases)
    def test_observer_adds_no_buff_queries_rate_reads_or_callbacks(self):
        c=next(c for c in self.cases if c['contract']['kind']=='all-pools-full-before-notices')
        codes={getattr(BuffManager,k).__code__:k for k in ('get_buffs','_get_value','_by_stat','final_atk','accumulate_damage','_accum_rate','accum_discharge','notify')}
        def measure(fn):
            counts={};previous=sys.getprofile()
            def profile(frame,event,value):
                if previous:previous(frame,event,value)
                if event=='call' and frame.f_code in codes:counts[codes[frame.f_code]]=counts.get(codes[frame.f_code],0)+1
            sys.setprofile(profile)
            try:fn(c)
            finally:sys.setprofile(previous)
            return counts
        self.assertEqual(measure(observe),measure(plain))
    def test_faults_in_taken_amount_emission_cap_and_full_queue_rejected(self):
        for kind,fault in (('dealt-default','take'),('negative-cap','cap'),('split-only-and-int-truncation','emission'),('all-pools-full-before-notices','done'),('all-pools-full-before-notices','order')):
            c=next(c for c in self.cases if c['contract']['kind']==kind);n=copy.deepcopy(self.answers[self.cases.index(c)][0]);events=n['damage_accumulation']['events']
            if fault=='take':next(e for e in events if e['kind']=='take')['value']+=1
            elif fault=='emission':next(e for e in events if e['kind']=='emission')['amount']+=1
            elif fault=='done':next(e for e in events if e['kind']=='full-notice')['before']['pools'][1]['done']=False
            elif fault=='order':next(e for e in events if e['kind']=='full-notice')['name']='second'
            else:
                for e in events:
                    if 'after' in e:
                        for p in e['after']['pools']:p['base']=0
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,n)
    def test_new_gpu_family_requires_private_combat_world(self):
        c=self.cases[0]
        for e in (c['effects'][1],self.cases[5]['effects'][2],c['effects'][-1]):
            with self.subTest(stat=e['stat']):
                portable_runtime.validate_effect(e,combat=c['combat'],world_frame=True)
                with self.assertRaises(ValueError):portable_runtime.validate_effect(e,combat=c['combat'],world_frame=False)
    def test_unported_enemy_carriers_and_allied_carriers_are_observed_separately(self):
        c=next(c for c in self.cases if c['contract']['kind']=='active-consume-once');n=self.answers[self.cases.index(c)][0]
        self.assertTrue(n['named_state']['enemy_memberships']);self.assertNotIn('pool',[p['name'] for p in n['named_state']['allied_carriers']])
        c=next(c for c in self.cases if c['contract']['kind']=='pool-target-does-not-filter-damage');n=self.answers[self.cases.index(c)][0]
        self.assertIn('pool',[p['name'] for p in n['named_state']['allied_carriers']])
    def test_readiness_keeps_scoped_metal_evidence_separate_from_full_support(self):
        from portable_readiness_semantics import reference_readiness
        for kind,stat in [('buff','dmg_accum_dealt_atk_pct'),('buff','dmg_accum_received_atk_pct'),('buff','dmg_accum_rate_pct'),('damage','accum_split_damage')]:
            issue=dict(phase='effect',kind=kind,stat=stat,target='target',scaling=None);r=reference_readiness(issue)
            self.assertEqual(r['lane'],'native_contract_extension');self.assertEqual(r['recorded_cases'],52);self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified']);self.assertFalse(r['in_game_rules_verified'])
            self.assertEqual(r['scoped_metal_validation']['inputs'],460);self.assertTrue(r['scoped_metal_validation']['independently_audited']);self.assertEqual(r['followup_metal_validation']['inputs'],4)
            self.assertEqual(reference_readiness(dict(issue,fields=['weapon_type']))['lane'],'reference_review')
    def test_installed_native_activation_uses_shared_lifecycle(self):
        from effect_runtime import CATALOG
        self.assertIs(CATALOG.handlers['damage_accumulation'].activate,damage_accum_runtime.activate)
    def test_prior_metal143_source_files_are_exactly_preserved(self):
        from portable_backend import source_hashes
        golden=json.loads((ROOT/'research/portable-world-heal-charge-lifetime-short-expected.json').read_text())
        from portable_damage_accum_source_contract import project_sources
        import hashlib
        projected=project_sources(ROOT)
        self.assertEqual({name:hashlib.sha256(projected.get(name,(ROOT/name).read_text()).encode()).hexdigest() for name in golden['source_sha256']},golden['source_sha256'])
if __name__=='__main__':unittest.main()
