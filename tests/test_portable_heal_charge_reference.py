"""Received-healing model contract and observer invariance before shared GPU admission."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,heal_charge_compat
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_heal_charge_cases import fixtures
from portable_heal_charge_contracts import verify
from world_heal_charge_native import observe,plain
class HealChargeReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.answers=[observe(c) for c in cls.cases]
    def test_literal_pool_capacity_lifetime_targets_and_discharge(self):
        self.assertEqual(len(self.cases),29)
        for c,(n,t) in zip(self.cases,self.answers):
            with self.subTest(case=c['name']):verify(c,n)
    def test_cleanse_fixture_marks_the_pool_harmful(self):
        c=next(c for c in self.cases if c['contract']['kind']=='cleanse-discards')
        harmful=[e for e in c['effects'] if e.get('polarity')=='harmful']
        self.assertEqual([e['stat'] for e in harmful],['heal_overcharge_store_atk_pct'])
    def test_no_simulation_or_packing_during_factory(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle')),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):self.assertEqual(fixtures(),self.cases)
    def test_all_native_state_trace_and_rng_preserved(self):
        for c,(n,t) in zip(self.cases,self.answers):
            b=copy.deepcopy(n);b.pop('healing_charge')
            with self.subTest(case=c['name']):self.assertEqual((b,t),plain(c))
    def test_observer_adds_no_queries_or_healing_callbacks(self):
        c=next(c for c in self.cases if c['contract']['kind']=='live-other-pool-receives-release')
        def measured(fn):
            counts={};previous=sys.getprofile();codes={BuffManager.get_buffs.__code__:'buffs',BuffManager.final_atk.__code__:'atk',heal_charge_compat.capacity.__code__:'capacity',heal_charge_compat.collect.__code__:'collect',heal_charge_compat.take.__code__:'take'}
            def profile(f,e,a):
                if previous:previous(f,e,a)
                if e=='call' and f.f_code in codes:counts[codes[f.f_code]]=counts.get(codes[f.f_code],0)+1
            sys.setprofile(profile)
            try:fn(c)
            finally:sys.setprofile(previous)
            return counts
        self.assertEqual(measured(observe),measured(plain))
    def test_contract_rejects_corrupted_pool_take_target_order_and_hp(self):
        c=next(c for c in self.cases if c['contract']['kind']=='ordered-duplicate-recipients');n=self.answers[self.cases.index(c)][0]
        for fault in ('take','targets','hp','done'):
            b=copy.deepcopy(n);events=b['healing_charge']['events']
            if fault=='take':next(e for e in events if e['kind']=='take')['value']+=1
            elif fault=='targets':next(e for e in events if e['kind']=='discharge')['targets']=[1,2]
            elif fault=='hp':b['allies'][1]['hp']+=1
            else:next(e for e in events if e['kind']=='take')['after'][0]['done']=False
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,b)
    def test_shared_gpu_requires_private_world_for_family(self):
        effects={e['stat']:e for c in self.cases for e in c['effects'] if e.get('stat') in ('heal_overcharge_store_atk_pct','accumulate_max_scale_pct','heal_overcharge_discharge')}
        for e in effects.values():
            portable_runtime.validate_effect(e,combat=self.cases[0]['combat'],world_frame=True)
            with self.assertRaises(ValueError):portable_runtime.validate_effect(e,combat=self.cases[0]['combat'],world_frame=False)
    def test_readiness_declares_model_and_keeps_runtime_unverified(self):
        from portable_readiness_semantics import reference_readiness
        for kind,stat,target in [('buff','heal_overcharge_store_atk_pct','self'),('buff','accumulate_max_scale_pct','self'),('instant','heal_overcharge_discharge','all_allies')]:
            r=reference_readiness(dict(phase='effect',kind=kind,stat=stat,target=target));self.assertEqual(r['recorded_cases'],29);self.assertTrue(r['declared_model']);self.assertFalse(r['in_game_rules_verified']);self.assertFalse(r['gpu_supported'])
        self.assertEqual(reference_readiness(dict(phase='effect',kind='buff',stat='accumulate_max_scale_pct',target='boss'))['lane'],'reference_review')
if __name__=='__main__':unittest.main()
