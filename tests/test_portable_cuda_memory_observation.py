"""CPU-only Windows ABI and CUDA observer fault injection; no real driver."""
import ctypes as C,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_cuda_memory_observation as memory
import portable_phase_audit as phase
from portable_phase_audit import Journal,NativeLibrary
from portable_admission_snapshot import digest


class MemoryObservationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.base=Path(temp.name)
        self.closed=[];self.opened=[];self.process_failure=False;self.close_ok=True;self.query_code=0;self.query_calls=0
        def info(handle,pointer,size):
            self.assertEqual(size,80);self.assertEqual(pointer._obj.cb,80)
            if self.process_failure:return 0
            pointer._obj.private_usage=1000 if handle==-1 else 2000;pointer._obj.working_set=3000;pointer._obj.peak_pagefile=4000
            return 1
        def opened(access,inherit,pid):self.opened.append((access,inherit,pid));return 97
        def closed(handle):self.closed.append(handle);return int(self.close_ok)
        def limits(handle,kind,pointer,size,returned):
            self.assertIsNone(handle);self.assertEqual(kind,9)
            pointer._obj.basic.flags=0x2200;pointer._obj.job_mem=2147483648;pointer._obj.peak_job=9876;returned._obj.value=size;return 1
        self.kernel=SimpleNamespace(GetCurrentProcess=lambda:-1,OpenProcess=opened,CloseHandle=closed,QueryInformationJobObject=limits)
        self.psapi=SimpleNamespace(GetProcessMemoryInfo=info)
        self.dll_calls=[]
        def loader(name,**kwargs):self.dll_calls.append(name);return self.kernel if name=='kernel32.dll' else self.psapi
        self.loader=loader
        def query(free,total):
            self.query_calls+=1;free._obj.value=8000;total._obj.value=16000;return self.query_code
        self.library=SimpleNamespace(cuMemGetInfo_v2=query)
    def host(self):return memory.host_memory(self.loader)
    def sampler(self):return memory.CudaMemorySampler(self.library,self.host)
    def test_fixed_x64_abi_reads_only_own_and_actual_parent_and_closes_handle(self):
        self.assertEqual(C.sizeof(memory.ProcessMemory),80);self.assertEqual(memory.ProcessMemory.private_usage.offset,72)
        r=self.host();self.assertEqual(r['process']['private_bytes'],1000);self.assertEqual(r['parent']['private_bytes'],2000)
        self.assertEqual(r['job']['job_peak_memory_bytes'],9876);self.assertEqual(r['job']['job_memory_limit_bytes'],2147483648)
        self.assertEqual(self.opened,[(0x1000,False,memory.os.getppid())]);self.assertEqual(self.closed,[97]);self.assertEqual(self.dll_calls,['kernel32.dll','psapi.dll'])
        self.assertFalse(r['atomic']);self.assertFalse(r['calculation_verified']);self.assertEqual(r['driver_calls'],0)
    def test_failed_process_query_keeps_unknown_and_still_closes_parent_handle(self):
        self.process_failure=True;r=self.host()
        self.assertFalse(r['process']['available']);self.assertNotIn('private_bytes',r['process']);self.assertEqual(self.closed,[97])
        self.assertFalse(r['parent']['available'])
    def test_parent_open_failure_and_close_failure_are_not_silently_successful(self):
        self.close_ok=False;r=self.host();self.assertFalse(r['parent']['handle_closed'])
        self.kernel.OpenProcess=lambda *a:None;r=self.host();self.assertFalse(r['parent']['available']);self.assertNotIn('private_bytes',r['parent'])
    def test_memory_query_failure_never_invents_zero_free_memory_or_cause(self):
        self.query_code=2;r=self.sampler()('cuLaunchKernel','before')
        self.assertFalse(r['device']['available']);self.assertIsNone(r['device']['free_bytes']);self.assertEqual(r['device']['return_code'],2)
        self.assertEqual(r['driver_memory_query_calls'],1);self.assertEqual(r['kernel_calls_added'],0)
    def test_host_error_does_not_replace_device_or_original_call_return_code(self):
        def failed():raise OSError('private path must not be serialized')
        r=memory.CudaMemorySampler(self.library,failed)('cuLaunchKernel','after',return_code=2)
        self.assertTrue(r['device']['available']);self.assertFalse(r['host']['available']);self.assertEqual(r['host']['reason'],'OSError')
        self.assertEqual(r['observed_call_return_code'],2);self.assertNotIn('private path',json.dumps(r))
    def test_opt_in_native_wrapper_preserves_launch_args_error_code_and_records_real_shape(self):
        path=self.base/'phases.jsonl';calls=[];token=C.c_void_p(3735928559)
        def launch(*args):calls.append(args);return 2
        self.library.cuLaunchKernel=launch
        lib=NativeLibrary(self.library,Journal(path),lambda dll:self.sampler())
        args=(token,15,1,1,1,1,1,0,token,token,token)
        self.assertEqual(lib.cuLaunchKernel(*args),2);self.assertEqual(calls,[args]);self.assertEqual(self.query_calls,2)
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        native=[r for r in rows if r['stage']=='cuLaunchKernel'];self.assertEqual(native[0]['grid'],[15,1,1]);self.assertEqual(native[0]['block'],[1,1,1]);self.assertEqual(native[0]['dynamic_shared_bytes'],0);self.assertEqual(native[1]['return_code'],2)
        self.assertNotIn('3735928559',path.read_text())
        report=memory.summarize(rows);self.assertTrue(report['launch_arguments_recorded']);self.assertTrue(report['memory_observations_present'])
        self.assertTrue(report['memory_observation_complete'])
        self.assertEqual(report['launches'][0]['return_code'],2);self.assertFalse(report['failure_cause_verified']);self.assertFalse(report['calculation_verified'])
    def test_default_observer_records_allocation_size_without_any_extra_query(self):
        path=self.base/'phases.jsonl';seen=[]
        def allocation(*args):seen.append(args);return 0
        lib=NativeLibrary(SimpleNamespace(cuMemAlloc_v2=allocation),Journal(path));output=C.c_uint64()
        args=(C.byref(output),C.c_size_t(129908160));self.assertEqual(lib.cuMemAlloc_v2(*args),0);self.assertEqual(seen,[args])
        report=memory.summarize([json.loads(line) for line in path.read_text().splitlines()])
        self.assertEqual(report['allocations'],[dict(requested_bytes=129908160,return_code=0)]);self.assertEqual(self.query_calls,0);self.assertFalse(report['memory_observations_present'])
    def test_legacy_missing_args_and_incomplete_events_stay_unknown(self):
        rows=[dict(stage='cuMemAlloc_v2',state='entered'),dict(stage='cuMemAlloc_v2',state='returned',return_code=0),dict(stage='cuLaunchKernel',state='entered')]
        r=memory.summarize(rows);self.assertIsNone(r['allocations'][0]['requested_bytes']);self.assertFalse(r['allocation_arguments_recorded']);self.assertFalse(r['launch_arguments_recorded']);self.assertEqual(r['incomplete_native_events'],['cuLaunchKernel'])
    def test_pinned_journal_summary_rejects_changed_or_invalid_event_data(self):
        path=self.base/'phases.jsonl';path.write_text(json.dumps(dict(stage='cuLaunchKernel',state='entered',grid=[15,1,1],block=[1,1,1],dynamic_shared_bytes=0))+'\n')
        original=path.read_bytes();out=self.base/'result.json';result=memory.saved_summary(path,digest(original),out)
        self.assertEqual(result['journal_sha256'],digest(original));self.assertEqual(result['diagnostic_gpu_calls'],0)
        path.write_bytes(original+b'\n')
        with self.assertRaisesRegex(ValueError,'SHA mismatch'):memory.saved_summary(path,digest(original),self.base/'bad.json')
        with self.assertRaises(ValueError):memory.summarize([dict(stage='cuMemAlloc_v2',state='returned',return_code=0)])
        with self.assertRaises(ValueError):memory.summarize([dict(stage='cuLaunchKernel',state='entered',grid=[True,1,1])])
    def test_new_api_exception_preserves_original_failure_and_no_fake_return(self):
        path=self.base/'exception.jsonl'
        def failed(*args):raise RuntimeError('original native failure')
        lib=NativeLibrary(SimpleNamespace(cuMemAlloc_v2=failed),Journal(path))
        with self.assertRaisesRegex(RuntimeError,'original native failure'):lib.cuMemAlloc_v2(None,128)
        rows=[json.loads(line) for line in path.read_text().splitlines()];r=memory.summarize(rows)
        self.assertIsNone(r['allocations'][0]['return_code']);self.assertEqual(r['allocations'][0]['exception'],'RuntimeError')
    def test_non_windows_host_gate_does_not_load_any_dll(self):
        # Module proxy leaves the real OS, pathlib and subprocess unchanged.
        with patch.object(memory,'os',SimpleNamespace(name='posix')),patch.object(C,'WinDLL',side_effect=AssertionError('No Windows DLL'),create=True),self.assertRaisesRegex(ValueError,'requires Windows'):memory.host_memory()
    def test_missing_current_job_is_unknown_not_zero(self):
        self.kernel.QueryInformationJobObject=lambda *args:0
        r=self.host();self.assertFalse(r['job']['available']);self.assertNotIn('job_peak_memory_bytes',r['job'])
    def test_missing_device_export_never_counts_a_query_or_claims_memory_available(self):
        r=memory.CudaMemorySampler(SimpleNamespace(),self.host)('cuLaunchKernel','before')
        self.assertEqual(r['driver_memory_query_calls'],0);self.assertIsNone(r['device']['free_bytes']);self.assertFalse(r['device']['available'])
    def test_missing_post_snapshot_is_not_complete_even_with_success_flags(self):
        sample=self.sampler()('cuLaunchKernel','before')
        rows=[dict(stage='cuda_memory_snapshot',state='observed',**sample),dict(stage='cuLaunchKernel',state='entered',grid=[1,1,1],block=[1,1,1],dynamic_shared_bytes=0),dict(stage='cuLaunchKernel',state='returned',return_code=0)]
        r=memory.summarize(rows);self.assertTrue(r['memory_observations_present']);self.assertFalse(r['memory_observation_complete']);self.assertFalse(r['calculation_verified'])
    def test_killed_final_append_is_preserved_as_incomplete_but_middle_corruption_fails(self):
        path=self.base/'killed.jsonl';raw=json.dumps(dict(stage='cuLaunchKernel',state='entered')).encode()+b'\n{"stage":'
        path.write_bytes(raw);r=memory.saved_summary(path,digest(raw),self.base/'killed-summary.json')
        self.assertTrue(r['truncated_final_event']);self.assertEqual(r['incomplete_native_events'],['cuLaunchKernel']);self.assertFalse(r['memory_observation_complete'])
        path.write_bytes(raw+b'\n{}\n')
        with self.assertRaises(ValueError):memory.saved_summary(path,digest(path.read_bytes()),self.base/'corrupt-summary.json')
    def test_observe_factory_adds_queries_only_with_explicit_flag_and_restores_loader(self):
        import os
        class OSProxy:
            name='nt'
            def __getattr__(self,key):return getattr(os,key)
        self.library.cuLaunchKernel=lambda *args:2
        def loader(name,**kwargs):
            return self.library if name=='nvcuda.dll' else self.loader(name,**kwargs)
        backend=SimpleNamespace(build=lambda:None)
        with patch.object(phase,'os',OSProxy()),patch.object(C,'WinDLL',loader,create=True):
            for flag,queries in (('0',0),('1',2)):
                before=self.query_calls
                with patch.dict(os.environ,NIKKE_CUDA_RESOURCE_OBSERVATION=flag,NIKKE_SLANG_GENERATION_CACHE=''),phase.observe(backend,Journal(self.base/('factory'+flag+'.jsonl'))):
                    library=C.WinDLL('nvcuda.dll');self.assertEqual(library.cuLaunchKernel(None,15,1,1,1,1,1,0,None,None,None),2)
                self.assertIs(C.WinDLL,loader);self.assertEqual(self.query_calls-before,queries)
    def test_invalid_observation_flag_fails_before_patching_backend(self):
        import os
        original=lambda:None;backend=SimpleNamespace(build=original)
        with patch.dict(os.environ,NIKKE_CUDA_RESOURCE_OBSERVATION='yes'),self.assertRaises(ValueError):
            with phase.observe(backend,Journal(self.base/'bad-flag.jsonl')):self.fail('No observer entered')
        self.assertIs(backend.build,original)


if __name__=='__main__':unittest.main()
