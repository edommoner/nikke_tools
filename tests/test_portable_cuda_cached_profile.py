"""Cached execution cannot silently become another cold compilation."""
import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_backend
import portable_cuda_cached_profile as profile
from portable_phase_audit import Journal

class CachedProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.config=dict(cuda_cache_profile=profile.PROFILE)
        self.source=self.root/'generated.cu';self.source.write_bytes(b'candidate-source')
        self.env=dict(NIKKE_CUDA_CACHE_REQUIRED='1',NIKKE_CUDA_COMPILE_CACHE=str(self.root),NIKKE_CUDA_ARTIFACT='cubin',NIKKE_CUDA_PTXAS_OPT_LEVEL='1',NIKKE_CUDA_PREFLIGHT_SOURCE=str(self.source))
    def test_actual_execution_requires_cached_cubin_and_exact_options(self):
        self.assertTrue(profile.validate(self.config,'cuda',environment=self.env))
        for key,value in [('NIKKE_CUDA_CACHE_REQUIRED','0'),('NIKKE_CUDA_COMPILE_CACHE','relative-cache'),('NIKKE_CUDA_COMPILE_CACHE',str(self.root/'missing')),('NIKKE_CUDA_ARTIFACT','ptx'),('NIKKE_CUDA_PTXAS_OPT_LEVEL','0'),('NIKKE_CUDA_PREFLIGHT_SOURCE','')]:
            with self.assertRaises(ValueError):profile.validate(self.config,'cuda',environment=dict(self.env,**{key:value}))
        for kwargs in [dict(backend='metal'),dict(backend='cuda',linked=True)]:
            with self.assertRaises(ValueError):profile.validate(self.config,environment=self.env,**kwargs)
    def test_cpu_and_ordinary_profiles_keep_existing_scope(self):
        self.assertFalse(profile.validate(self.config,'metal',execute=False,environment={}))
        self.assertFalse(profile.validate({},'cuda',environment={}))
        with self.assertRaises(ValueError):profile.validate(dict(cuda_cache_profile='unknown'),'cuda',execute=False)
    def test_nvrtc_and_builtins_are_blocked_before_native_loader(self):
        journal=Journal(self.root/'phase.jsonl')
        with patch.dict(os.environ,self.env),patch.object(portable_backend.C,'WinDLL',create=True) as win,patch.object(portable_backend.C,'CDLL') as cd:
            with profile.library_guard(self.config,'cuda',journal):
                for loader in ('WinDLL','CDLL'):
                    for name in ['nvrtc64_120_0.dll','C:/SDK/NVRTC-BUILTINS64_124.dll']:
                        with self.assertRaisesRegex(RuntimeError,'NVRTC library forbidden'):getattr(portable_backend.C,loader)(name)
            win.assert_not_called();cd.assert_not_called()
        rows=[json.loads(x) for x in (self.root/'phase.jsonl').read_text().splitlines()]
        self.assertEqual(sum(r['state']=='rejected' for r in rows),4)
    def test_driver_loader_is_forwarded_and_restored(self):
        journal=Journal(self.root/'phase.jsonl');sentinel=object()
        with patch.dict(os.environ,self.env),patch.object(portable_backend.C,'WinDLL',return_value=sentinel,create=True) as load:
            with profile.library_guard(self.config,'cuda',journal):self.assertIs(portable_backend.C.WinDLL('nvcuda.dll'),sentinel)
            self.assertIs(portable_backend.C.WinDLL,load)
        load.assert_called_once_with('nvcuda.dll')
    def test_audit_demands_runtime_flag_profile_marker_and_real_hit_record(self):
        runtime=dict(cache_required='1',compile_cache_enabled=True,cuda_artifact_kind='cubin',ptxas_optimization_level='1')
        rows=[dict(stage='cuda_cache_only_profile',state='required',profile=profile.PROFILE),dict(stage='cuda_compile_cache',state='verified',receipt=dict(enabled=True,hit=True,artifact_bytes=1,key='a'*64,artifact_sha256='b'*64))]
        self.assertTrue(profile.audit(self.config,runtime,rows)['required_cache_hit_verified'])
        for candidate in [[],rows[:1],rows[1:],rows+[dict(stage='nvrtcCompileProgram',state='entered')],rows+[dict(stage='cuda_cache_only_library',state='rejected',name='nvrtc.dll')],rows+[dict(stage='cuda_cache_only_library',state='allowed',name='NVRTC.DLL')]]:
            with self.assertRaises(ValueError):profile.audit(self.config,runtime,candidate)
        with self.assertRaises(ValueError):profile.audit(self.config,dict(runtime,cache_required='0'),rows)
        self.assertIsNone(profile.audit({}, {}, []))
    def test_profile_guard_precedes_capture_worker_and_gpu_claim(self):
        import nikke_gpu as cli
        capture=self.root/'capture';manifest=dict(suite='cached-fixture',purpose='sealed')
        with patch.dict(os.environ,{'NIKKE_CUDA_CACHE_REQUIRED':'0'}),patch.object(cli,'verify_package',return_value=manifest),patch.dict(cli.SUITES,{'cached-fixture':self.config}),patch.object(cli,'cpu_test_groups',side_effect=AssertionError('CPU worker must not start')),patch.object(cli,'run_job',side_effect=AssertionError('Job must not start')):
            with self.assertRaisesRegex(ValueError,'requires --require-cache'):cli.run_capture(capture,'cuda',180)
        self.assertFalse(capture.exists())
    def test_stale_saved_source_and_required_miss_stop_without_native_calls(self):
        import nikke_gpu as cli
        manifest=dict(suite='cached-fixture',package_id='a'*64,golden=dict(generated_normalized=dict(cuda='b'*64)))
        with patch.dict(os.environ,self.env),patch.dict(cli.SUITES,{'cached-fixture':self.config}),patch.object(cli,'module',return_value=SimpleNamespace(normalized=lambda data:'a'*64)),patch.object(portable_backend,'probe_cuda_source_cache') as probe,patch.object(cli.subprocess,'run',side_effect=AssertionError('No process')):
            capture=self.root/'mismatch';capture.mkdir()
            with self.assertRaisesRegex(ValueError,'differs from the sealed Metal proof'):cli.required_cuda_cache_preflight(manifest,capture)
            probe.assert_not_called();manifest['golden']['generated_normalized']['cuda']='a'*64
            capture=self.root/'miss';capture.mkdir();probe.return_value=dict(hit=False)
            with self.assertRaisesRegex(RuntimeError,'no execution claim consumed'):cli.required_cuda_cache_preflight(manifest,capture)
            self.assertFalse(json.loads((capture/'cache-preflight.json').read_text())['passed'])
            capture=self.root/'hit';capture.mkdir();probe.return_value=dict(hit=True)
            self.assertTrue(cli.required_cuda_cache_preflight(manifest,capture))
            self.assertEqual(json.loads((capture/'cache-preflight.json').read_text())['gpu_calls'],0)

if __name__=='__main__':unittest.main()
