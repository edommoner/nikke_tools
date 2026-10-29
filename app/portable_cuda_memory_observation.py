"""Read-only owned-process and current CUDA-context memory observations.

No allocation, launch, compilation or admission decision. Device free memory
is an OS estimate at sampling time, not a promise that an allocation will fit.
"""
import ctypes as C,os,time
from portable_job_limits import read_job_limits


class ProcessMemory(C.Structure):
    # Windows x64 PROCESS_MEMORY_COUNTERS_EX; DWORD is always 32 bits.
    _fields_=[('cb',C.c_uint32),('page_faults',C.c_uint32),
        *[(n,C.c_size_t) for n in ('peak_working_set','working_set','peak_paged_pool','paged_pool',
            'peak_nonpaged_pool','nonpaged_pool','pagefile','peak_pagefile','private_usage')]]


def host_memory(loader=None):
    """Only this process and its actual parent; no arbitrary PID or tree scan."""
    if loader is None:
        if os.name!='nt':raise ValueError('Owned host-memory observation requires Windows')
        loader=C.WinDLL
    if C.sizeof(C.c_void_p)!=8 or C.sizeof(ProcessMemory)!=80:raise ValueError('Windows x64 process memory ABI required')
    kernel=loader('kernel32.dll',use_last_error=True);psapi=loader('psapi.dll',use_last_error=True)
    kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=C.c_void_p
    kernel.OpenProcess.argtypes=[C.c_uint32,C.c_int,C.c_uint32];kernel.OpenProcess.restype=C.c_void_p
    kernel.CloseHandle.argtypes=[C.c_void_p];kernel.CloseHandle.restype=C.c_int
    psapi.GetProcessMemoryInfo.argtypes=[C.c_void_p,C.POINTER(ProcessMemory),C.c_uint32];psapi.GetProcessMemoryInfo.restype=C.c_int
    def process(handle,pid):
        value=ProcessMemory();value.cb=C.sizeof(value)
        if not psapi.GetProcessMemoryInfo(handle,C.byref(value),C.sizeof(value)):
            return dict(pid=pid,available=False,reason='GetProcessMemoryInfo failed')
        return dict(pid=pid,available=True,private_bytes=int(value.private_usage),
            working_set_bytes=int(value.working_set),peak_private_bytes=int(value.peak_pagefile),
            observed_unix_ns=time.time_ns())
    own=process(kernel.GetCurrentProcess(),os.getpid());parent_pid=os.getppid()
    handle=kernel.OpenProcess(0x1000,False,parent_pid) # QUERY_LIMITED_INFORMATION
    if handle:
        try:parent=process(handle,parent_pid)
        finally:closed=bool(kernel.CloseHandle(handle))
        parent['handle_closed']=closed
    else:parent=dict(pid=parent_pid,available=False,reason='OpenProcess parent failed',handle_closed=True)
    try:job=dict(available=True,**read_job_limits(kernel,None,include_flags=True),observed_unix_ns=time.time_ns())
    except (OSError,RuntimeError,AttributeError) as error:job=dict(available=False,reason=type(error).__name__)
    return dict(schema='owned-host-memory-v1',process=own,parent=parent,job=job,
        atomic=False,scope='Current private commit and separate historical peaks; not current total Job usage',
        gpu_calls=0,driver_calls=0,calculation_verified=False)


class CudaMemorySampler:
    """Query only an already-loaded driver's current context; never create one."""
    def __init__(self,library,host):
        self.host=host;self.query=None;self.query_error=None
        try:
            self.query=library.cuMemGetInfo_v2
            self.query.argtypes=[C.POINTER(C.c_size_t),C.POINTER(C.c_size_t)];self.query.restype=C.c_int
        except (AttributeError,OSError) as error:self.query_error=type(error).__name__
    def __call__(self,boundary,position,*,return_code=None):
        started=time.time_ns()
        try:host=self.host()
        except Exception as error:host=dict(available=False,reason=type(error).__name__)
        free=C.c_size_t();total=C.c_size_t();attempts=0
        device=dict(available=False,free_bytes=None,total_bytes=None,return_code=None)
        if self.query is not None:
            attempts=1
            try:
                code=int(self.query(C.byref(free),C.byref(total)))
                device['return_code']=code
                if code==0 and 0<=free.value<=total.value and total.value>0:
                    device.update(available=True,free_bytes=int(free.value),total_bytes=int(total.value))
                else:device['reason']='Query failed or returned invalid memory sizes'
            except Exception as error:device['reason']=type(error).__name__
        else:device['reason']=self.query_error
        device['observed_unix_ns']=time.time_ns()
        return dict(schema='cuda-memory-observation-v1',boundary=boundary,position=position,
            observed_call_return_code=return_code,started_unix_ns=started,finished_unix_ns=time.time_ns(),
            host=host,device=device,atomic=False,driver_memory_query_calls=attempts,kernel_calls_added=0,
            scope='Point-in-time estimate only; not allocation capacity, failure cause, or calculation proof')


