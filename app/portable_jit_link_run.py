"""In-process link provider inside the existing bounded CLI child and auditor."""
import ctypes as C
import hashlib,json,os,time,types
from pathlib import Path
import portable_jit_link as jit
import portable_partition_object as obj
from portable_phase_audit import NativeLibrary

PREFIX='module_jit_link'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def validate_context(view,record):
    pre=record['pre_gate'];pid=record['child_pid']
    if not record['pre_gate_verified'] or record['inspection_error'] or view.get('child_pid')!=pid or view.get('wrapper_pid')!=pid or view.get('child_ppid')!=record['wrapper_pid'] or view.get('parent_observation')!='os_process_snapshot' or view.get('job_members')!=[pid] or view.get('job_memory_limit_bytes')!=jit.LIMIT or not pre['child_creation_filetime_ticks'] or view.get('child_creation_filetime_ticks')!=pre['child_creation_filetime_ticks'] or view.get('observed_unix_ns',0)<pre['observed_unix_ns']:
        raise ValueError('JIT link child is not in its fixed current Job')
    return view


def inspect_context(capture):
    from windows_validation_observer import inspect_job
    from ctypes import wintypes as W
    dll=C.WinDLL('kernel32',use_last_error=True)
    dll.GetCurrentProcess.argtypes=[];dll.GetCurrentProcess.restype=W.HANDLE
    dll.CloseHandle.argtypes=[W.HANDLE];dll.CloseHandle.restype=W.BOOL
    process=types.SimpleNamespace(pid=os.getpid(),_handle=dll.GetCurrentProcess(),poll=lambda:None)
    return inspect_job(types.SimpleNamespace(dll=dll,handle=None),process)


def checked_context(capture):
    records=json.loads((Path(capture)/'job.json').read_bytes())['records']
    if len(records)!=1:raise ValueError('One fresh validation Job required')
    return validate_context(inspect_context(capture),records[0])


def driver_loaded():
    from ctypes import wintypes as W
    dll=C.WinDLL('kernel32',use_last_error=True)
    dll.GetModuleHandleW.argtypes=[W.LPCWSTR];dll.GetModuleHandleW.restype=W.HANDLE
    return bool(dll.GetModuleHandleW('nvcuda.dll'))


def driver_guard(journal,phase):
    loaded=driver_loaded();journal.emit(PREFIX+'_driver','verified' if not loaded else 'rejected',phase=phase,driver_module_loaded=loaded)
    if loaded:raise RuntimeError('Unexpected CUDA driver module in JIT link worker')


def run(capture,tool,raw,origin,*,journal):
    if obj.object_profile(origin)['stem']!='jit-linked':raise ValueError('JIT API provider origin required')
    capture=Path(capture).resolve();tool=Path(tool).resolve();started=time.perf_counter()
    input_path,partial,output=obj.object_paths(capture,origin)
    if any(path.exists() for path in (input_path,partial,output)):raise FileExistsError('Fresh JIT link outputs required')
    try:
        identity=jit.validate_library(tool)
        if obj.validate_input(origin,raw)!=origin['input']:raise ValueError('JIT object input changed')
        with input_path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        journal.emit(PREFIX+'_tool','verified',tool=identity);journal.emit(PREFIX+'_input','verified',input=origin['input'])
        journal.emit(PREFIX+'_job','verified',phase='before',inspection=checked_context(capture))
        driver_guard(journal,'before_load')
        library=journal.invoke(PREFIX+'_library_load',C.WinDLL,str(tool),event_facts=dict(path=str(tool),tool_sha256=identity['sha256']))
        driver_guard(journal,'after_load')
        artifact,diagnostic=journal.invoke(PREFIX+'_api',jit.link_cubin,NativeLibrary(library,journal),raw)
        driver_guard(journal,'after_link')
        journal.emit(PREFIX+'_job','verified',phase='after',inspection=checked_context(capture))
        if jit.validate_library(tool)!=identity or input_path.read_bytes()!=raw:raise ValueError('JIT DLL/input changed during execution')
        metadata=obj.validate_output(origin,artifact)
        if metadata!=diagnostic['artifact']:raise ValueError('JIT API artifact mismatch')
        with partial.open('xb') as stream:stream.write(artifact);stream.flush();os.fsync(stream.fileno())
        if output.exists():raise FileExistsError('JIT image already published')
        partial.rename(output)
        bound=obj.identity(identity,origin)
        receipt=dict(identity=bound,key=digest(json.dumps(bound,sort_keys=True,separators=(',',':')).encode()),artifact=metadata,
            api_diagnostic=diagnostic,elapsed_seconds=time.perf_counter()-started)
        journal.emit(PREFIX+'_receipt','verified',receipt=receipt);return receipt
    except BaseException as error:
        journal.emit(PREFIX+'_failure','raised',exception=type(error).__name__,diagnostic=error.diagnostic if isinstance(error,jit.JitLinkError) else None)
        raise


