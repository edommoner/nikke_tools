"""Native named completion and carrier contracts before private GPU admission."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime
from calculator import timeline
from portable_projectile_chain_cases import fixtures
from portable_projectile_chain_contracts import verify
from world_projectile_chain_native import observe,plain
class ProjectileChainReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.answers=[observe(c) for c in cls.cases]
    def test_literal_packet_notice_and_buff_carrier_contracts(self):
        self.assertEqual(len(self.cases),26)
        for c,(n,t) in zip(self.cases,self.answers):
            with self.subTest(case=c['name']):verify(c,n)
    def test_complete_battle_trace_rng_unchanged(self):
        for c,(n,t) in zip(self.cases,self.answers):
            bare=copy.deepcopy(n);bare.pop('projectile_chain')
            with self.subTest(case=c['name']):self.assertEqual((bare,t),plain(c))
    def test_factory_performs_no_simulation_or_gpu_packing(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No simulation')),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):self.assertEqual(fixtures(),self.cases)
    def test_existing_native_weapon_reader_is_still_pinned(self):
        from portable_skill_weapon_contract import verify as weapon
        self.assertFalse(weapon(ROOT)['effect_local_weapon_override'])
    def test_faults_in_quantity_carrier_state_or_notice_identity_are_rejected(self):
        for kind,fault in (('plain','quantity'),('buff-kind-enemy-carrier','stack'),('nested-handler-order','name'),('matching-normal-MG-annotation','weapon')):
            c=next(c for c in self.cases if c['contract']['kind']==kind);n=copy.deepcopy(self.answers[self.cases.index(c)][0]);d=n['projectile_chain']
            if fault=='quantity':next(e for e in d['events'] if e['kind']=='packet')['amount']+=1
            elif fault=='stack':d['final_carriers'][0]['stack']=1
            elif fault=='name':next(e for e in d['events'] if e['kind']=='weapon-hit')['name']='wrong'
            else:next(e for e in d['events'] if e['kind']=='handler')['current_weapon']='RL'
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,n)
    def test_observer_adds_no_semantic_queries_or_notifications(self):
        from calculator.buff_manager import BuffManager
        c=next(c for c in self.cases if c['contract']['kind']=='nested-handler-order');codes={getattr(BuffManager,k).__code__:k for k in ('get_buffs','_get_value','_by_stat','notify')}
        def measure(fn):
            counts={};old=sys.getprofile()
            def profile(frame,event,value):
                if old:old(frame,event,value)
                if event=='call' and frame.f_code in codes:counts[codes[frame.f_code]]=counts.get(codes[frame.f_code],0)+1
            sys.setprofile(profile)
            try:fn(c)
            finally:sys.setprofile(old)
            return counts
        self.assertEqual(measure(observe),measure(plain))
    def test_pinned_handler_and_buff_instant_producers(self):
        from portable_projectile_chain_contract import verify as sources
        r=sources(ROOT);self.assertTrue(r['buff_kind_uses_regular_activation']);self.assertEqual(r['weapon_hit_producers'],1)
    def test_readiness_routes_confirmed_producers_without_changing_admission(self):
        from portable_readiness_semantics import reference_readiness
        issues=[dict(phase='effect',category='trigger',kind='damage',stat='projectile_explosion_damage',target='target',scaling=None,operator=dict(domain='timing',descriptor='weapon_hit:source: 부착 ')),dict(phase='effect',category='effect',kind='buff',stat='buff_stack_add',target='target',scaling=None),dict(phase='effect',category='fields',kind='damage',stat='projectile_attachment_damage',target='target',scaling=None,fields=['weapon_type'])]
        for issue in issues:
            r=reference_readiness(issue);self.assertEqual(r['recorded_cases'],26);self.assertFalse(r['gpu_supported']);self.assertFalse(r['gpu_admission_verified'])
        self.assertEqual(reference_readiness(issues[0])['lane'],'gpu_lowering_candidate')
        self.assertEqual(reference_readiness(issues[2])['lane'],'native_contract_extension')
        empty=dict(issues[0],operator=dict(domain='timing',descriptor='weapon_hit:'));self.assertEqual(reference_readiness(empty)['lane'],'reference_review');self.assertEqual(reference_readiness(dict(issues[0],operator=None))['lane'],'reference_review')
    def test_weapon_completion_timing_stays_closed_before_shared_adapter(self):
        c=self.cases[0]
        with self.assertRaises(ValueError):portable_runtime.validate_effect(c['effects'][-1],combat=c['combat'],world_frame=True)
if __name__=='__main__':unittest.main()