def summarize(rows):
    """Saved event data only. Missing arguments/observations remain unknown."""
    allocations=[];launches=[];snapshots=[];pending={};expected_observations=[]
    for row in rows:
        stage=row.get('stage');state=row.get('state')
        if stage in ('cuMemAlloc_v2','cuLaunchKernel'):
            if state=='entered':
                if stage in pending:raise ValueError('Overlapping native resource events')
                if stage=='cuMemAlloc_v2':
                    size=row.get('requested_bytes')
                    if size is not None and (type(size) is not int or size<0):raise ValueError('Invalid recorded allocation size')
                    record=dict(requested_bytes=size,return_code=None);allocations.append(record)
                else:
                    grid=row.get('grid');block=row.get('block');shared=row.get('dynamic_shared_bytes')
                    for dims in (grid,block):
                        if dims is not None and (type(dims) is not list or len(dims)!=3 or any(type(v) is not int or v<1 for v in dims)):raise ValueError('Invalid recorded launch dimensions')
                    if shared is not None and (type(shared) is not int or shared<0):raise ValueError('Invalid recorded dynamic shared memory')
                    record=dict(grid=grid,block=block,dynamic_shared_bytes=shared,return_code=None);launches.append(record)
                pending[stage]=record
                expected_observations.extend(((stage,'before'),(stage,'after')))
            elif state=='returned':
                code=row.get('return_code')
                if stage not in pending or type(code) is not int:raise ValueError('Unpaired native resource return')
                pending.pop(stage)['return_code']=code
            elif state=='raised':
                if stage not in pending:raise ValueError('Unpaired raised resource event')
                pending.pop(stage)['exception']=row.get('exception')
        elif stage=='cuda_memory_snapshot':
            if (state!='observed' or row.get('schema')!='cuda-memory-observation-v1'
                or row.get('boundary') not in ('cuMemAlloc_v2','cuLaunchKernel') or row.get('position') not in ('before','after')
                or type(row.get('driver_memory_query_calls')) is not int or row['driver_memory_query_calls'] not in (0,1)
                or type(row.get('kernel_calls_added')) is not int or row['kernel_calls_added']!=0):
                raise ValueError('Invalid CUDA memory observation event')
            if (type(row.get('host')) is not dict or type(row.get('device')) is not dict
                or any(type(row.get(k)) is not int for k in ('started_unix_ns','finished_unix_ns'))
                or not 0<=row['started_unix_ns']<=row['finished_unix_ns']):raise ValueError('Invalid CUDA memory observation payload')
            snapshots.append({k:row[k] for k in ('boundary','position','host','device','started_unix_ns','finished_unix_ns','driver_memory_query_calls')})
    def available(row):
        h=row['host'];d=row['device']
        if type(h) is not dict or type(d) is not dict:raise ValueError('Memory observation dictionaries required')
        return (d.get('available') is True and type(d.get('free_bytes')) is int and type(d.get('total_bytes')) is int
            and 0<=d['free_bytes']<=d['total_bytes'] and d['total_bytes']>0
            and type(d.get('return_code')) is int and d['return_code']==0 and row['driver_memory_query_calls']==1
            and all(type(h.get(k)) is dict and h[k].get('available') is True for k in ('process','parent','job'))
            and all(type(h[k].get('private_bytes')) is int and h[k]['private_bytes']>=0 for k in ('process','parent'))
            and type(h['job'].get('job_memory_limit_bytes')) is int and h['job']['job_memory_limit_bytes']>0
            and type(h['job'].get('job_peak_memory_bytes')) is int and h['job']['job_peak_memory_bytes']>=0
            and h['parent'].get('handle_closed') is True)
    complete=bool(snapshots) and [(r['boundary'],r['position']) for r in snapshots]==expected_observations and all(available(r) for r in snapshots)
    return dict(schema='saved-cuda-resource-summary-v1',allocations=allocations,launches=launches,
        snapshots=snapshots,incomplete_native_events=sorted(pending),
        allocation_arguments_recorded=bool(allocations) and all(r['requested_bytes'] is not None for r in allocations),
        launch_arguments_recorded=bool(launches) and all(r['grid'] is not None and r['block'] is not None and r['dynamic_shared_bytes'] is not None for r in launches),
        memory_observations_present=bool(snapshots),memory_observation_complete=complete,failure_cause_verified=False,
        diagnostic_gpu_calls=0,diagnostic_driver_calls=0,calculation_verified=False,
        scope='Pinned saved events only; not source, containment, allocation capacity, or calculation certification')


def saved_summary(path,expected_sha256,out):
    import json
    from pathlib import Path
    from portable_admission_snapshot import hex_string,digest,file_sha
    from portable_staged_preflight import exclusive
    path=Path(path);out=Path(out)
    if not hex_string(expected_sha256,64) or path.is_symlink() or not path.is_file() or path.stat().st_size>16*1024**2:
        raise ValueError('Pinned bounded phase journal required')
    raw=path.read_bytes()
    if len(raw)>16*1024**2 or digest(raw)!=expected_sha256:raise ValueError('Resource journal SHA mismatch')
    rows=[];truncated=False;lines=raw.splitlines()
    for index,line in enumerate(lines):
        try:rows.append(json.loads(line))
        except (json.JSONDecodeError,UnicodeDecodeError):
            if index!=len(lines)-1 or raw.endswith(b'\n'):raise
            truncated=True
    if any(type(row) is not dict for row in rows):raise ValueError('Resource journal must contain event objects')
    result=summarize(rows);result.update(journal_sha256=expected_sha256,journal_bytes=len(raw),truncated_final_event=truncated)
    if truncated:result['memory_observation_complete']=False
    if file_sha(path)!=expected_sha256:raise ValueError('Resource journal changed during summary')
    exclusive(out,result)
    return result
