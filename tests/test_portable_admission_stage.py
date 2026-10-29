"""CPU preparation reuses the existing bounded stage and cannot claim a GPU run."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
spec=importlib.util.spec_from_file_location('admission_stage_wrapper',ROOT/'scripts/run-gpu-packet.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


class AdmissionStageTests(unittest.TestCase):
    def request(self,base):
        return {k:('a'*64 if k=='expected_owner_id' else str(base/k)) for k in stage.PREPARE_FIELDS}
    def test_exact_request_preserves_owner_anchor_and_never_uses_gpu_command(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d).resolve();request=self.request(base)
            plan=stage.recipe('id',stage.PREPARE_STAGE,'cuda',base/'out',base/'original',180,request)
            args=stage.proof_arguments(plan);self.assertEqual(args[0],'prepare-admission')
            self.assertEqual(plan['memory_limit_mb'],2048);self.assertEqual(plan['timeout_seconds'],180)
            for k,v in request.items():self.assertEqual(args[args.index('--'+k.replace('_','-'))+1],v)
            self.assertEqual(args[args.index('--out')+1],str(base/'out/proof'))
            for bad in ({},dict(request,expected_owner_id='bad'),dict(request,transaction='relative'),dict(request,extra='yes')):
                with self.assertRaises(ValueError):stage.recipe('id',stage.PREPARE_STAGE,'cuda',base/'out',base/'original',180,bad)
            with self.assertRaises(ValueError):stage.recipe('id',stage.PREPARE_STAGE,'metal',base/'out',base/'original',180,request)
            with self.assertRaises(ValueError):stage.recipe('id',stage.PREPARE_STAGE,'cuda',base/'out',None,180,request)
    def test_parent_uses_preparation_validator_keeps_claim_and_cannot_promote_calculation(self):
        for accepted in (True,False):
            with tempfile.TemporaryDirectory() as d:
                base=Path(d).resolve();root=base/'packet';root.mkdir();folder=base/'out';request=self.request(base)
                proof=dict(preparation_verified=True,calculation_verified=True,gpu_calls=0)
                def bounded(*args,**kwargs):
                    self.assertEqual(kwargs['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
                    (folder/'proof').mkdir();stage.save(folder/'proof/result.json',proof);return dict(passed=True)
                cli=SimpleNamespace(validation_environment=lambda _:dict(),bounded_module=lambda:SimpleNamespace(run_bounded=bounded))
                with patch.object(stage,'ROOT',root),patch.object(stage,'packet_header',return_value=dict(package_id='id')),patch.object(stage,'load_module',return_value=cli),patch.object(stage,'is_windows',return_value=False),patch('portable_admission_prepare.verified_result',return_value=accepted) as validate:
                    result=stage.run_stage(folder,stage.PREPARE_STAGE,'cuda',180,base/'original',request)
                    self.assertEqual(result['preparation_verified'],accepted);self.assertEqual(result['stage_verified'],accepted)
                    self.assertFalse(result['execution_admitted']);self.assertFalse(result['calculation_verified']);self.assertFalse(result['compiler_verified'])
                    validate.assert_called_once_with(proof,folder/'proof','id',request)
                    with self.assertRaises(FileExistsError):stage.run_stage(base/'again',stage.PREPARE_STAGE,'cuda',180,base/'original',request)
                self.assertTrue((root/'packet-stage-claimed-prepare-admission-cuda.json').is_file())


if __name__=='__main__':unittest.main()
