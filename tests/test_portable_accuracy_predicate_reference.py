"""Strict numeric predicate contracts before shared host/GPU admission."""
from cpu_reference_guard import forbid_execution
import copy,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_accuracy_predicate_cases import fixtures
from portable_accuracy_predicate_contracts import verify
from world_accuracy_predicate_native import observe,plain_observe


class AccuracyPredicateReferenceTests(unittest.TestCase):
    pass

    def test_all_native_fields_trace_and_buff_query_count_are_preserved(self):
        original=BuffManager.get_buffs
        for case in fixtures():
            counts=[]
            def counted(*a,**kw):counts[-1]+=1;return original(*a,**kw)
            with self.subTest(case['name']),patch.object(BuffManager,'get_buffs',counted):
                counts.append(0);plain,trace=plain_observe(case)
                counts.append(0);native,recorded=observe(case)
                native.pop('accuracy_predicate');self.assertEqual(native,plain);self.assertEqual(recorded,trace)
                self.assertEqual(counts[0],counts[1])

    def test_wrong_condition_value_owner_order_damage_stack_or_ammo_reject(self):
        case=fixtures()[1];native,_=observe(case)
        for fault in ('result','value','owner','target','time','stack','damage','total','ammo'):
            changed=copy.deepcopy(native);obs=changed['accuracy_predicate']
            if fault=='result':obs['checks'][0]['result']=False
            elif fault=='value':obs['checks'][0]['queries'][0]['value']=0
            elif fault=='owner':obs['checks'][0]['owner']=4
            elif fault=='target':obs['checks'][0]['queries'][0]['target']='wrong'
            elif fault=='time':obs['checks'][0]['time']=10
            elif fault=='stack':obs['carriers'][0]['stack']=2
            elif fault=='damage':changed['projectile_shots'][0]['damage']+=1
            elif fault=='total':changed['damage'][0]+=1
            else:changed['ammo'][0]-=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,changed)




    def test_shared_host_admission_preserves_accuracy_condition(self):
        effect=fixtures()[1]['effects'][-1];before=copy.deepcopy(effect)
        portable_runtime.validate_effect(effect,combat={},world_frame=True)
        self.assertEqual(effect,before)

    def test_twenty_six_literal_contracts_without_packing_or_gpu(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No factory battle')):cases=fixtures()
        self.assertEqual(len(cases),26);before=copy.deepcopy(cases)
        with forbid_execution(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')),patch.object(detail_gpu,'compile_effects',side_effect=AssertionError('No legacy packing')):
            for case in cases:
                with self.subTest(case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_whole_original_profile_contract_and_transparent_observation(self):
        from portable_accuracy_predicate_roster_cases import fixtures as real_fixtures
        from world_accuracy_predicate_roster_native import observe as real_observe,plain_observe as real_plain
        from portable_accuracy_predicate_roster_contracts import verify as real_verify
        with forbid_execution(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):
            for case in real_fixtures():
                native,trace=real_observe(case);self.assertTrue(real_verify(case,native)['verified'])
                native.pop('accuracy_predicate_roster');plain,other=real_plain(case);self.assertEqual(native,plain);self.assertEqual(trace,other)




if __name__=='__main__':unittest.main()
