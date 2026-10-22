"""CPU prerequisite coverage without treating packing or no-op output as GPU proof."""
import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_state_predicate_cases import fixtures
from portable_state_predicate_contracts import verify
from world_state_predicate_native import observe,plain_observe
s=importlib.util.spec_from_file_location('state_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class StatePredicateReferenceTests(unittest.TestCase):
    def test_thirty_literal_contracts_without_packing_or_gpu(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No factory battle')):cases=fixtures()
        self.assertEqual(len(cases),30);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')),patch.object(detail_gpu,'compile_effects',side_effect=AssertionError('No compiler')):
            for c in cases:
                with self.subTest(case=c['name']):self.assertTrue(verify(c,observe(c)[0])['verified'])
        self.assertEqual(cases,before)

    def test_all_fields_trace_and_existing_query_counts_preserved(self):
        originals={name:getattr(BuffManager,name) for name in ['_condition_ok','_runtime_condition_ok','cover_alive']}
        for c in fixtures():
            counts=[]
            def wrapper(name):
                def call(*args,**kwargs):counts[-1][name]+=1;return originals[name](*args,**kwargs)
                return call
            with self.subTest(case=c['name']),patch.object(BuffManager,'_condition_ok',wrapper('_condition_ok')),patch.object(BuffManager,'_runtime_condition_ok',wrapper('_runtime_condition_ok')),patch.object(BuffManager,'cover_alive',wrapper('cover_alive')):
                counts.append(dict.fromkeys(originals,0));plain,trace=plain_observe(c)
                counts.append(dict.fromkeys(originals,0));native,recorded=observe(c)
                native.pop('state_predicates');self.assertEqual(native,plain);self.assertEqual(trace,recorded);self.assertEqual(counts[0],counts[1])

    def test_faults_in_covers_camera_or_battle_are_rejected(self):
        c=fixtures()[0];base,_=observe(c)
        for fault in ['cover_owner','cover_value','result','stack','damage','ammo']:
            n=copy.deepcopy(base);obs=n['state_predicates']
            if fault=='cover_owner':obs['checks'][0]['cover'][0]['owner']=4
            elif fault=='cover_value':obs['checks'][0]['cover'][0]['result']=False
            elif fault=='result':obs['checks'][0]['result']=False
            elif fault=='stack':obs['carriers'][0]['stack']=1
            elif fault=='damage':n['projectile_shots'][0]['damage']+=1
            else:n['ammo'][0]+=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,n)
        c=next(c for c in fixtures() if c['name'].endswith('focus-dynamic-owner'));n,_=observe(c);n['state_predicates']['runtime'][0]['camera_mask']=16
        with self.assertRaises(AssertionError):verify(c,n)

    def test_unported_host_predicates_still_reject(self):
        for c in [fixtures()[0],next(c for c in fixtures() if c['name'].endswith('focus-passive-self'))]:
            with self.assertRaises(ValueError):portable_runtime.validate_effect(c['effects'][-1],combat={},world_frame=True)

    def test_cli_is_explicitly_cpu_reference_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'reference.json';r=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'reference','--suite','state-predicates','--out',str(out)],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stderr);d=json.loads(out.read_text());self.assertEqual(d['case_count'],30);self.assertFalse(d['gpu_supported']);self.assertFalse(d['calculation_verified']);self.assertEqual(d['gpu_calls'],dict(build=0,execute=0));self.assertEqual(d['packing_calls'],0)


if __name__=='__main__':unittest.main()
