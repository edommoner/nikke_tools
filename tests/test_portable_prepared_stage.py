"""Bounded prepared-stage recipe and launch adapter; no real Job/device."""
import contextlib,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import test_portable_packet_stage as fixture
import test_portable_admission_handoff as cli_fixture
stage=fixture.stage


class OSProxy:
    name='nt'
    def __getattr__(self,key):return getattr(os,key)


class PreparedStageTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.base=Path(tmp.name).resolve()
        self.request={key:('a'*64 if key.endswith('_sha256') else str(self.base/key)) for key in stage.PREPARED_GPU_FIELDS}
        self.binding=dict(owner_package_id='b'*64,controller_package_id='c'*64,transaction_nonce='d'*32,input_sha256='e'*64,artifact_sha256='f'*64,future_capture=str(self.base/'reserved-gpu'))
        Path(self.request['binding']).write_text(json.dumps(self.binding))
    def recipe(self,**kwargs):
        return stage.recipe('consumer',stage.PREPARED_GPU_STAGE,'cuda',self.base/'stage',self.base/'original',180,self.request,**kwargs)
    def test_recipe_retains_both_budgets_external_hashes_and_fixed_generation_paths(self):
        p=self.recipe();args=stage.proof_arguments(p)
        self.assertEqual(p['timeout_seconds'],180);self.assertEqual(p['inner_gpu_timeout_seconds'],60);self.assertEqual(p['memory_limit_mb'],2048)
        self.assertEqual(args[0],'prepared-run');self.assertEqual(args[args.index('--out')+1],p['proof_capture'])
        self.assertEqual(args[args.index('--expected-sha256')+1],self.request['snapshot_sha256'])
        self.assertEqual(p['generation_settings'],{k:self.request[k] for k in ('slang_root','generation_cache')})
        self.request['header_materials']=str(self.base/'descriptor.json');self.assertIn('--header-materials',stage.proof_arguments(self.recipe()))
    def test_request_rejects_missing_extra_sha_and_relative_paths(self):
        for change in (dict(snapshot_sha256='wrong'),dict(binding='relative.json'),dict(extra='unexpected')):
            with self.subTest(change=change),self.assertRaises(ValueError):stage.object_request(stage.PREPARED_GPU_STAGE,dict(self.request,**change))
        with self.assertRaises(ValueError):stage.object_request(stage.PREPARED_GPU_STAGE,{k:v for k,v in self.request.items() if k!='certificate_sha256'})
    def test_cuda_workspace_and_generation_settings_are_mandatory(self):
        with self.assertRaises(ValueError):stage.recipe('consumer',stage.PREPARED_GPU_STAGE,'metal',self.base/'stage',self.base/'original',180,self.request)
        with self.assertRaises(ValueError):stage.recipe('consumer',stage.PREPARED_GPU_STAGE,'cuda',self.base/'stage',None,180,self.request)
        with self.assertRaises(ValueError):self.recipe(generation_settings=dict(slang_root='other',generation_cache='other'))
    def proof(self):
        return dict(mode='snapshot-gpu-pending-native-audit',protocol='snapshot-prepared-v1',package_id='consumer',capture=self.binding['future_capture'],
            gpu_execution_completed=True,readback_fingerprint_matches=True,containment_verified=True,independent_post_audit_required=True,execution_claim_retained=True,
            calculation_verified=False,passed=False,full_goal_complete=False,gpu_retries=0,preservation_verified=False,process_preservation_verified=True)
    def test_stage_success_cannot_promote_pending_native_or_unknown_service(self):
        self.assertTrue(stage.verified_prepared_gpu(self.proof(),'consumer',self.request))
        for change in (dict(calculation_verified=True),dict(containment_verified=False),dict(readback_fingerprint_matches=False),dict(gpu_retries=False),dict(package_id='different'),dict(capture=str(self.base/'wrong'))):
            with self.subTest(change=change):self.assertFalse(stage.verified_prepared_gpu(dict(self.proof(),**change),'consumer',self.request))
    def test_actual_shared_job_adapter_records_exact_command_and_uses_existing_observers(self):
        cli=cli_fixture.cli;capture=self.base/'gpu';capture.mkdir();observed={}
        def bounded(command,folder,timeout,**kwargs):
            observed.update(command=command,folder=folder,timeout=timeout,kwargs=kwargs)
            kwargs['before_gate']();kwargs['after_wait']();return dict(passed=True)
        fake=SimpleNamespace(run_bounded=bounded)
        import windows_validation_observer as observer
        namespace=cli.run_job.__globals__
        with patch.dict(namespace,dict(ROOT=self.base,__file__=str(self.base/'scripts/nikke_gpu.py'),os=OSProxy(),bounded_module=lambda:fake)),patch.dict(os.environ,NIKKE_VALIDATION_JOB_MEMORY_MB='2048'),patch.object(observer,'observe_job',return_value=contextlib.nullcontext()) as job,patch.object(observer,'capture_snapshot',side_effect=lambda *a:dict(processes=[],service_status='unverified',observed_unix_ns=1)):
            facts=cli.run_job(capture,'cuda',60,self.base/'original',prepared_claim_sha256='a'*64)
        self.assertTrue(facts['passed']);self.assertEqual(observed['timeout'],60)
        self.assertIn('_prepared_child',observed['command']);self.assertNotIn('_child',observed['command'])
        command=cli.load(capture/'command.json');self.assertEqual(command['argv'],observed['command']);self.assertFalse(command['shell'])
        self.assertEqual(observed['kwargs']['env']['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048');self.assertEqual(observed['kwargs']['env']['CUDA_CACHE_DISABLE'],'1')
        job.assert_called_once_with(fake,capture/'job.json')
        self.assertEqual(cli.load(capture/'observation.json')['comparison']['missing_existing_processes'],[])
    def test_job_adapter_refuses_diagnostic_switches_before_launch(self):
        cli=cli_fixture.cli;capture=self.base/'gpu';capture.mkdir();namespace=cli.run_job.__globals__
        with patch.dict(namespace,dict(ROOT=self.base,os=OSProxy(),bounded_module=lambda:None)):
            with self.assertRaisesRegex(ValueError,'bounded battle child'):
                cli.run_job(capture,'cuda',60,self.base/'original',compile_only=True,prepared_claim_sha256='a'*64)
        self.assertFalse((capture/'command.json').exists())


if __name__=='__main__':unittest.main()
