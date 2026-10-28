"""Final canonical queued hits remain valid when their source retires."""
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from world_add_self_destruct_native import fixtures,observe,verify


class AddSelfDestructNativeTests(unittest.TestCase):
    def test_all_original_shots_remain_and_inputs_methods_are_unchanged(self):
        from calculator.boss_pattern import BossScript
        methods={n:getattr(BossScript,n) for n in ('begin_frame','_add_attacks','_retire')}
        cases=fixtures();before=copy.deepcopy(cases)
        for case in cases:
            with self.subTest(case=case['name']):
                native,trace=observe(case);contract=verify(case,native)
                self.assertTrue(contract['verified']);self.assertEqual(contract['queued_shots'],case['hits']);self.assertEqual(trace,[])
                self.assertFalse(native['full_battle_validation']);self.assertFalse(native['gpu_supported'])
        self.assertEqual(cases,before)
        self.assertEqual(methods,{n:getattr(BossScript,n) for n in methods})

    def test_dropping_a_final_shot_or_delaying_retirement_fails_the_contract(self):
        case=fixtures()[1];native,_=observe(case)
        for change in ('drop','alive','death-event'):
            broken=copy.deepcopy(native);last=next(r for r in broken['frames'] if 'enemy_death' in r['events'])
            if change=='drop':last['queued']=[]
            elif change=='alive':last['alive']=True
            else:last['events'].remove('enemy_death')
            with self.subTest(change=change),self.assertRaises(AssertionError):verify(case,broken)

    def test_fresh_cli_initializes_the_reference_without_gpu_or_packing(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'reference.json'
            run=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'reference','--suite','add-self-destruct-native','--out',str(output)],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            proof=json.loads(output.read_text());self.assertTrue(proof['cpu_reference_verified'])
            self.assertEqual(proof['case_count'],4);self.assertEqual(proof['packing_calls'],0)
            self.assertEqual(proof['gpu_calls'],dict(build=0,execute=0));self.assertFalse(proof['gpu_supported'])

    def test_missing_feature_metadata_distinguishes_component_from_gpu(self):
        from portable_readiness_semantics import enemy_ammo_prerequisites
        r=enemy_ammo_prerequisites()['declared_add_self_destruct_contract'];proof=json.loads((ROOT/r['evidence']).read_text())
        self.assertEqual(proof['case_count'],r['cases']);self.assertTrue(proof['cpu_reference_verified'])
        self.assertEqual(hashlib.sha256((ROOT/r['source']).read_bytes()).hexdigest(),proof['observer_source_sha256'])
        canonical=ROOT/'research/upstream/nikke-calc-master/calculator/boss_pattern.py'
        self.assertEqual(hashlib.sha256(canonical.read_bytes()).hexdigest(),proof['canonical_source_sha256'])
        for key in ('gpu_wire_connected','metal_verified','cuda_verified','full_battle_verified','default_producer_installed'):self.assertFalse(r[key])


if __name__=='__main__':unittest.main()
