"""Native consumer semantics, observer transparency and closed GPU admission."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_max_ammo_scaling_cases import fixtures
from portable_max_ammo_scaling_contracts import verify
from world_max_ammo_scaling_native import observe,plain

class MaxAmmoScalingReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.answers=[observe(c) for c in cls.cases]
    def test_literal_live_capacity_rounding_lifetime_and_mode_contracts(self):
        for c,(n,t) in zip(self.cases,self.answers):
            with self.subTest(case=c['name']):verify(c,n)
    def test_factory_does_not_run_battle_or_pack(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle')),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):self.assertEqual(fixtures(),self.cases)
    def test_observer_preserves_every_native_field_trace_and_rng(self):
        for c,(n,t) in zip(self.cases,self.answers):
            b=copy.deepcopy(n);b.pop('max_ammo_scaling')
            with self.subTest(case=c['name']):self.assertEqual((b,t),plain(c))
    def test_observer_adds_no_queries_or_lifetime_consumption(self):
        c=next(c for c in self.cases if c['contract']['kind']=='one-bullet-late')
        def measure(fn):
            counts={};previous=sys.getprofile();codes={BuffManager.get_buffs.__code__:'buffs',BuffManager.consume_bullet_buffs.__code__:'consume',BuffManager._scale_by_max_ammo.__code__:'scale'}
            def profile(f,e,a):
                if previous:previous(f,e,a)
                if e=='call' and f.f_code in codes:counts[codes[f.f_code]]=counts.get(codes[f.f_code],0)+1
            sys.setprofile(profile)
            try:fn(c)
            finally:sys.setprofile(previous)
            return counts
        self.assertEqual(measure(observe),measure(plain))
    def test_contract_rejects_wrong_recipient_context_capacity_and_damage(self):
        c=self.cases[0];n=self.answers[0][0]
        for fault in ('recipient','capacity','nested','damage','missing'):
            b=copy.deepcopy(n);o=b['max_ammo_scaling']
            if fault=='recipient':o['capacities'][0]['owner']=4
            elif fault=='capacity':o['capacities'][0]['value']+=1
            elif fault=='nested':next(r for r in o['reads'] if r['recursive'])['value']=0
            elif fault=='damage':b['projectile_shots'][0]['damage']+=1
            else:o['reads'].pop()
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,b)
    def test_missing_provider_recursive_none_and_exception_cleanup(self):
        # Exercise the pinned helper with only its documented provider/guard state.
        class State:pass
        state=State();state.max_ammo_provider=None;state._ammo_query=set()
        call=lambda:BuffManager._scale_by_max_ammo(state,2.5,'recipient',.4)
        self.assertIsNone(call())
        state.max_ammo_provider=lambda n,t:None;self.assertIsNone(call());self.assertEqual(state._ammo_query,set())
        def provider(n,t):
            self.assertEqual((n,t),('recipient',.4));self.assertIsNone(call());return 7
        state.max_ammo_provider=provider;self.assertEqual(call(),17.5);self.assertEqual(state._ammo_query,set())
        def fail(n,t):raise RuntimeError('provider failed')
        state.max_ammo_provider=fail
        with self.assertRaisesRegex(RuntimeError,'provider failed'):call()
        self.assertEqual(state._ammo_query,set())
    def test_unimplemented_gpu_value_source_is_still_rejected(self):
        for c in self.cases:
            eff=next(e for e in c['effects'] if e.get('scaling')=='max_ammo_count')
            with self.assertRaises(ValueError):portable_runtime.validate_effect(eff,combat=c['combat'],world_frame=True)
    def test_readiness_is_native_evidence_not_gpu_certification(self):
        from portable_readiness_semantics import reference_readiness
        issue=dict(phase='effect',kind='buff',stat='charge_dmg_pct',scaling='max_ammo_count',fields=['scaling'],target='self')
        r=reference_readiness(issue);self.assertEqual(r['recorded_cases'],20);self.assertEqual(r['contract_coverage'],'recorded_subset');self.assertFalse(r['gpu_supported'])
        self.assertEqual(reference_readiness(dict(issue,target='boss'))['lane'],'reference_review')

if __name__=='__main__':unittest.main()
