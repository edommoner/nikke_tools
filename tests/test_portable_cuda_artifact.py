"""NVRTC transport contracts on CPU: no driver load, contexts or GPU dispatch."""
import ctypes as C
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock
import contextlib
import types
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import compile_cuda_artifact,cuda_compile_options

class NVRTC:
    def __init__(self):self.calls=[];self.options=[];self.payload=b'\x7fELF\x00binary\x00tail\x00'
    def nvrtcVersion(self,major,minor):
        self.calls.append('version');C.cast(major,C.POINTER(C.c_int))[0]=12;C.cast(minor,C.POINTER(C.c_int))[0]=4;return 0
    def nvrtcCreateProgram(self,out,*args):self.calls.append('create');C.cast(out,C.POINTER(C.c_void_p))[0]=C.c_void_p(1);return 0
    def nvrtcCompileProgram(self,program,count,options):self.calls.append('compile');self.options=list(options[:count]);return 0
    def nvrtcGetProgramLogSize(self,p,out):C.cast(out,C.POINTER(C.c_size_t))[0]=1;return 0
    def nvrtcGetProgramLog(self,p,out):C.memmove(out,b'\x00',1);return 0
    def nvrtcGetCUBINSize(self,p,out):self.calls.append('cubin_size');C.cast(out,C.POINTER(C.c_size_t))[0]=len(self.payload);return 0
    def nvrtcGetCUBIN(self,p,out):self.calls.append('cubin');C.memmove(out,self.payload,len(self.payload));return 0
    def nvrtcGetPTXSize(self,p,out):self.calls.append('ptx_size');C.cast(out,C.POINTER(C.c_size_t))[0]=len(self.payload);return 0
    def nvrtcGetPTX(self,p,out):self.calls.append('ptx');C.memmove(out,self.payload,len(self.payload));return 0
    def nvrtcDestroyProgram(self,p):self.calls.append('destroy');return 0

