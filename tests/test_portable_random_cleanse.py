"""Native selection/cleanse witnesses and transparent observation contracts."""
import copy,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,portable_backend,detail_gpu
from calculator.buff_manager import BuffManager
from portable_random_cleanse_cases import fixtures
from portable_random_cleanse_contracts import verify
from world_random_cleanse_native import observe,plain
from portable_readiness_semantics import reference_readiness


class RandomCleanseTests(unittest.TestCase):
    def test18_native_contracts_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),18)
        def no(*a,**kw):raise AssertionError('No packing or GPU')
        with patch.object(portable_runtime,'compile_program',no),patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no),patch.object(detail_gpu,'compile_effects',no):
            for c in cases:
                with self.subTest(case=c['name']):self.assertTrue(verify(c,observe(c)[0])['verified'])
        self.assertEqual(before,cases)

    def test_native_battle_trace_random_and_query_counts_unchanged(self):
        for c in fixtures():
            def measured(fn):
                with patch.object(random,'sample',side_effect=random.sample) as sample,patch.object(BuffManager,'_resolve_target_raw',autospec=True,side_effect=BuffManager._resolve_target_raw) as resolve,patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'_has_harmful',autospec=True,side_effect=BuffManager._has_harmful) as harmful:
                    result=fn(c);return result,(sample.call_count,resolve.call_count,get.call_count,harmful.call_count),random.getstate()
            with self.subTest(case=c['name']):
                (n,t),counts,state=measured(observe);n.pop('random_cleanse');(p,trace),old,previous=measured(plain)
                self.assertEqual((n,t,counts,state),(p,trace,old,previous))

    def test_pool_self_exclusion_rng_limit_and_membership_faults_rejected(self):
        c=fixtures()[7];base=observe(c)[0]
        for fault in ('pool','picked','k','rng','before_rng','after_rng','owner','before','after','count','boss'):
            n=copy.deepcopy(base);o=n['random_cleanse'];s=o['samples'][0];call=o['calls'][0]
            if fault=='pool':s['pool']=s['pool'][1:]
            elif fault=='picked':s['picked']=[1,4]
            elif fault=='k':s['k']=1
            elif fault=='rng':s['state_changed']=False
            elif fault=='before_rng':s['before_index']=0
            elif fault=='after_rng':s['after_index']=624
            elif fault=='owner':call['owner']=4
            elif fault=='before':call['before']['first'].pop()
            elif fault=='after':call['after']['second']=[1,2,3]
            elif fault=='count':o['calls'].append(copy.deepcopy(call))
            else:n['rng']['draws']=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,n)
        c=fixtures()[3];n=observe(c)[0];n['random_cleanse']['calls'][0]['after'].pop('locked')
        with self.assertRaises(AssertionError):verify(c,n)

    def test_gpu_remains_rejected_and_readiness_is_only_recorded_scope(self):
        from portable_reference import REFERENCES
        self.assertIn('random-cleanse',REFERENCES)
        c=fixtures()[0];effect=c['effects'][-1]
        with self.assertRaises(ValueError):portable_runtime.validate_effect(effect,combat={},world_frame=True)
        issue=dict(phase='effect',category='recipient',kind='instant',stat='debuff_cleanse',target='allies_random_with_debuff:2')
        r=reference_readiness(issue);self.assertEqual(r['reference_suites'],['random-cleanse']);self.assertEqual(r['recorded_cases'],18)
        self.assertEqual(r['lane'],'native_contract_extension')
        for k in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertFalse(r[k])
        for extra in (dict(target='allies_random_with_debuff:3'),dict(fields=['future']),dict(scaling='stack_count'),dict(kind='buff')):
            self.assertEqual(reference_readiness(dict(issue,**extra))['lane'],'reference_review')

if __name__=='__main__':unittest.main()
