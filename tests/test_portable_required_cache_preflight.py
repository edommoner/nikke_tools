"""Paired-required cache misses precede expensive CPU work and execution claim."""
import contextlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_backend as backend
from portable_compile_cache import get_or_compile
s=importlib.util.spec_from_file_location('required_cache_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
class StopAfterCache(Exception):pass
class WindowsNameOnly:
    name='nt'
    def __getattr__(self,name):return getattr(os,name)

class RequiredCachePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'gpu').mkdir();(self.root/'research/portable-build').mkdir(parents=True)
        self.source='gpu/main.slang';(self.root/self.source).write_bytes(b'#define PORTABLE_RESIDENT_RUNTIME\n')
        self.outputs={kind:self.root/('research/portable-build/main.'+suffix) for kind,suffix in [('cuda','cu'),('metal','metal')]}
        for k,p in self.outputs.items():p.write_bytes(('synthetic '+k).encode())
        self.hashes={self.source:cli.sha((self.root/self.source).read_bytes())};self.normal={k:cli.sha(p.read_bytes()) for k,p in self.outputs.items()}
        self.m=dict(suite='cache-unit',purpose='sealed',package_id='synthetic-cache-unit',golden=dict(source_sha256=self.hashes,generated_normalized=dict(self.normal)))
        self.cuda=self.root/'cuda';(self.cuda/'bin').mkdir(parents=True);self.files=[self.cuda/'bin/nvrtc64_fixture.dll',self.cuda/'bin/nvrtc-builtins64_fixture.dll']
        for p in self.files:p.write_bytes(b'synthetic compiler')
        self.cache=self.root/'compile-cache';self.capture=self.root/'capture';self.build=Mock(return_value=(self.outputs,self.hashes));self.cpu=Mock(side_effect=StopAfterCache('CPU gate reached'))
        self.receipt=self.root/'research/portable-build/main.generation-cache.json';self.receipt.write_text(json.dumps(dict(hit=True,compiler_invocations=0)))
        slang=self.root/'slang/bin';slang.mkdir(parents=True);(slang/'slangc.exe').write_bytes(b'synthetic compiler')
        self.env=dict(NIKKE_CUDA_CACHE_REQUIRED='1',NIKKE_CUDA_COMPILE_CACHE=str(self.cache),NIKKE_CUDA_ARTIFACT='cubin',NIKKE_CUDA_PTXAS_OPT_LEVEL='',NIKKE_SLANG_GENERATION_REQUIRED='1',NIKKE_SLANG_GENERATION_CACHE=str(self.root/'generation-cache'),CUDA_PATH=str(self.cuda),NIKKE_SLANG_ROOT=str(slang.parent))
    def seed(self):get_or_compile(self.outputs['cuda'].read_bytes(),backend.cuda_compile_options('cubin'),self.files,lambda:b'\x7fELF-synthetic',self.cache,artifact_kind='cubin')
    def context(self):
        stack=contextlib.ExitStack();stack.enter_context(patch.dict(os.environ,self.env));stack.enter_context(patch.object(cli,'ROOT',self.root));stack.enter_context(patch.object(cli,'os',WindowsNameOnly()))
        stack.enter_context(patch.dict(cli.SUITES,{'cache-unit':dict(source=self.source,tests=[])}));stack.enter_context(patch.object(cli,'verify_package',return_value=self.m));stack.enter_context(patch.object(backend,'build',self.build))
        stack.enter_context(patch.object(cli,'module',return_value=types.SimpleNamespace(normalized=cli.sha)));stack.enter_context(patch.object(cli,'cpu_test_groups',self.cpu));stack.enter_context(patch.object(cli,'cpu_preflight',side_effect=AssertionError('Native work after miss')));stack.enter_context(patch.object(cli,'run_job',side_effect=AssertionError('Job after miss')))
        return stack
    def test_miss_stops_before_cpu_native_job_and_exclusive_claim(self):
        with self.context(),self.assertRaisesRegex(RuntimeError,'before CPU preflight'):cli.run_capture(self.capture,'cuda',180)
        self.cpu.assert_not_called();self.assertFalse(self.cache.exists());self.assertFalse((self.root/'gpu-claimed-cuda.json').exists());r=cli.load(self.capture/'cache-preflight.json');self.assertFalse(r['passed']);self.assertEqual(r['gpu_calls'],0);self.assertFalse(r['calculation_verified']);self.assertEqual(cli.load(self.capture/'run.json')['status'],'failed')
    def test_hit_continues_to_existing_cpu_gate_without_claim_or_gpu_proof(self):
        self.seed();before={p.name:p.read_bytes() for p in self.cache.iterdir()}
        with self.context(),self.assertRaises(StopAfterCache):cli.run_capture(self.capture,'cuda',180)
        self.cpu.assert_called_once();r=cli.load(self.capture/'cache-preflight.json');self.assertTrue(r['passed']);self.assertFalse(r['calculation_verified']);self.assertEqual(r['forbidden_attempts'],[]);self.assertEqual(before,{p.name:p.read_bytes() for p in self.cache.iterdir()});self.assertFalse((self.root/'gpu-claimed-cuda.json').exists())
    def test_generation_miss_or_wrong_source_or_unverified_hit_cannot_reach_cpu(self):
        for reason in ('generation-miss','source','normalized','unverified'):
            with self.subTest(reason=reason):
                self.capture=self.root/reason
                if reason=='generation-miss':self.build.side_effect=RuntimeError('Required Slang generation cache miss')
                if reason=='source':self.build.return_value=(self.outputs,{self.source:'0'*64})
                if reason=='normalized':self.m['golden']['generated_normalized']['cuda']='0'*64
                if reason=='unverified':self.receipt.write_text(json.dumps(dict(hit=False,compiler_invocations=2)))
                with self.context(),self.assertRaises((RuntimeError,ValueError)):cli.run_capture(self.capture,'cuda',180)
                self.cpu.assert_not_called();self.assertFalse((self.root/'gpu-claimed-cuda.json').exists());self.build.side_effect=None;self.build.return_value=(self.outputs,self.hashes);self.m['golden']['generated_normalized']=dict(self.normal)
    def test_library_or_process_attempts_are_blocked_before_cpu(self):
        for operation in ('library','process','generation'):
            self.capture=self.root/operation
            def attempted(*args,**kwargs):
                if operation=='library':backend.C.WinDLL('nvrtc.dll')
                elif operation=='process':backend.subprocess.run(['forbidden'])
                else:backend._build_resident(None,None,None,None,None)
            self.build.side_effect=attempted
            with self.context(),self.assertRaisesRegex(RuntimeError,'forbids'):cli.run_capture(self.capture,'cuda',180)
            self.cpu.assert_not_called();self.assertFalse((self.root/'gpu-claimed-cuda.json').exists())
    def test_nonpaired_cpu_only_and_smoke_keep_original_gate(self):
        for label,change,options in [('no-generation-require',{'NIKKE_SLANG_GENERATION_REQUIRED':'0'},{}),('cpu-only',{},dict(cpu_only=True)),('smoke',{},dict(smoke=True))]:
            self.capture=self.root/label
            with self.context(),patch.dict(os.environ,change),self.assertRaises(StopAfterCache):cli.run_capture(self.capture,'cuda',180,**options)
            self.assertFalse((self.capture/'cache-preflight.json').exists());self.build.assert_not_called()
    def test_generation_only_requirement_checks_before_cpu_on_cuda_or_metal(self):
        for kind in ('cuda','metal'):
            self.capture=self.root/('generation-only-'+kind)
            with self.context(),patch.dict(os.environ,{'NIKKE_CUDA_CACHE_REQUIRED':'0'}),self.assertRaises(StopAfterCache):cli.run_capture(self.capture,kind,180)
            self.assertTrue(cli.load(self.capture/'generation-preflight.json')['passed']);self.assertFalse((self.capture/'cache-preflight.json').exists())
            self.assertFalse((self.root/('gpu-claimed-'+kind+'.json')).exists())
    def test_generation_miss_on_metal_cannot_consume_claim_or_cpu(self):
        self.build.side_effect=RuntimeError('Required Slang generation cache miss')
        with self.context(),self.assertRaisesRegex(RuntimeError,'generation cache miss'):cli.run_capture(self.capture,'metal',180)
        self.cpu.assert_not_called();self.assertFalse((self.root/'gpu-claimed-metal.json').exists())
    def test_development_generation_snapshot_does_not_invent_sealed_numeric_proof(self):
        self.m['purpose']='development';self.m['golden'].pop('generated_normalized')
        with self.context(),self.assertRaises(StopAfterCache):cli.run_capture(self.capture,'metal',180)
        r=cli.load(self.capture/'generation-preflight.json');self.assertFalse(r['sealed_generated_baseline_verified']);self.assertFalse(r['calculation_verified'])
    def test_missing_directories_and_invalid_flags_stop_before_cpu(self):
        for i,change in enumerate([{'NIKKE_CUDA_COMPILE_CACHE':''},{'NIKKE_SLANG_GENERATION_CACHE':''},{'NIKKE_CUDA_CACHE_REQUIRED':'2'},{'NIKKE_SLANG_GENERATION_REQUIRED':'invalid'}]):
            self.capture=self.root/('invalid-'+str(i))
            with self.context(),patch.dict(os.environ,change),self.assertRaises(ValueError):cli.run_capture(self.capture,'cuda',180)
            self.cpu.assert_not_called();self.build.assert_not_called();self.assertFalse((self.root/'gpu-claimed-cuda.json').exists())

if __name__=='__main__':unittest.main()
