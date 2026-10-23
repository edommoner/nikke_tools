"""Named-enemy native routing and transparent observation before GPU admission."""
import copy,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,detail_gpu
from calculator import timeline
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript
from portable_named_enemy_cases import fixtures
from portable_named_enemy_contracts import verify
from world_named_enemy_native import observe,plain
from portable_readiness_semantics import reference_readiness

class NamedEnemyReferenceTests(unittest.TestCase):
    def test23_literal_native_contracts_without_gpu_or_portable_packing(self):
        def no(*a,**kw):raise AssertionError('Packing/GPU forbidden')
        with patch.object(timeline,'simulate',no):cases=fixtures()
        self.assertEqual(len(cases),23);before=copy.deepcopy(cases);checks=0
        with patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no),patch.object(portable_runtime,'compile_program',no),patch.object(detail_gpu,'compile_effects',no):
            for c in cases:
                with self.subTest(case=c['name']):checks+=verify(c,observe(c)[0])['membership_checks']
        self.assertEqual(checks,628);self.assertEqual(cases,before)

    def test_entire_battle_trace_rng_and_native_query_call_counts_preserved(self):
        for c in fixtures():
            def measured(fn):
                with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'enemy_has_state',autospec=True,side_effect=BuffManager.enemy_has_state) as has,patch.object(BuffManager,'_by_name',autospec=True,side_effect=BuffManager._by_name) as named,patch.object(BossScript,'_ranked',autospec=True,side_effect=BossScript._ranked) as rank,patch.object(BuffManager,'_resolve_enemies',autospec=True,side_effect=BuffManager._resolve_enemies) as resolve,patch.object(random,'sample',side_effect=random.sample) as sample:
                    result=fn(c);return result,(get.call_count,has.call_count,named.call_count,rank.call_count,resolve.call_count,sample.call_count),random.getstate()
            with self.subTest(case=c['name']):
                (n,t),counts,state=measured(observe);n.pop('named_enemy');(p,trace),old,previous=measured(plain);self.assertEqual((n,t,counts,state),(p,trace,old,previous))

    def test_faults_in_name_pool_order_ownership_fallback_lifetime_and_count_rejected(self):
        c=fixtures()[3];native=observe(c)[0]
        for fault in ('name','pool','presence','order','count','owner','recipient','time','rng','allied'):
            n=copy.deepcopy(native);o=n['named_enemy'];r=o['rankings'][0]
            if fault=='name':r['checks'][0]['name']='different'
            elif fault=='pool':r['checks'].reverse()
            elif fault=='presence':r['checks'][0]['present']=False
            elif fault=='order':r['order'].reverse()
            elif fault=='count':o['rankings'].pop()
            elif fault=='owner':r['owner']=4
            elif fault=='recipient':o['recipients'][0]['picked']=[]
            elif fault=='time':o['recipients'][0]['time']=1
            elif fault=='rng':n['rng']['draws']=1
            else:n['named_state']['allied_carriers']=[dict(name='misclassified')]
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,n)
        c=next(c for c in fixtures() if c['name'].endswith('reopened-same-id-drops-mark'));n=observe(c)[0];n['named_enemy']['rankings'][1]['checks'][1]['present']=True
        with self.assertRaises(AssertionError):verify(c,n)
        c=fixtures()[0];n=observe(c)[0];n['named_enemy']['rankings'][0]['order']=[]
        with self.assertRaises(AssertionError):verify(c,n)

    def test_gpu_rejection_remains_and_routing_has_only_recorded_native_scope(self):
        from portable_reference import REFERENCES
        self.assertIn('named-enemy',REFERENCES)
        for c in fixtures():
            with self.subTest(case=c['name']),self.assertRaises(ValueError):portable_runtime.validate_effect(c['effects'][-1],combat={},world_frame=True)
        rows=[dict(kind='buff',stat='received_dmg_pct'),dict(kind='damage',stat='bonus_damage'),dict(kind='instant',stat='named_buff_duration_extend'),dict(kind='damage',stat='sequential_damage:ref')]
        for row in rows:
            issue=dict(phase='effect',category='recipient',target='enemies_with_buff:mark',**row);r=reference_readiness(issue)
            self.assertEqual(r['lane'],'native_contract_extension');self.assertEqual(r['recorded_cases'],23);self.assertEqual(r['reference_suites'],['named-enemy'])
            for flag in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertFalse(r[flag])
            self.assertEqual(reference_readiness(dict(issue,fields=['unproven']))['lane'],'reference_review')
        self.assertEqual(reference_readiness(dict(phase='effect',category='recipient',kind='instant',stat='ammo_charge_pct',target='enemies_with_buff:mark'))['lane'],'reference_review')

if __name__=='__main__':unittest.main()
