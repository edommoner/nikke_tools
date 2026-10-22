"""Read the actual inherited Job memory cap with the shared Windows x64 ABI."""
import ctypes as C,importlib.util,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_job_limits import BasicLimitInformation,ExtendedLimitInformation,read_job_limits


class Query:
    def __init__(self):self.calls=[];self.flags=0x2200;self.cap=2147483648;self.peak=37257216;self.success=True;self.returned=144
    def __call__(self,handle,kind,output,size,returned):
        self.calls.append((handle,kind,size))
        limits=C.cast(output,C.POINTER(ExtendedLimitInformation)).contents
        limits.basic.flags=self.flags;limits.job_mem=self.cap;limits.peak_job=self.peak
        C.cast(returned,C.POINTER(C.c_uint32)).contents.value=self.returned
        return int(self.success)


class JobLimitsTests(unittest.TestCase):
    def test_shared_structure_has_the_windows_x64_extended_limit_layout(self):
        self.assertEqual(C.sizeof(BasicLimitInformation),64);self.assertEqual(C.sizeof(ExtendedLimitInformation),144)
        self.assertEqual(ExtendedLimitInformation.job_mem.offset,120);self.assertEqual(ExtendedLimitInformation.peak_job.offset,136)
        self.assertEqual(BasicLimitInformation.flags.offset,16)
    def test_null_handle_reads_the_current_job_instead_of_leaving_native_cap_unknown(self):
        query=Query();dll=types.SimpleNamespace(QueryInformationJobObject=query)
        self.assertEqual(read_job_limits(dll,None),dict(job_memory_limit_bytes=2147483648,job_peak_memory_bytes=37257216))
        self.assertEqual(query.calls,[(None,9,144)])
    def test_explicit_job_handle_and_disabled_cap_are_distinguished(self):
        query=Query();query.flags=0x2000;dll=types.SimpleNamespace(QueryInformationJobObject=query)
        self.assertIsNone(read_job_limits(dll,456)['job_memory_limit_bytes']);self.assertEqual(query.calls,[(456,9,144)])
    def test_success_with_an_incomplete_response_is_not_a_memory_cap_proof(self):
        query=Query();dll=types.SimpleNamespace(QueryInformationJobObject=query)
        for returned in (0,80,145):
            query.returned=returned
            with self.subTest(returned=returned),self.assertRaisesRegex(RuntimeError,'Incomplete'):read_job_limits(dll,None)
    def test_query_failure_never_becomes_a_zero_or_missing_cap_success(self):
        query=Query();query.success=False;dll=types.SimpleNamespace(QueryInformationJobObject=query)
        with patch.object(C,'WinError',side_effect=OSError('query denied'),create=True),patch.object(C,'get_last_error',return_value=5,create=True):
            with self.assertRaisesRegex(OSError,'query denied'):read_job_limits(dll,None)
    def test_observer_always_queries_limits_even_without_an_explicit_job_class(self):
        import windows_validation_observer as observer
        # Execute the real observer with synthetic process APIs and a NULL Job.
        query=Query()
        class Function:
            def __init__(self,fn):self.fn=fn
            def __call__(self,*args):return self.fn(*args)
        def times(handle,created,*args):C.cast(created,C.POINTER(C.c_uint64)).contents.value=123;return 1
        def first(handle,pointer):
            # inspect_job passes its concrete ProcessEntry through byref.
            entry=pointer._obj;entry.pid=200;entry.parent=os.getpid();return 1
        def information(handle,kind,output,size,returned):
            if kind==9:return query(handle,kind,output,size,returned)
            C.memmove(output,(C.c_uint32*2)(2,2),8)
            C.memmove(C.addressof(output)+8,(C.c_size_t*2)(os.getpid(),200),16);return 1
        dll=types.SimpleNamespace(**{name:Function(fn) for name,fn in dict(QueryInformationJobObject=information,GetProcessTimes=times,CreateToolhelp32Snapshot=lambda *args:99,Process32FirstW=first,Process32NextW=lambda *args:0,CloseHandle=lambda *args:1).items()})
        with patch.object(observer,'os',types.SimpleNamespace(**dict(vars(os),name='nt'))):
            result=observer.inspect_job(types.SimpleNamespace(dll=dll,handle=None),types.SimpleNamespace(_handle=100,pid=200))
        self.assertEqual(result['job_memory_limit_bytes'],2147483648);self.assertEqual(result['job_peak_memory_bytes'],37257216)
        self.assertEqual(query.calls,[(None,9,144)]);self.assertEqual(result['job_members'],sorted([os.getpid(),200]))


if __name__=='__main__':unittest.main()
