"""CPU fault injection for cache-only module JIT; no allocations or dispatch."""
import contextlib,ctypes as C,importlib.util,json,os,sys,time,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_backend as backend
import test_portable_resident_transport as transport_test
from test_portable_resident_layout import document
spec=importlib.util.spec_from_file_location('module_check_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class ModuleCheckTests(unittest.TestCase):
    def setUp(self):
        self.base=transport_test.ResidentTransportTests();self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.root=self.base.source.parent.resolve();build=self.root/'research/portable-build';build.mkdir(parents=True)
        self.cuda=build/'entry.cu';self.cuda.write_bytes(self.base.source.read_bytes());self.metal=build/'entry.metal';self.metal.write_bytes(b'metal fixture')
        (self.root/'gpu').mkdir();(self.root/'gpu/entry.slang').write_text('#define PORTABLE_RESIDENT_RUNTIME\n')
        self.outputs=dict(cuda=self.cuda,metal=self.metal)
        for target,path in self.outputs.items():Path(str(path)+'.reflection.json').write_text(json.dumps(document(target)))
        self.hashes={'gpu/entry.slang':cli.sha((self.root/'gpu/entry.slang').read_bytes())}
        self.m=dict(suite='fixture',package_id='fixed-test',purpose='sealed',golden=dict(source_sha256=self.hashes,generated_normalized={k:cli.sha(p.read_bytes()) for k,p in self.outputs.items()}))
        self.capture=self.root/'capture';self.capture.mkdir()
        self.artifact=b'.version 8.4\n.target sm_86\n.address_size 64\n'
        identity=dict(artifact='ptx',options=backend.cuda_compile_options('ptx'),source_sha256=cli.sha(self.cuda.read_bytes()))
        self.receipt=dict(enabled=True,hit=True,key=cli.sha(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()),identity=identity,artifact_bytes=len(self.artifact),artifact_sha256=cli.sha(self.artifact))
        self.fake_os=types.SimpleNamespace(name='nt',environ={'NIKKE_CUDA_ARTIFACT':'ptx','NIKKE_CUDA_CACHE_REQUIRED':'1'})

    def context(self):
        stack=contextlib.ExitStack()
        stack.enter_context(patch.object(backend,'os',self.fake_os))
        stack.enter_context(patch.object(backend,'ROOT',self.root));stack.enter_context(patch.object(cli,'ROOT',self.root))
        stack.enter_context(patch.dict(cli.SUITES,fixture=dict(source='gpu/entry.slang')))
        stack.enter_context(patch.object(backend,'build',return_value=(self.outputs,self.hashes)))
        stack.enter_context(patch.object(backend.C,'WinDLL',return_value=self.base.driver,create=True))
        def compiled(*args,**kwargs):
            # Exercise the same observed compiler/cache boundary without NVRTC.
            result=backend.compile_cuda_artifact(None,b'not compiled')
            self.cuda.with_suffix('.ptx').write_bytes(result[0]);return result
        stack.enter_context(patch.object(backend,'compile_cuda_source',side_effect=compiled))
        stack.enter_context(patch.object(backend,'compile_cuda_artifact',return_value=(self.artifact,self.receipt)))
        stack.enter_context(patch.object(cli,'module',return_value=types.SimpleNamespace(normalized=cli.sha)))
        return stack

    def proof(self,level=None):
        with self.context(),patch.dict(os.environ,NIKKE_CUDA_JIT_OPT_LEVEL='' if level is None else str(level)):
            cli.module_child(self.m,self.capture,'cuda')
        cli.write(self.capture/'run.json',dict(mode='module-only',package_id=self.m['package_id'],backend='cuda',memory_limit_mb=2048,jit_optimization_level=level))
        cli.write(self.capture/'execution.json',dict(passed=True,timeout_seconds=60,observation_error=None,wait_completed_unix_ns=time.time_ns()))
        pre=dict(child_pid=os.getpid(),child_ppid=17,job_members=[os.getpid()],child_creation_filetime_ticks='100',observed_unix_ns=1,job_memory_limit_bytes=2048*1024*1024)
        cli.write(self.capture/'job.json',dict(records=[dict(child_pid=os.getpid(),wrapper_pid=17,pre_gate_verified=True,inspection_error=None,pre_gate=pre,post_wait=dict(pre,job_members=[],observed_unix_ns=time.time_ns()))]))

    def audit(self):
        with self.context():return cli.audit_module_capture(self.m,self.capture,verify_artifacts=False)

    def test_module_success_requires_cleanup_cache_abi_and_job_and_is_not_calculation(self):
        self.proof();result=self.audit();self.assertTrue(result['module_verified']);self.assertTrue(result['containment_verified'])
        self.assertFalse(result['calculation_verified']);self.assertFalse(result['preservation_verified']);self.assertFalse(result['passed'])
        self.assertEqual(result['kernel_calls'],0);self.assertEqual(self.base.allocations,[])
        self.base.driver.cuCtxDestroy_v2.assert_called_once();self.base.driver.cuLaunchKernel.assert_not_called()
        self.base.driver.cuMemcpyHtoD_v2.assert_not_called();self.base.driver.cuCtxSynchronize.assert_not_called()

    def test_explicit_jit_level_passes_scalar_option_and_preserves_cleanup(self):
        self.base.driver.cuModuleLoadDataEx=Mock(return_value=0)
        for level in (0,1,4):
            with self.subTest(level=level),self.context():
                result=backend.inspect_cuda_module(self.cuda,'portableEvents',resident=self.base.plan,jit_opt_level=level)
                args=self.base.driver.cuModuleLoadDataEx.call_args.args
                self.assertEqual(args[2],1);self.assertEqual(args[3][0],7)
                self.assertEqual(args[4][0],level or None)
                self.assertEqual(result['jit_optimization_level'],level)
                self.assertEqual(self.base.allocations,[])
        self.base.driver.cuModuleLoadData.assert_not_called()
        self.assertEqual(self.base.driver.cuCtxDestroy_v2.call_count,3)

    def test_explicit_jit_failure_cleans_context_and_does_not_fallback(self):
        self.base.driver.cuModuleLoadDataEx=Mock(return_value=218)
        with self.context(),self.assertRaisesRegex(RuntimeError,'cuModuleLoadDataEx: CUDA error 218'):
            backend.inspect_cuda_module(self.cuda,'portableEvents',resident=self.base.plan,jit_opt_level=1)
        self.base.driver.cuModuleLoadData.assert_not_called()
        self.base.driver.cuCtxDestroy_v2.assert_called_once();self.assertEqual(self.base.allocations,[])

    def test_invalid_jit_configuration_stops_before_driver(self):
        for level in (-1,5,True,'1'):
            with self.subTest(level=level),self.context(),self.assertRaises(ValueError):
                backend.inspect_cuda_module(self.cuda,'portableEvents',resident=self.base.plan,jit_opt_level=level)
        self.base.driver.cuInit.assert_not_called()

    def test_explicit_jit_module_journal_and_audit_match_native_arguments(self):
        self.base.driver.cuModuleLoadDataEx=Mock(return_value=0)
        self.proof(level=1);self.assertTrue(self.audit()['module_verified'])
        self.assertEqual(len(self.base.driver.cuModuleLoadDataEx.argtypes),5)
        self.assertIs(self.base.driver.cuModuleLoadDataEx.restype,C.c_int)
        self.base.driver.cuModuleLoadData.assert_not_called()
        path=self.capture/'phases.jsonl';rows=[json.loads(line) for line in path.read_text().splitlines()]
        path.write_text('\n'.join(json.dumps(r) for r in rows if r['stage']!='cuda_jit_native_options')+'\n')
        self.assertFalse(self.audit()['module_verified'])

    def test_jit_audit_rejects_changed_configuration(self):
        self.proof();path=self.capture/'run.json';run=cli.load(path);run['jit_optimization_level']=1;cli.write(path,run)
        self.assertFalse(self.audit()['module_verified'])

    def test_required_cache_miss_stops_before_driver(self):
        self.receipt['hit']=False
        with self.context(),self.assertRaisesRegex(ValueError,'verified PTX cache hit'):cli.module_child(self.m,self.capture,'cuda')
        self.base.driver.cuInit.assert_not_called()

    def test_codegen_drift_stops_before_cache_or_driver(self):
        self.m['golden']['generated_normalized']['cuda']='wrong'
        with self.context(),self.assertRaisesRegex(ValueError,'sealed Metal'):cli.module_child(self.m,self.capture,'cuda')
        self.base.driver.cuInit.assert_not_called()

    def test_failed_jit_or_abi_destroys_context_and_never_allocates(self):
        for failure in ('jit','abi'):
            with self.subTest(failure=failure):
                self.base.driver.cuModuleLoadData.return_value=2 if failure=='jit' else 0
                self.base.global_size=32 if failure=='abi' else 48
                self.base.driver.cuCtxDestroy_v2.reset_mock()
                with self.context(),self.assertRaises(RuntimeError):cli.module_child(self.m,self.capture,'cuda')
                self.base.driver.cuCtxDestroy_v2.assert_called_once();self.assertEqual(self.base.allocations,[])

    def test_forbidden_api_is_blocked_before_native_function(self):
        def wrong(*args,**kwargs):backend.C.WinDLL('nvcuda.dll').cuMemAlloc_v2(None,1)
        with self.context(),patch.object(backend,'inspect_cuda_module',side_effect=wrong),self.assertRaisesRegex(RuntimeError,'Battle API forbidden'):
            cli.module_child(self.m,self.capture,'cuda')
        self.base.driver.cuMemAlloc_v2.assert_not_called()

    def test_nvrtc_library_is_blocked(self):
        def wrong(*args,**kwargs):backend.C.WinDLL('nvrtc64_dummy.dll')
        with self.context(),patch.object(backend,'inspect_cuda_module',side_effect=wrong),self.assertRaisesRegex(RuntimeError,'NVRTC forbidden'):
            cli.module_child(self.m,self.capture,'cuda')
        self.base.driver.cuInit.assert_not_called()

    def test_cleanup_failure_never_writes_success_metadata(self):
        self.base.driver.cuCtxDestroy_v2.return_value=3
        with self.context(),self.assertRaisesRegex(RuntimeError,'cuCtxDestroy'):cli.module_child(self.m,self.capture,'cuda')
        self.assertFalse((self.capture/'module.json').exists())

    def test_audit_rejects_missing_api_tampered_ptx_and_wrong_job(self):
        self.proof();phase=self.capture/'phases.jsonl';original=phase.read_bytes()
        rows=[json.loads(line) for line in original.decode().splitlines()];phase.write_text('\n'.join(json.dumps(r) for r in rows if r['stage']!='cuModuleLoadData')+'\n')
        self.assertFalse(self.audit()['module_verified']);phase.write_bytes(original)
        ptx=self.capture/'compiled.ptx';raw=ptx.read_bytes();ptx.write_bytes(b'wrong');self.assertFalse(self.audit()['module_verified']);ptx.write_bytes(raw)
        job=cli.load(self.capture/'job.json');job['records'][0]['post_wait']['job_memory_limit_bytes']=None;cli.write(self.capture/'job.json',job)
        self.assertFalse(self.audit()['module_verified'])

    def test_audit_cannot_hide_resident_abi_or_invent_calculation_success(self):
        self.proof();path=self.capture/'module.json';original=path.read_bytes()
        for field,value in [('resident_runtime',None),('calculation_verified',True),('buffer_allocations',1)]:
            proof=json.loads(original)
            if field=='resident_runtime':proof[field]=value
            else:proof['transport'][field]=value
            cli.write(path,proof);self.assertFalse(self.audit()['module_verified']);path.write_bytes(original)

    def test_truncated_phase_or_bad_budget_is_not_a_module_proof(self):
        self.proof();path=self.capture/'phases.jsonl';original=path.read_bytes();path.write_bytes(original+b'{"partial')
        self.assertFalse(self.audit()['module_verified']);path.write_bytes(original)
        run=cli.load(self.capture/'run.json');run['memory_limit_mb']=4096;cli.write(self.capture/'run.json',run)
        with self.assertRaisesRegex(ValueError,'bounded policy'):self.audit()

    def test_cache_verification_must_precede_driver_apis_even_when_all_return_zero(self):
        self.proof();path=self.capture/'phases.jsonl';rows=[json.loads(line) for line in path.read_text().splitlines()]
        receipt=next(r for r in rows if r['stage']=='cuda_compile_cache');rows.remove(receipt);rows.insert(len(rows)-1,receipt)
        mono=min(r['monotonic_ns'] for r in rows);wall=min(r['wall_time_ns'] for r in rows)
        for i,row in enumerate(rows):row.update(monotonic_ns=mono+i,wall_time_ns=wall+i)
        path.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
        result=self.audit();self.assertFalse(result['module_verified']);self.assertIn('order invalid',result['error'])

    def test_direct_probe_requires_ptx_and_cache_only_before_loading_driver(self):
        with self.context():
            for settings in ({'NIKKE_CUDA_ARTIFACT':'cubin'},{'NIKKE_CUDA_CACHE_REQUIRED':'0'}):
                with patch.dict(self.fake_os.environ,settings),self.assertRaisesRegex(ValueError,'cache-only PTX'):
                    backend.inspect_cuda_module(self.cuda,'portableEvents',resident=self.base.plan)
        self.base.driver.cuInit.assert_not_called()

    def test_capture_uses_separate_once_claim_and_bounded_cache_only_child(self):
        env={'NIKKE_CUDA_COMPILE_CACHE':str(self.root/'cache')};new=self.root/'fresh'
        def job(*args,**kwargs):
            self.assertTrue(kwargs['module_only']);self.assertEqual(args[2],60)
            self.assertEqual(env['NIKKE_CUDA_CACHE_REQUIRED'],'1');self.assertEqual(env['NIKKE_CUDA_ARTIFACT'],'ptx')
            self.assertEqual(env['NIKKE_VALIDATION_JOB_MEMORY_MB'],'2048')
        with self.context(),patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='nt',environ=env))),\
             patch.object(cli,'verify_package',return_value=self.m),patch.object(cli,'run_job',side_effect=job) as run,\
             patch.object(cli,'copy_generated'),patch.object(cli,'audit_module_capture',return_value=dict(mode='module-only',module_verified=True,calculation_verified=False)):
            self.assertTrue(cli.module_capture(new,60,self.root/'original')['module_verified'])
            claim=(self.root/'module-claimed-cuda.json').read_bytes()
            with self.assertRaises(FileExistsError):cli.module_capture(self.root/'second',60,self.root/'original')
            self.assertEqual((self.root/'module-claimed-cuda.json').read_bytes(),claim);self.assertEqual(run.call_count,1)
        self.assertEqual(env,{'NIKKE_CUDA_COMPILE_CACHE':str(self.root/'cache')})

    def test_module_child_flag_and_driver_cache_are_isolated_to_owned_job(self):
        observed={};capture=self.root/'job-capture';capture.mkdir()
        def run(command,path,timeout,**kwargs):observed.update(command=command,env=kwargs['env']);return dict(passed=True)
        with self.context(),patch.object(cli,'os',types.SimpleNamespace(**dict(vars(os),name='posix'))),\
             patch.object(cli,'bounded_module',return_value=types.SimpleNamespace(run_bounded=run)),\
             patch.dict(os.environ,CUDA_CACHE_PATH='original-cache'):
            cli.run_job(capture,'cuda',60,module_only=True)
            self.assertEqual(os.environ['CUDA_CACHE_PATH'],'original-cache')
        self.assertIn('--module-only',observed['command']);self.assertNotIn('--compile-only',observed['command'])
        self.assertEqual(observed['env']['CUDA_CACHE_PATH'],str(capture/'driver-cache'))
        self.assertTrue((capture/'driver-cache').is_dir())


if __name__=='__main__':unittest.main()
