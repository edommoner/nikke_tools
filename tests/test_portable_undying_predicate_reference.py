"""Independent native contracts and transparent live-marker observation."""
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
from portable_readiness_semantics import reference_readiness
s=importlib.util.spec_from_file_location('undying_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class UndyingPredicateReferenceTests(unittest.TestCase):
    def test_literal_contracts_without_packing_or_gpu(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No factory battle')):cases=fixtures()
        self.assertEqual(len(cases),22);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')),patch.object(detail_gpu,'compile_effects',side_effect=AssertionError('No legacy packing')):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

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

    def test_complete_makima_inputs_and_live_observer_are_transparent(self):
        from portable_undying_predicate_roster_cases import fixtures as real_cases
        from portable_undying_predicate_roster_contracts import verify as real_verify
        from world_undying_predicate_roster_native import observe as real_observe,plain_observe as real_plain
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):
            for case in real_cases():
                n,t=real_observe(case);self.assertTrue(real_verify(case,n)['verified']);n.pop('undying_predicate_roster');plain,trace=real_plain(case);self.assertEqual(n,plain);self.assertEqual(t,trace)

    def test_reference_cli_preserves_cpu_only_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'reference.json';result=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'reference','--suite','undying-predicate','--out',str(output)],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr);report=json.loads(output.read_text());self.assertEqual(report['case_count'],22)
            self.assertTrue(report['cpu_reference_verified']);self.assertFalse(report['gpu_supported']);self.assertEqual(report['gpu_calls'],dict(build=0,execute=0));self.assertEqual(report['packing_calls'],0)

    def test_specific_blocker_routes_to_contracts_without_support_claim(self):
        row=dict(phase='effect',category='trigger',kind='buff',stat='heal_received_pct',target='self',operator=dict(domain='condition',descriptor='self_undying'))
        r=reference_readiness(row);self.assertEqual(r['lane'],'reference_review');self.assertEqual(r['recorded_cases'],25);self.assertFalse(r['gpu_supported']);self.assertFalse(r['runtime_validation_performed'])
        self.assertEqual(reference_readiness(dict(row,target='all_allies'))['lane'],'reference_review')


if __name__=='__main__':unittest.main()
