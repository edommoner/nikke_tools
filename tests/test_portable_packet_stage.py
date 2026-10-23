"""Whole-stage orchestration cannot broaden preparation or replay a claim."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('packet_stage',ROOT/'scripts/run-gpu-packet.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
class PacketStageTests(unittest.TestCase):
    def test_recipe_rejects_capture_inside_package_and_original(self):
        with self.assertRaises(ValueError):stage.recipe('id','cpu','cuda',ROOT/'capture',None,180)
        with self.assertRaises(ValueError):stage.recipe('id','cpu','cuda',Path('/tmp/original/capture'),'/tmp/original',180)
    def test_commands_are_fixed_without_shell_or_history_paths(self):
        for mode in ('cpu','gpu','smoke'):
            p=stage.recipe('id',mode,'cuda','/tmp/isolated-stage','/tmp/original',180)
            a=stage.proof_arguments(p);self.assertEqual(a[:3],['run','--backend','cuda']);self.assertIn('--timeout',a);self.assertEqual(a[a.index('--timeout')+1],'60')
            self.assertEqual('--cpu-only' in a,mode=='cpu');self.assertEqual('--smoke' in a,mode=='smoke')
    def test_budget_and_stage_validation(self):
        for timeout in (0,181,True,1.5):
            with self.assertRaises(ValueError):stage.recipe('id','cpu','cuda','/tmp/x',None,timeout)
        with self.assertRaises(ValueError):stage.recipe('id','compile','cuda','/tmp/x',None,180)
    def test_existing_stage_record_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'claim.json';stage.save(p,{'old':1})
            with self.assertRaises(FileExistsError):stage.save(p,{'new':2})
            self.assertEqual(json.loads(p.read_text()),{'old':1})
    def test_missing_or_failed_child_result_never_becomes_success(self):
        # The real bounded owner cleans its process tree; this checks parent
        # interpretation without starting another process or importing a GPU.
        for facts,proof in [({'passed':False},None),({'passed':False},{'cpu_verified':True}),({'passed':True},None),({'passed':True},{'cpu_verified':False})]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage'
                def bounded(*a,**kw):
                    if proof is not None:(folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps(proof))
                    return facts
                cli=SimpleNamespace(verify_package=lambda _:dict(package_id='id'),bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
                with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False),patch.object(Path,'rglob',side_effect=AssertionError('No historical enumeration')):
                    result=stage.run_stage(folder,'cpu','metal',20)
                self.assertFalse(result['stage_verified']);self.assertFalse(result['cpu_verified'])
    def test_success_requires_real_proof_receipt_and_owned_completion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'packet';root.mkdir();folder=Path(d)/'stage'
            def bounded(command,where,timeout,**kw):
                self.assertEqual(where,folder.resolve());self.assertGreater(timeout,170);self.assertLessEqual(timeout,180);self.assertEqual(command[0],sys.executable);self.assertFalse('shell' in kw);self.assertEqual(kw['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
                (folder/'proof').mkdir();(folder/'proof/result.json').write_text(json.dumps({'cpu_verified':True}));return {'passed':True}
            cli=SimpleNamespace(verify_package=lambda _:dict(package_id='id'),bounded_module=lambda:SimpleNamespace(run_bounded=bounded),validation_environment=lambda _:dict())
            with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False):
                result=stage.run_stage(folder,'cpu','metal',180)
                self.assertTrue(result['cpu_verified']);self.assertTrue(result['stage_complete'])
                with self.assertRaises(FileExistsError):stage.run_stage(Path(d)/'another','cpu','metal',180)
if __name__=='__main__':unittest.main()
