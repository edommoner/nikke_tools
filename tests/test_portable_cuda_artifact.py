"""NVRTC transport contracts on CPU: no driver load, contexts or GPU dispatch."""
import ctypes as C
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import compile_cuda_artifact,cuda_compile_options

class NVRTC:
    def __init__(self):self.calls=[];self.options=[];self.payload=b'\x7fELF\x00binary\x00tail\x00'
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

if __name__=='__main__':unittest.main()
