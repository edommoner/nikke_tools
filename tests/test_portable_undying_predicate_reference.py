"""Independent native contracts and transparent live-marker observation."""
from cpu_reference_guard import forbid_execution
import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_undying_predicate_cases import fixtures
from portable_undying_predicate_contracts import verify
from world_undying_predicate_native import observe,plain_observe


class UndyingPredicateReferenceTests(unittest.TestCase):
    pass

    def test_native_fields_trace_and_live_query_count_preserved(self):
        original=BuffManager.has_live_stat
        for case in fixtures():
            counts=[]
            def counted(*args,**kwargs):counts[-1]+=1;return original(*args,**kwargs)
            with self.subTest(case=case['name']),patch.object(BuffManager,'has_live_stat',counted):
                counts.append(0);plain,trace=plain_observe(case)
                counts.append(0);native,recorded=observe(case)
                native.pop('undying_predicate');self.assertEqual(native,plain);self.assertEqual(recorded,trace);self.assertEqual(counts[0],counts[1])

    def test_wrong_scope_order_values_or_physical_result_rejected(self):
        case=fixtures()[1];native,_=observe(case)
        for fault in ('result','query','owner','stat','time','stack','damage','total','ammo'):
            n=copy.deepcopy(native);obs=n['undying_predicate']
            if fault=='result':obs['checks'][0]['result']=False
            elif fault=='query':obs['checks'][0]['queries'][0]['result']=False
            elif fault=='owner':obs['checks'][0]['owner']=4
            elif fault=='stat':obs['checks'][0]['queries'][0]['stat']='invincible'
            elif fault=='time':obs['checks'][0]['time']=10
            elif fault=='stack':obs['carriers'][0]['stack']=2
            elif fault=='damage':n['projectile_shots'][0]['damage']+=1
            elif fault=='total':n['damage'][0]+=1
            else:n['ammo'][0]-=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,n)

    def test_literal_contracts_without_packing_or_gpu(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No factory battle')):cases=fixtures()
        self.assertEqual(len(cases),22);before=copy.deepcopy(cases)
        with forbid_execution(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')),patch.object(detail_gpu,'compile_effects',side_effect=AssertionError('No legacy packing')):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_complete_makima_inputs_and_live_observer_are_transparent(self):
        from portable_undying_predicate_roster_cases import fixtures as real_cases
        from portable_undying_predicate_roster_contracts import verify as real_verify
        from world_undying_predicate_roster_native import observe as real_observe,plain_observe as real_plain
        with forbid_execution(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):
            for case in real_cases():
                n,t=real_observe(case);self.assertTrue(real_verify(case,n)['verified']);n.pop('undying_predicate_roster');plain,trace=real_plain(case);self.assertEqual(n,plain);self.assertEqual(t,trace)






if __name__=='__main__':unittest.main()
