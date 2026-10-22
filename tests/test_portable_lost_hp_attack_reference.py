"""Native live scalar/attack sampling contracts with no packing or GPU."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from portable_lost_hp_attack_cases import fixtures
from portable_lost_hp_attack_contracts import verify
import world_lost_hp_attack_native as observer
from world_parts_skill_native import observe as plain_observe
s=importlib.util.spec_from_file_location('lost_hp_reference_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)

class LostHPAttackReferenceTests(unittest.TestCase):
    def test_down_and_passive_or_preserved_revival_body_contracts(self):
        from portable_lost_hp_attack_revival_cases import fixtures as revival
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('packing forbidden')):
            for case in revival():
                native,_=observer.observe(case)
                with self.subTest(case=case['name']):
                    self.assertTrue(verify(case,native)['verified']);native['allies'][0]['down']=not native['allies'][0]['down']
                    with self.assertRaises(AssertionError):verify(case,native)
    def test_all_literal_contracts_without_packing_or_gpu(self):
        cases=fixtures();self.assertEqual(len(cases),21);before=copy.deepcopy(cases)
        def forbidden(*a,**kw):raise AssertionError('packing/GPU forbidden')
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observer.observe(case)[0])['verified'])
        self.assertEqual(cases,before)
    def test_preserves_all_native_fields_and_trace(self):
        for case in fixtures():
            with self.subTest(case=case['name']):
                plain,trace=plain_observe(case);observed,otrace=observer.observe(case);observed.pop('lost_hp_attack');self.assertEqual(observed,plain);self.assertEqual(otrace,trace)
    def test_faults_in_totals_packets_rate_hp_owner_name_time_scalar_and_count_reject(self):
        case=fixtures()[0];native,_=observer.observe(case)
        for fault in ('total','packet','atk_pct','hp_pct','owner','name','time','scalar-value','scalar-owner','count'):
            altered=copy.deepcopy(native);obs=altered['lost_hp_attack']
            if fault=='total':altered['damage'][0]+=1
            elif fault=='packet':next(x for x in altered['parts_skill_events'] if x['kind']=='packet')['damage']+=1
            elif fault=='name':obs['samples'][0]['name']='wrong-source'
            elif fault=='scalar-value':obs['values'][0]['value']=999
            elif fault=='scalar-owner':obs['values'][0]['owner']=1
            elif fault=='count':obs['samples'].pop()
            else:obs['samples'][0][fault]+=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,altered)
    def test_stack_bypass_parent_snapshot_and_physical_faults_reject(self):
        cases={c['name']:c for c in fixtures()}
        for label in ('stack-count-ignored','parent-snapshot-and-child-refresh','physical-live-hp'):
            case=cases['lost-hp-attack-'+label];native,_=observer.observe(case)
            if label=='stack-count-ignored':
                for q in native['lost_hp_attack']['values']:q['stack']=1
            elif label=='physical-live-hp':native['projectile_shots'][0]['damage']+=1
            else:native['lost_hp_attack']['samples'][1]['atk_pct']=50
            with self.subTest(label=label),self.assertRaises(AssertionError):verify(case,native)
    def test_profile_composes_and_restores_after_failure(self):
        previous=sys.getprofile();calls=[]
        def prior(frame,event,answer):
            if event=='return' and frame.f_code is observer.BuffManager._get_value.__code__:calls.append(event)
        try:
            sys.setprofile(prior);observer.observe(fixtures()[0]);self.assertTrue(calls);self.assertIs(sys.getprofile(),prior)
            with patch.object(observer,'parts_observe',side_effect=RuntimeError('injected failure')):
                with self.assertRaisesRegex(RuntimeError,'injected failure'):observer.observe(fixtures()[0])
            self.assertIs(sys.getprofile(),prior)
        finally:sys.setprofile(previous)

if __name__=='__main__':unittest.main()
