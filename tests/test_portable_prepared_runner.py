"""Parent -> real ownership/child/envelope with synthetic GPU/Windows boundary."""
import json,os,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_prepared_runner as runner
import portable_prepared_execution as execution
import portable_admission_authority as authority
import portable_admission_snapshot as snap
import test_portable_admission_authority as authority_fixture
import test_portable_prepared_execution as child_fixture
import test_portable_generation_cache as generation_fixture
from windows_validation_observer import compare_snapshots

def numeric_handoff(original=authority_fixture.fixture.HandoffTests):
    f=original();setup=f.setUp
    def numeric_setup():
        setup();f.golden['output_sha256']=snap.digest(struct.pack('<I',123))
        f.cert['golden_sha256']=snap.digest(snap.canonical(f.golden))
    f.setUp=numeric_setup
    return f


class PreparedRunnerTests(unittest.TestCase):
    def setUp(self):
        f=authority_fixture.AuthorityTests()
        with patch.object(authority_fixture.fixture,'HandoffTests',numeric_handoff):f.setUp()
        self.addCleanup(f.doCleanups);self.f=f;self.base=f.f.base;self.out=self.base/'parent'
        self.capture=Path(f.f.binding['future_capture']);self.workspace=self.base/'original';self.workspace.mkdir()
        self.slang=self.base/'sdk';self.cache=self.base/'generation';self.slang.mkdir();self.cache.mkdir()
        self.generated=self.base/'cached.cu';self.generated.write_bytes(f.f.cuda);self.metal=self.base/'cached.metal';self.metal.write_bytes(b'generated metal')
        self.preflight_calls=0;self.launches=0;self.proxy=patch.object(runner,'is_windows',return_value=True);self.proxy.start();self.addCleanup(self.proxy.stop)
        self.child_proxy=patch.object(execution,'is_windows',return_value=True);self.child_proxy.start();self.addCleanup(self.child_proxy.stop)
        self.config=f.cli.SUITES['authority-fixture'];self.config['output_words']=1
        self.cli=SimpleNamespace(**{**vars(f.cli),'required_generation_snapshot':self.preflight,'run_job':self.launch})
    def save(self,path,value):path.write_text(json.dumps(value))
    def preflight(self,m):
        self.preflight_calls+=1
        self.assertEqual(os.environ['NIKKE_SLANG_GENERATION_REQUIRED'],'1')
        self.assertFalse((self.f.consumer/'gpu-claimed-cuda.json').exists())
        return dict(cuda=self.generated,metal=self.metal),dict(passed=True,gpu_calls=0,calculation_verified=False)
    def launch(self,capture,backend,timeout,workspace,*,prepared_claim_sha256):
        self.launches+=1;self.assertEqual(backend,'cuda');self.assertEqual(timeout,60)
        self.assertEqual(workspace,self.workspace);self.assertEqual(os.environ['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
        self.assertTrue((self.f.f.tx/'gpu-execution-claimed.json').exists())
        self.save(capture/'start.json',{})
        python=str(authority.base_python())
        self.save(capture/'command.json',dict(base_python=python,argv=[python,str(self.cli.ROOT/'scripts/nikke_gpu.py'),'_prepared_child','--capture',str(capture),'--claim-sha256',prepared_claim_sha256],cwd=str(self.cli.ROOT),shell=False,timeout_seconds=timeout))
        helper=child_fixture.PreparedExecutionTests();helper.f=self.f;helper.source=self.generated;helper.capture=capture;helper.gpu_calls=0;helper.emit_trace=True
        def copy(folder,suite):
            (folder/'generated.cu').write_bytes(self.f.f.cuda);(folder/'generated.metal').write_bytes(b'generated metal');(folder/'compiled.cubin').write_bytes(self.f.f.image)
        child_cli=SimpleNamespace(**{**vars(self.cli),'copy_generated':copy})
        import portable_backend
        with patch.object(execution,'is_windows',return_value=True),patch.object(execution,'live_job',return_value=dict(job_memory_limit_bytes=2147483648,job_limit_flags=0x2200)),patch.object(portable_backend,'execute',side_effect=helper.cpu_execute):
            execution.child(child_cli,capture,prepared_claim_sha256)
        self.assertEqual(helper.gpu_calls,1)
        rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()];pid=rows[0]['pid'];first=rows[0]['wall_time_ns'];last=rows[-1]['wall_time_ns']
        self.save(capture/'job.json',dict(records=[dict(child_pid=pid,wrapper_pid=777,pre_gate_verified=True,inspection_error=None,
            pre_gate=dict(child_pid=pid,child_ppid=777,job_members=[pid],child_creation_filetime_ticks='identity',observed_unix_ns=first-1,job_memory_limit_bytes=2147483648),
            post_wait=dict(child_pid=pid,child_ppid=777,job_members=[],child_creation_filetime_ticks='identity',observed_unix_ns=last+1,job_memory_limit_bytes=2147483648))]))
        facts=dict(passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,below_normal_priority=True,timeout_seconds=60,error=None,cleanup_error=None,observation_error=None,wait_completed_unix_ns=last+2)
        self.save(capture/'execution.json',facts)
        before=dict(processes=[],service_status='unverified',observed_unix_ns=first-2);after=dict(processes=[],service_status='unverified',observed_unix_ns=last+3)
        self.save(capture/'observation.json',dict(before=before,after=after,comparison=compare_snapshots(before,after)))
        return facts
    def run_parent(self,**kwargs):
        f=self.f
        return runner.run(self.cli,f.f.controller,f.stage,f.f.binding,f.f.sha,f.f.cert_sha,self.out,
            original_workspace=self.workspace,slang_root=self.slang,generation_cache=self.cache,**kwargs)
    def test_real_authority_claim_child_and_envelope_stay_pending_fresh_native_audit(self):
        result=self.run_parent()
        self.assertTrue(result['gpu_execution_completed']);self.assertTrue(result['readback_fingerprint_matches']);self.assertTrue(result['containment_verified'])
        self.assertFalse(result['calculation_verified']);self.assertFalse(result['preservation_verified']);self.assertFalse(result['passed']);self.assertTrue(result['independent_post_audit_required'])
        self.assertEqual(self.preflight_calls,1);self.assertEqual(self.launches,1)
        self.cli.check_records(self.capture,self.cli.load(self.capture/'artifacts.json')['files'])
        with self.assertRaises(FileExistsError):self.run_parent()
        self.assertEqual(self.launches,1)
    def test_missing_cache_or_wrong_cuda_never_consumes_original_attempt(self):
        self.generated.write_bytes(b'wrong CUDA')
        with self.assertRaisesRegex(ValueError,'exact CUDA bytes'):self.run_parent()
        self.assertFalse((self.f.f.tx/'gpu-execution-claimed.json').exists());self.assertFalse(self.capture.exists());self.assertEqual(self.launches,0)
    def test_insufficient_storage_never_claims_or_allocates_raw(self):
        with patch.object(runner,'space_status',return_value=dict(passed=False,required_bytes=100,free_bytes=0,reserve_bytes=1024**3)),self.assertRaisesRegex(ValueError,'storage budget'):self.run_parent()
        self.assertFalse((self.f.consumer/'gpu-claimed-cuda.json').exists());self.assertFalse(self.capture.exists());self.assertEqual(self.launches,0)
    def test_required_generation_miss_stops_before_authority_and_claim(self):
        self.cli.required_generation_snapshot=lambda m:(_ for _ in ()).throw(RuntimeError('required generation miss'))
        with self.assertRaisesRegex(RuntimeError,'generation miss'):self.run_parent()
        self.assertFalse((self.out/'authority').exists());self.assertFalse(self.capture.exists());self.assertEqual(self.launches,0)
    def test_real_required_cache_reader_keeps_its_own_file_only_guard(self):
        import copy,runpy
        g=generation_fixture.GenerationCacheTests();g.setUp();self.addCleanup(g.doCleanups)
        g.build();paths,hashes=g.build(True)
        normalizer=runpy.run_path(str(ROOT/'research/summarize-portable-cross-gpu.py'))['normalized']
        original=authority_fixture.original_cli.required_generation_snapshot
        observed=[]
        def real_preflight(m):
            probe=copy.deepcopy(m);probe['golden']['source_sha256']=hashes
            probe['golden']['generated_normalized']={k:normalizer(p.read_bytes()) for k,p in paths.items()}
            with patch.dict(original.__globals__,dict(ROOT=g.root,module=lambda path:SimpleNamespace(normalized=normalizer))),patch.dict(os.environ,NIKKE_SLANG_ROOT=str(g.tool),NIKKE_SLANG_GENERATION_CACHE=str(g.cached)):
                _,receipt=original(probe);observed.append(receipt)
            raise RuntimeError('real required cache reader completed')
        self.cli.required_generation_snapshot=real_preflight
        with self.assertRaisesRegex(RuntimeError,'real required cache reader completed'):self.run_parent()
        self.assertTrue(observed[0]['generation']['hit']);self.assertEqual(observed[0]['forbidden_attempts'],[])
        self.assertEqual(g.calls,['cuda','metal']);self.assertFalse((self.f.f.tx/'gpu-execution-claimed.json').exists());self.assertEqual(self.launches,0)
    def test_failed_launch_retains_claims_and_blocks_retry(self):
        self.cli.run_job=lambda *args,**kwargs:(_ for _ in ()).throw(TimeoutError('bounded child stopped'))
        with self.assertRaises(TimeoutError):self.run_parent()
        self.assertTrue((self.f.f.tx/'gpu-execution-claimed.json').exists());self.assertTrue((self.f.consumer/'gpu-claimed-cuda.json').exists())
        failure=self.cli.load(self.out/'failure.json');self.assertTrue(failure['execution_claim_may_exist']);self.assertIsNone(failure['gpu_calls'])
        with self.assertRaises(FileExistsError):self.run_parent()
    def test_partial_claim_is_not_rolled_back_or_reported_unclaimed(self):
        original=runner.claim
        def interrupted(cli,a):
            original(cli,a);raise OSError('publication interrupted')
        with patch.object(runner,'claim',side_effect=interrupted),self.assertRaises(OSError):self.run_parent()
        self.assertTrue(self.cli.load(self.out/'failure.json')['execution_claim_may_exist']);self.assertFalse(self.capture.exists());self.assertEqual(self.launches,0)
    def test_parent_output_must_not_mutate_immutable_source(self):
        self.out=self.f.consumer/'forbidden'
        with self.assertRaisesRegex(ValueError,'separate'):self.run_parent()
        self.assertFalse(self.out.exists())
    def test_existing_capture_is_not_collected_or_modified_on_rejection(self):
        self.capture.mkdir();(self.capture/'sentinel').write_bytes(b'original')
        with self.assertRaises(FileExistsError):self.run_parent()
        self.assertEqual(sorted(p.name for p in self.capture.iterdir()),['sentinel'])
    def test_platform_and_timeout_gates_precede_any_writes(self):
        with patch.object(runner,'is_windows',return_value=False),self.assertRaisesRegex(ValueError,'requires Windows'):self.run_parent()
        for timeout in (False,0,61):
            with self.subTest(timeout=timeout),self.assertRaises(ValueError):self.run_parent(timeout=timeout)
        self.assertFalse(self.out.exists());self.assertEqual(self.preflight_calls,0)


if __name__=='__main__':unittest.main()
