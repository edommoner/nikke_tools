"""Versioned nvJitLink primitive and clean failure with synthetic C functions."""
import ctypes as C,hashlib,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_jit_link as jit
from test_portable_partition_object import relocatable
from test_portable_device_linker import cubin


class Function:
    def __init__(self,owner,name):self.owner=owner;self.name=name
    def __call__(self,*args):return self.owner.call(self.name,*args)


class Library:
    def __init__(self):
        self.calls=[];self.fail=None;self.destroy_fail=False;self.version=[12,4];self.data=None;self.payload=cubin();self.size_override=None;self.error_log=b'';self.info_log=b'linked synthetic image';self.handle_on_create_failure=False
        for name in ('Version','Create','Destroy','AddData','Complete','GetLinkedCubinSize','GetLinkedCubin','GetErrorLogSize','GetErrorLog','GetInfoLogSize','GetInfoLog'):setattr(self,jit.symbol(name),Function(self,name))
    def call(self,name,*args):
        self.calls.append(name)
        if name=='Create' and (self.fail!=name or self.handle_on_create_failure):C.cast(args[0],C.POINTER(C.c_void_p)).contents.value=123
        if self.fail==name:return 3
        if name=='Version':
            C.cast(args[0],C.POINTER(C.c_uint)).contents.value=self.version[0];C.cast(args[1],C.POINTER(C.c_uint)).contents.value=self.version[1]
        elif name=='Create':
            self.options=[args[2][i].decode() for i in range(args[1])]
        elif name=='AddData':

            if args[1]!=1 or args[4]!=b'module.relocatable.cubin':raise AssertionError('Expected raw device CUBIN input')
            self.data=C.string_at(args[2],args[3])
        elif name=='GetLinkedCubinSize':C.cast(args[1],C.POINTER(C.c_size_t)).contents.value=len(self.payload) if self.size_override is None else self.size_override
        elif name=='GetLinkedCubin':C.memmove(args[1],self.payload,len(self.payload))
        elif name.endswith('LogSize'):
            value=self.error_log if 'Error' in name else self.info_log;C.cast(args[1],C.POINTER(C.c_size_t)).contents.value=len(value)+1
        elif name.endswith('Log'):
            value=self.error_log if 'Error' in name else self.info_log;C.memmove(args[1],value+b'\0',len(value)+1)
        elif name=='Destroy':
            if self.destroy_fail:return 3
            C.cast(args[0],C.POINTER(C.c_void_p)).contents.value=None
        return 0


class JitLinkTests(unittest.TestCase):
    def test_library_identity_is_file_only_and_rejects_changed_dll(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'nvJitLink_120_0.dll';path.write_bytes(b'MZsynthetic DLL')
            with patch.object(jit,'TOOL_SHA256',hashlib.sha256(path.read_bytes()).hexdigest()):
                result=jit.validate_library(path);self.assertEqual(result['version'],'12.4.127')
                path.write_bytes(b'MZchanged')
                with self.assertRaisesRegex(ValueError,'pinned'):jit.validate_library(path)
    def test_non_regular_or_non_pe_library_is_rejected_before_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'not-dll';path.write_bytes(b'other')
            with patch.object(jit,'TOOL_SHA256',hashlib.sha256(path.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,'pinned'):jit.validate_library(path)
            with self.assertRaisesRegex(ValueError,'regular'):jit.validate_library(Path(folder))
    def test_versioned_cubin_in_memory_and_shared_output_validator(self):
        lib=Library();raw=relocatable();artifact,result=jit.link_cubin(lib,raw)
        self.assertEqual(artifact,cubin());self.assertEqual(lib.data,raw);self.assertEqual(lib.options,['-arch=sm_86','-verbose'])
        self.assertEqual(result['api_version'],[12,4]);self.assertEqual(result['artifact']['static_bindings']['SLANG_globalParams']['bytes'],48)
        self.assertFalse(result['source_origin_verified']);self.assertFalse(result['containment_verified']);self.assertFalse(result['calculation_verified'])
        self.assertEqual(result['program_driver_api_calls'],0);self.assertEqual(lib.calls.count('Destroy'),1)
        self.assertEqual(lib.calls[:4],['Version','Create','AddData','Complete']);self.assertEqual(lib.calls[-1],'Destroy')
    def test_wrong_version_and_invalid_input_cannot_create_link_handle(self):
        lib=Library();lib.version=[12,5]
        with self.assertRaises(jit.JitLinkError):jit.link_cubin(lib,relocatable())
        self.assertEqual(lib.calls,['Version']);lib=Library()
        for raw in (b'wrong',bytearray(relocatable())):
            with self.subTest(raw=type(raw)),self.assertRaises(ValueError):jit.link_cubin(lib,raw)
        self.assertEqual(lib.calls,[])
    def test_link_failure_preserves_logs_and_destroys_once_without_retry(self):
        lib=Library();lib.fail='Complete';lib.error_log=b'link failed'
        with self.assertRaises(jit.JitLinkError) as raised:jit.link_cubin(lib,relocatable())
        diagnostic=raised.exception.diagnostic;self.assertIn('Complete',diagnostic['failure']);self.assertEqual(diagnostic['error_log'],'link failed')
        self.assertEqual(lib.calls.count('Complete'),1);self.assertEqual(lib.calls.count('Destroy'),1);self.assertNotIn('GetLinkedCubin',lib.calls)
    def test_create_failure_cleans_only_a_returned_handle(self):
        for returned in (False,True):
            lib=Library();lib.fail='Create';lib.handle_on_create_failure=returned
            with self.subTest(returned=returned),self.assertRaises(jit.JitLinkError):jit.link_cubin(lib,relocatable())
            self.assertEqual(lib.calls.count('Destroy'),int(returned));self.assertNotIn('AddData',lib.calls)
    def test_bad_size_or_incomplete_elf_cannot_be_published(self):
        for size,payload in ((0,cubin()),(2147483648,cubin()),(None,b'not ELF')):
            lib=Library();lib.size_override=size;lib.payload=payload
            with self.subTest(size=size),self.assertRaises(jit.JitLinkError):jit.link_cubin(lib,relocatable())
            self.assertEqual(lib.calls.count('Destroy'),1)
    def test_destroy_error_is_never_success_and_does_not_hide_original_failure(self):
        lib=Library();lib.destroy_fail=True
        with self.assertRaises(jit.JitLinkError) as raised:jit.link_cubin(lib,relocatable())
        self.assertIsNotNone(raised.exception.diagnostic['cleanup_error']);self.assertEqual(lib.calls.count('Destroy'),1)
        lib=Library();lib.fail='Complete';lib.destroy_fail=True
        with self.assertRaises(jit.JitLinkError) as raised:jit.link_cubin(lib,relocatable())
        self.assertIn('Complete',raised.exception.diagnostic['failure']);self.assertIsNotNone(raised.exception.diagnostic['cleanup_error'])
    def test_log_api_failure_or_error_log_on_success_is_not_an_artifact(self):
        for failed,error in (('GetInfoLog',b''),(None,b'unexpected error')):
            lib=Library();lib.fail=failed;lib.error_log=error
            with self.subTest(failed=failed),self.assertRaises(jit.JitLinkError):jit.link_cubin(lib,relocatable())
            self.assertEqual(lib.calls.count('Destroy'),1);self.assertEqual(lib.calls.count('GetInfoLogSize'),1)


if __name__=='__main__':unittest.main()