class ArtifactTests(unittest.TestCase):
    def test_split_compile_is_bounded_and_keeps_default_options_exact(self):
        with patch.dict(os.environ,{'NIKKE_CUDA_SPLIT_COMPILE':'1'}):
            self.assertEqual(cuda_compile_options('ptx'),['--std=c++17','--gpu-architecture=compute_86','--fmad=false'])
        with patch.dict(os.environ,{'NIKKE_CUDA_SPLIT_COMPILE':'2'}):
            self.assertEqual(cuda_compile_options('ptx'),['--std=c++17','--gpu-architecture=compute_86','--fmad=false','--split-compile=2'])
        for invalid in ('0','3','-1','','02','2.0','all'):
            with self.subTest(invalid=invalid),patch.dict(os.environ,{'NIKKE_CUDA_SPLIT_COMPILE':invalid}),self.assertRaises(ValueError):
                cuda_compile_options('ptx')

    def test_split_compile_has_separate_cache_and_warm_hit_never_loads_compiler(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':folder,'NIKKE_CUDA_CACHE_REQUIRED':'0','NIKKE_CUDA_PTXAS_OPT_LEVEL':'','NIKKE_CUDA_SPLIT_COMPILE':'1'}):
            dll=Path(folder)/'nvrtc.dll';dll.write_bytes(b'compiler');lib=NVRTC()
            _,serial=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='ptx')
            self.assertNotIn('version',lib.calls)
            with patch.dict(os.environ,{'NIKKE_CUDA_SPLIT_COMPILE':'2'}):
                _,parallel=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='ptx')
                self.assertNotEqual(serial['key'],parallel['key'])
                self.assertIn('--split-compile=2',parallel['identity']['options'])
                self.assertIn(b'--fmad=false',lib.options)
                self.assertEqual(lib.calls.count('version'),1)
                with patch.dict(os.environ,{'NIKKE_CUDA_CACHE_REQUIRED':'1'}):
                    _,warm=compile_cuda_artifact(None,b'cuda',[dll],artifact_kind='ptx',library_factory=lambda:self.fail('No compiler load on a cache hit'))
                self.assertTrue(warm['hit']);self.assertEqual(warm['key'],parallel['key'])

    def test_split_compile_rejects_unvalidated_versions_before_program_creation(self):
        for version in ((11,3),(12,3),(13,4)):
            class Other(NVRTC):
                def nvrtcVersion(self,major,minor):
                    self.calls.append('version')
                    C.cast(major,C.POINTER(C.c_int))[0]=version[0]
                    C.cast(minor,C.POINTER(C.c_int))[0]=version[1]
                    return 0
            with self.subTest(version=version),tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':folder,'NIKKE_CUDA_CACHE_REQUIRED':'0','NIKKE_CUDA_PTXAS_OPT_LEVEL':'','NIKKE_CUDA_SPLIT_COMPILE':'2'}):
                dll=Path(folder)/'nvrtc.dll';dll.write_bytes(b'compiler');lib=Other()
                with self.assertRaisesRegex(ValueError,'requires verified NVRTC12.4'):
                    compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='ptx')
                self.assertEqual(lib.calls,['version'])

    def test_source_cache_hit_required_miss_and_corruption_do_not_load_nvrtc(self):
        import portable_backend as backend
        import json
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'bin').mkdir();dll=root/'bin/nvrtc64_dummy.dll';dll.write_bytes(b'compiler')
            builtins=root/'bin/nvrtc-builtins64_dummy.dll';builtins.write_bytes(b'companion')
            source=root/'generated.cu';source.write_bytes(b'cuda');cache=root/'cache'
            env=dict(CUDA_PATH=str(root),NIKKE_CUDA_COMPILE_CACHE=str(cache),NIKKE_CUDA_CACHE_REQUIRED='0',NIKKE_CUDA_PTXAS_OPT_LEVEL='',NIKKE_CUDA_SPLIT_COMPILE=os.environ.get('NIKKE_CUDA_SPLIT_COMPILE','1'))
            fake_os=types.SimpleNamespace(name='nt',environ=env,add_dll_directory=lambda path:contextlib.nullcontext())
            with patch.dict(os.environ,env):
                artifact,receipt=compile_cuda_artifact(NVRTC(),b'cuda',[dll,builtins],artifact_kind='cubin')
                with patch.object(backend,'os',fake_os),patch.object(C,'WinDLL',side_effect=AssertionError('DLL load forbidden'),create=True) as loader:
                    actual,hit=backend.compile_cuda_source(source,artifact_kind='cubin')
                    self.assertEqual(actual,artifact);self.assertTrue(hit['hit'])
                    self.assertEqual(source.with_suffix('.cubin').read_bytes(),artifact)
                    with patch.dict(env,{'NIKKE_CUDA_CACHE_REQUIRED':'1'}):
                        source.write_bytes(b'different')
                        with self.assertRaisesRegex(RuntimeError,'required cache miss'):backend.compile_cuda_source(source,artifact_kind='cubin')
                    source.write_bytes(b'cuda')
                    path=cache/(receipt['key']+'.json');saved=json.loads(path.read_text());saved['artifact_bytes']+=1;path.write_text(json.dumps(saved))
                    with self.assertRaisesRegex(ValueError,'integrity'):backend.compile_cuda_source(source,artifact_kind='cubin')
                    loader.assert_not_called()

    def test_shared_source_compiler_loads_only_nvrtc_and_publishes_native_bytes(self):
        import portable_backend as backend
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'bin').mkdir();dll=root/'bin/nvrtc64_dummy.dll';dll.write_bytes(b'compiler')
            builtins=root/'bin/nvrtc-builtins64_dummy.dll';builtins.write_bytes(b'companion')
            source=root/'generated.cu';source.write_bytes(b'cuda');native=NVRTC()
            library=types.SimpleNamespace(**{name:Mock(wraps=getattr(native,name)) for name in dir(native) if name.startswith('nvrtc')})
            env=dict(CUDA_PATH=str(root),NIKKE_CUDA_COMPILE_CACHE='',NIKKE_CUDA_CACHE_REQUIRED='0')
            fake_os=types.SimpleNamespace(name='nt',environ=env,add_dll_directory=lambda path:contextlib.nullcontext())
            companion=object()
            with patch.object(backend,'os',fake_os),patch.object(C,'WinDLL',side_effect=[library,companion],create=True) as loader:
                artifact,receipt=backend.compile_cuda_source(source,artifact_kind='cubin')
            self.assertEqual([call.args[0] for call in loader.call_args_list],[str(dll),str(builtins)])
            self.assertIs(library._nikke_builtins,companion)
            self.assertEqual(set(receipt['identity']['compiler_files']),{dll.name,builtins.name})
            self.assertEqual(source.with_suffix('.cubin').read_bytes(),native.payload)
            self.assertEqual(artifact,native.payload);self.assertFalse(receipt['hit'])

    def test_missing_or_ambiguous_companions_stop_before_library_load_or_cache_work(self):
        import portable_backend as backend
        for names in (['nvrtc64_dummy.dll'],['nvrtc64_a.dll','nvrtc64_b.dll','nvrtc-builtins64_a.dll'],['nvrtc64_a.dll','nvrtc-builtins64_a.dll','nvrtc-builtins64_b.dll']):
            with self.subTest(names=names),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);(root/'bin').mkdir()
                for name in names:(root/'bin'/name).write_bytes(b'dll')
                source=root/'generated.cu';source.write_bytes(b'cuda')
                fake_os=types.SimpleNamespace(name='nt',environ=dict(CUDA_PATH=str(root)))
                with patch.object(backend,'os',fake_os),patch.object(C,'WinDLL',create=True) as loader,patch.object(backend,'compile_cuda_artifact') as compile:
                    with self.assertRaisesRegex(RuntimeError,'exactly one'):backend.compile_cuda_source(source,artifact_kind='cubin')
                loader.assert_not_called();compile.assert_not_called()

    def test_companion_load_failure_stops_before_create_program_and_preserves_error(self):
        import portable_backend as backend
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'bin').mkdir()
            for name in ('nvrtc64_dummy.dll','nvrtc-builtins64_dummy.dll'):(root/'bin'/name).write_bytes(b'dll')
            source=root/'generated.cu';source.write_bytes(b'cuda');native=NVRTC()
            library=types.SimpleNamespace(**{name:Mock(wraps=getattr(native,name)) for name in dir(native) if name.startswith('nvrtc')})
            env=dict(CUDA_PATH=str(root),NIKKE_CUDA_COMPILE_CACHE=str(root/'cache'),NIKKE_CUDA_CACHE_REQUIRED='0')
            fake_os=types.SimpleNamespace(name='nt',environ=env,add_dll_directory=lambda p:contextlib.nullcontext())
            with patch.dict(os.environ,env),patch.object(backend,'os',fake_os),patch.object(C,'WinDLL',side_effect=[library,OSError('Companion dependency missing')],create=True):
                with self.assertRaisesRegex(OSError,'Companion dependency missing'):backend.compile_cuda_source(source,artifact_kind='cubin')
            self.assertEqual(native.calls,[]);self.assertEqual(list((root/'cache').iterdir()),[])
            self.assertFalse(source.with_suffix('.cubin').exists())

    def test_required_cache_miss_never_creates_a_compiler_program(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':folder,'NIKKE_CUDA_CACHE_REQUIRED':'1'}):
            dll=Path(folder)/'nvrtc.dll';dll.write_bytes(b'compiler');lib=NVRTC()
            with self.assertRaisesRegex(RuntimeError,'required cache miss'):
                compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
            self.assertEqual(lib.calls,[])

    def test_explicit_ptxas_level_has_a_distinct_key_and_required_hit_skips_compile(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':folder,'NIKKE_CUDA_CACHE_REQUIRED':'0','NIKKE_CUDA_PTXAS_OPT_LEVEL':''}):
            dll=Path(folder)/'nvrtc.dll';dll.write_bytes(b'compiler');lib=NVRTC()
            _,original=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
            with patch.dict(os.environ,{'NIKKE_CUDA_PTXAS_OPT_LEVEL':'1'}):
                a,lower=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
                self.assertNotEqual(original['key'],lower['key']);self.assertEqual(lib.options[-2:],[b'--ptxas-options',b'-O1'])
                with patch.dict(os.environ,{'NIKKE_CUDA_CACHE_REQUIRED':'1'}):
                    b,hit=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
                    self.assertEqual(a,b);self.assertTrue(hit['hit']);self.assertEqual(lib.calls.count('compile'),2)
            for kind,level in [('ptx',1),('cubin',-1),('cubin',4),('cubin',True)]:
                with self.assertRaises(ValueError):cuda_compile_options(kind,level)

    def test_native_object_preserves_all_binary_bytes_and_warm_hit_skips_nvrtc(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':folder}):
            dll=Path(folder)/'nvrtc.dll';dll.write_bytes(b'compiler');lib=NVRTC()
            a,receipt=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
            self.assertEqual(a,lib.payload);self.assertIn(b'--gpu-architecture=sm_86',lib.options)
            self.assertIn(b'--fmad=false',lib.options);self.assertEqual(receipt['identity']['artifact'],'cubin')
            b,warm=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
            self.assertEqual(a,b);self.assertTrue(warm['hit']);self.assertEqual(lib.calls.count('compile'),1)
            self.assertNotIn('ptx',lib.calls);self.assertEqual(lib.calls.count('destroy'),1)

    def test_ptx_is_explicit_and_has_a_separate_cache_identity(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':folder}):
            dll=Path(folder)/'nvrtc.dll';dll.write_bytes(b'compiler');lib=NVRTC()
            _,a=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='ptx')
            self.assertIn(b'--gpu-architecture=compute_86',lib.options)
            _,b=compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
            self.assertNotEqual(a['key'],b['key']);self.assertEqual(lib.calls.count('compile'),2)

    def test_invalid_format_never_compiles_and_empty_object_is_destroyed(self):
        lib=NVRTC()
        with self.assertRaises(ValueError):cuda_compile_options('other')
        lib.payload=b''
        with patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':''}),self.assertRaisesRegex(RuntimeError,'empty cubin'):
            compile_cuda_artifact(lib,b'cuda',[],artifact_kind='cubin')
        self.assertEqual(lib.calls[-1],'destroy')

    def test_ptx_data_cannot_be_loaded_as_a_native_object(self):
        lib=NVRTC();lib.payload=b'PTX text\x00'
        with patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':''}),self.assertRaisesRegex(RuntimeError,'native ELF'):
            compile_cuda_artifact(lib,b'cuda',[],artifact_kind='cubin')
        self.assertEqual(lib.calls[-1],'destroy')

    def test_invalid_native_artifact_is_not_published_to_cache(self):
        lib=NVRTC();lib.payload=b'not an ELF object'
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'NIKKE_CUDA_COMPILE_CACHE':folder}):
            dll=Path(folder)/'nvrtc.dll';dll.write_bytes(b'compiler')
            with self.assertRaisesRegex(RuntimeError,'native ELF'):
                compile_cuda_artifact(lib,b'cuda',[dll],artifact_kind='cubin')
            self.assertEqual(list(Path(folder).glob('*.json')),[])
            self.assertEqual(lib.calls[-1],'destroy')

    def test_context_cleanup_error_keeps_the_original_module_failure(self):
        import portable_backend as backend
        def create(out,*args):C.cast(out,C.POINTER(C.c_void_p))[0]=C.c_void_p(1);return 0
        functions=('cuInit','cuDeviceGet','cuDeviceGetName','cuDeviceComputeCapability','cuCtxCreate_v2',
            'cuCtxDestroy_v2','cuModuleLoadData','cuModuleGetFunction','cuModuleGetGlobal_v2',
            'cuMemAlloc_v2','cuMemcpyHtoD_v2','cuMemcpyDtoH_v2','cuCtxSynchronize','cuLaunchKernel')
        driver=types.SimpleNamespace(**{name:Mock(return_value=0) for name in functions})
        driver.cuCtxCreate_v2.side_effect=create
        driver.cuModuleLoadData.return_value=77;driver.cuCtxDestroy_v2.return_value=55
        fake_os=types.SimpleNamespace(name='nt',environ={'NIKKE_CUDA_ARTIFACT':'ptx'})
        with patch.object(backend,'os',fake_os),patch.object(backend,'compile_cuda_source',return_value=(b'ptx',{})),patch.object(C,'WinDLL',return_value=driver,create=True):
            with self.assertRaisesRegex(RuntimeError,'cuModuleLoadData: CUDA error 77') as caught:
                backend.execute_cuda_batches(Path('unused'), 'entry',[bytes.fromhex('01000000')],[4],[1])
        self.assertIn('cuCtxDestroy_v2: CUDA error 55',caught.exception.__notes__[0])
        driver.cuCtxDestroy_v2.assert_called_once()

if __name__=='__main__':unittest.main()