def api_order(events):
    names=[r['api'] for r in events]
    if any(type(r.get('return_code')) is not int or r['return_code']!=0 for r in events):raise ValueError('JIT native API did not return success')
    required=['Version','Create','AddData','Complete','GetErrorLogSize']
    index=len(required)
    if names[:index]!=[jit.symbol(n) for n in required]:raise ValueError('Wrong JIT API prefix')
    if index<len(names) and names[index]==jit.symbol('GetErrorLog'):index+=1
    if index>=len(names) or names[index]!=jit.symbol('GetInfoLogSize'):raise ValueError('Missing JIT info log')
    index+=1
    if index<len(names) and names[index]==jit.symbol('GetInfoLog'):index+=1
    if names[index:]!=[jit.symbol(n) for n in ('GetLinkedCubinSize','GetLinkedCubin','Destroy')]:raise ValueError('Wrong JIT artifact/cleanup API order')
    return names


def audit_rows(rows,capture,origin,tool,record):
    capture=Path(capture);proof=json.loads((capture/'jit-link.json').read_bytes());receipt=proof['receipt'];diagnostic=receipt['api_diagnostic']
    if proof['origin']!=origin or proof.get('calculation_verified') is not False or proof.get('link_verified') is not True or proof.get('kernel_calls')!=0:raise ValueError('Wrong JIT proof scope')
    if diagnostic.get('failure') is not None or diagnostic.get('cleanup_error') is not None or diagnostic.get('log_errors')!=[] or diagnostic.get('error_log')!='' or diagnostic.get('api_version')!=[12,4] or diagnostic.get('options')!=jit.OPTIONS or diagnostic.get('input')!=origin['input'] or any(diagnostic.get(k) is not False for k in ('source_origin_verified','containment_verified','calculation_verified')) or diagnostic.get('program_driver_api_calls')!=0:raise ValueError('Incomplete JIT API diagnostic')
    names=api_order(diagnostic['events']);api_rows=[]
    for name in names:api_rows.extend([(name,'entered'),(name,'returned')])
    expected=[(PREFIX+'_origin','verified'),('shared_'+PREFIX,'entered'),(PREFIX+'_tool','verified'),(PREFIX+'_input','verified'),(PREFIX+'_job','verified'),(PREFIX+'_driver','verified'),(PREFIX+'_library_load','entered'),(PREFIX+'_library_load','returned'),(PREFIX+'_driver','verified'),(PREFIX+'_api','entered'),*api_rows,(PREFIX+'_api','returned'),(PREFIX+'_driver','verified'),(PREFIX+'_job','verified'),(PREFIX+'_receipt','verified'),('shared_'+PREFIX,'returned')]
    if [(r['stage'],r['state']) for r in rows]!=expected:raise ValueError('Incomplete or forbidden JIT journal')
    if rows[0]['origin']!=origin or rows[2]['tool']!=tool or rows[3]['input']!=origin['input'] or rows[6]['path']!=str(Path(tool_path(capture)).resolve()) or rows[6]['tool_sha256']!=tool['sha256']:raise ValueError('JIT journal source/tool/input mismatch')
    for offset,event in enumerate(diagnostic['events']):
        if rows[11+2*offset].get('return_code')!=event['return_code']:raise ValueError('JIT native return receipt mismatch')
    driver_rows=[r for r in rows if r['stage']==PREFIX+'_driver']
    if [r['phase'] for r in driver_rows]!=['before_load','after_load','after_link'] or any(r['driver_module_loaded'] is not False for r in driver_rows):raise ValueError('JIT driver observation mismatch')
    jobs=[r for r in rows if r['stage']==PREFIX+'_job']
    if [r['phase'] for r in jobs]!=['before','after']:raise ValueError('JIT Job observation phases missing')
    for row in jobs:
        view=validate_context(row['inspection'],record)
        if not rows[1]['wall_time_ns']<=view['observed_unix_ns']<=row['wall_time_ns']:raise ValueError('JIT Job observation time mismatch')
    bound=obj.identity(tool,origin)
    if receipt['identity']!=bound or receipt['key']!=digest(json.dumps(bound,sort_keys=True,separators=(',',':')).encode()) or rows[-2]['receipt']!=receipt:raise ValueError('JIT receipt identity mismatch')
    input_path,_,output=obj.object_paths(capture,origin)
    if obj.validate_input(origin,input_path.read_bytes())!=origin['input'] or obj.validate_output(origin,output.read_bytes())!=receipt['artifact'] or receipt['artifact']!=diagnostic['artifact']:raise ValueError('JIT input/output artifact changed')
    return receipt


def tool_path(capture):return json.loads((Path(capture)/'object-request.json').read_bytes())['nvjitlink']
