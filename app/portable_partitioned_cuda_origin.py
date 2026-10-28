"""Bounded, GPU-forbidden reread of the consumed CUDA launch failure.

This creates no GPU claim and cannot start a replacement execution. It reuses
the original owner's admission, Job timeline and snapshot comparators.
"""
import argparse,contextlib,ctypes,json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

MODE='partitioned-cuda-origin-audit-v1'
OWNER='66c50b923e5786c58989121324f206f880341db76bbb27992b81f27962adb58a'


@contextlib.contextmanager
def gpu_forbidden(cli):
    import portable_backend as backend
    def stop(*a,**k):raise RuntimeError('Compiler/driver execution forbidden in saved CUDA origin audit')
    with cli.forbid_gpu(),contextlib.ExitStack() as stack:
        for name in ('execute_cuda','execute_cuda_batches','inspect_cuda_module','_cuda_module','compile_cuda_source','compile_cuda_artifact'):
            if hasattr(backend,name):stack.enter_context(patch.object(backend,name,stop))
        def gate(loader):
            def load(name,*a,**k):
                base=str(name).replace('\\','/').rsplit('/',1)[-1].lower()
                if any(x in base for x in ('nvcuda','nvrtc','nvjitlink','slang')):return stop()
                return loader(name,*a,**k)
            return load
        for name in ('WinDLL','CDLL'):
            if hasattr(ctypes,name):stack.enter_context(patch.object(ctypes,name,gate(getattr(ctypes,name))))
        yield


def failure_trace(rows):
    if any(r.get('stage','').lower().startswith('nvrtc') or r.get('stage')=='slang_compiler' or r.get('state')=='raised' and re.fullmatch(r'cu[A-Z].*',r.get('stage','')) for r in rows):
        raise ValueError('Original failure includes a compiler or unknown native failure')
    native=[r for r in rows if re.fullmatch(r'cu[A-Z].*',r.get('stage',''))]
    expected=['cuInit','cuDeviceGet','cuDeviceComputeCapability','cuDeviceGetName','cuCtxCreate_v2','cuModuleLoadData',
              'cuModuleGetFunction','cuModuleGetGlobal_v2',*(['cuMemAlloc_v2']*3),'cuMemcpyHtoD_v2','cuMemsetD8_v2',
              'cuMemcpyHtoD_v2','cuLaunchKernel','cuCtxDestroy_v2']
    if len(native)!=2*len(expected):raise ValueError('Unknown original CUDA launch failure boundaries')
    for i,stage in enumerate(expected):
        a,b=native[2*i:2*i+2]
        if (a.get('stage')!=stage or b.get('stage')!=stage or a.get('state')!='entered' or b.get('state')!='returned'
            or type(b.get('return_code')) is not int or b['return_code']!=(2 if stage=='cuLaunchKernel' else 0)):
            raise ValueError('Original failure is not the preserved allocation-success/launch-code2/cleanup-success sequence')
    return native


def inspect_original(cli,root,outer):
    from portable_staged_preflight import admit
    from windows_validation_observer import compare_snapshots
    root=Path(root).resolve();outer=Path(outer).resolve();proof=outer/'proof';m=cli.verify_package(root)
    if m.get('package_id')!=OWNER:raise ValueError('Exact consumed CUDA owner required')
    saved=cli.load(proof/'staged-preflight.json');tx=Path(saved['transaction']);context=cli.load(tx/'transaction.json')
    claims=[root/'gpu-claimed-cuda.json',root/'packet-stage-claimed-staged-gpu-linked-cuda.json',tx/'gpu-execution-claimed.json',Path(context['recovery_parent']['ledger'])]
    before=[dict(path=str(p),bytes=p.stat().st_size,sha256=cli.sha(p.read_bytes())) for p in claims]
    raw=(proof/'phases.jsonl').read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
    native=failure_trace(rows)
    if any((proof/n).exists() for n in ('readback.bin','readback.bin.partial','evidence.json')):raise ValueError('Original failed launch has result/readback artifacts')
    summaries={}
    for name,folder in (('outer',outer),('inner',proof)):
        facts=cli.load(folder/'execution.json');job=cli.load(folder/'job.json')['records']
        if (facts.get('passed') is not False or facts.get('timed_out') is not False or facts.get('child_exit_code')!=1
            or facts.get('final_child_exit_code')!=1 or facts.get('below_normal_priority') is not True
            or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error')) or len(job)!=1):
            raise ValueError('Original launch failure is not terminal and bounded')
        observed=rows if name=='inner' else [json.loads(x) for x in (folder/'preparation.jsonl').read_bytes().splitlines()]
        observed=[r for r in observed if r.get('pid')==job[0]['child_pid']]
        contained,pid=cli.job_contained(folder,observed,memory_limit_bytes=2147483648)
        observation=cli.load(folder/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
        if not contained or observation['comparison']!=comparison or comparison['missing_existing_processes']:
            raise ValueError('Original Job cleanup or process preservation is unverified')
        summaries[name]=dict(containment_verified=True,child_pid=pid,job_post_members=job[0]['post_wait']['job_members'],
                             process_preserved=True,observation_comparison=comparison,execution_sha256=cli.sha((folder/'execution.json').read_bytes()))
    # Use its own unchanged admission; do not regenerate any native value or
    # remove/reassign claims. The same host and saved environment are required.
    with gpu_forbidden(cli):
        actual=admit(cli,m,tx,'cuda',proof)
        linked=cli.saved_linked_admission(m,cli.load(proof/'linked-artifact-request.json'))
        from portable_linked_artifact import valid_marker
        receipts=[r['receipt'] for r in rows if valid_marker(r)]
        if receipts!=[linked['receipt']]:raise ValueError('Original loaded CUBIN differs from its revalidated producer')
    if actual!=saved or actual.get('all_native_preflight_verified') is not True:raise ValueError('Original native admission changed')
    after=[dict(path=str(p),bytes=p.stat().st_size,sha256=cli.sha(p.read_bytes())) for p in claims]
    if before!=after or (proof/'phases.jsonl').read_bytes()!=raw or cli.verify_package(root)!=m:raise ValueError('Original failure, source or claims changed during reread')
    return dict(schema=MODE,original_package_id=m['package_id'],golden=m['golden'],native_admission_revalidated=True,
                input_count=actual['input_count'],native_cases=actual['native_cases'],native_admission_sha256=cli.sha((proof/'staged-preflight.json').read_bytes()),
                original_stage_passed=False,claims_modified=False,claims=before,original_failure_sha256=cli.sha(raw),original_failure_bytes=len(raw),
                linked_receipt=linked['receipt'],linked_artifact=linked['artifact'],native_events=native,terminal=summaries,gpu_calls=0,compiler_calls=0,native_calls=0,calculation_verified=False,
                execution_permitted=False,full_goal_complete=False)


def child(cli,capture):
    from portable_phase_audit import Journal
    deadline=time.monotonic()+60
    while not (capture/'start.json').exists():
        if time.monotonic()>deadline:raise RuntimeError('CPU audit containment gate was not released')
        time.sleep(.02)
    j=Journal(capture/'phases.jsonl');m=j.invoke('cuda_origin_verify_packet',cli.verify_package,cli.ROOT)
    request=cli.load(capture/'run.json')
    if request.get('mode')!=MODE or request.get('package_id')!=m['package_id']:raise ValueError('Unknown CPU origin request')
    if request.get('smoke') is True:
        if os.name=='nt':j.invoke('cuda_origin_native_job_smoke',cli.native_smoke_child,capture)
        cli.write(capture/'smoke.json',dict(pid=os.getpid(),ppid=os.getppid(),gpu_calls=0,compiler_calls=0))
        return
    original=cli.load(Path(request['source_package'])/'gpu-package.json')
    if original.get('package_id')!=OWNER or cli.package_id(original)!=OWNER or original.get('golden')!=m['golden']:
        raise ValueError('Exact original owner and complete baseline required before loading its CLI')
    cli.check_records(Path(request['source_package']),original['files'])
    script='''import importlib.util,pathlib,json,sys
from types import SimpleNamespace
root=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location('cuda_origin_original_owner',root/'scripts/nikke_gpu.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
s=importlib.util.spec_from_file_location('cuda_origin_readonly_controller',sys.argv[3]);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
with a.gpu_forbidden(SimpleNamespace(**vars(c))):r=a.inspect_original(SimpleNamespace(**vars(c)),root,pathlib.Path(sys.argv[2]))
print(json.dumps(r))
'''
    try:
        with gpu_forbidden(cli):
            result=j.invoke('cuda_origin_readonly_admission',subprocess.run,[sys.executable,'-B','-c',script,request['source_package'],request['source_capture'],str(Path(__file__).resolve())],
                            cwd=request['source_package'],capture_output=True,text=True,timeout=150,check=True)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
        for key in ('stdout','stderr'):
            value=getattr(error,key,None) or ''
            (capture/('origin.'+key+'.log')).write_text(value.decode(errors='replace') if isinstance(value,bytes) else value)
        raise
    (capture/'origin.stdout.log').write_text(result.stdout);(capture/'origin.stderr.log').write_text(result.stderr)
    report=json.loads(result.stdout)
    if report.get('golden')!=m['golden'] or report.get('native_admission_revalidated') is not True or report.get('execution_permitted') is not False:
        raise ValueError('CPU origin report differs from complete frozen baseline')
    cli.write(capture/'origin.json',report)


def run(cli,source_package,source_capture,capture,workspace,slang_root,generation_cache,timeout=180):
    from portable_staged_preflight import outside
    if os.name!='nt':raise ValueError('Consumed CUDA admission is host-bound to Windows')
    if type(timeout) is not int or not 1<=timeout<=180:raise ValueError('CPU origin audit budget must be 1..180')
    m=cli.verify_package(cli.ROOT)
    if m.get('partitioned_diagnostic',{}).get('cuda_execution_admitted') is not False:raise ValueError('GPU-disabled immutable diagnostic required')
    source_package=Path(source_package).resolve();source_capture=Path(source_capture).resolve()
    capture=outside(capture,[cli.ROOT,source_package,source_capture]);capture.mkdir(parents=True,exist_ok=False)
    os.environ.update(NIKKE_VALIDATION_JOB_MEMORY_MB='2048',NIKKE_SLANG_ROOT=str(Path(slang_root).resolve()),NIKKE_SLANG_GENERATION_CACHE=str(Path(generation_cache).resolve()),NIKKE_SLANG_GENERATION_REQUIRED='1')
    cli.write(capture/'run.json',dict(mode=MODE,package_id=m['package_id'],source_package=str(source_package),source_capture=str(source_capture)))
    try:
        facts=cli.run_job(capture,'cuda',timeout,original_workspace=str(Path(workspace).resolve()))
        report=cli.load(capture/'origin.json') if (capture/'origin.json').is_file() else None
        rows=[json.loads(x) for x in (capture/'phases.jsonl').read_bytes().splitlines()] if (capture/'phases.jsonl').exists() else []
        contained,_=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
        preservation=cli.environment_preserved(capture,facts,'cuda')
        from windows_validation_observer import compare_snapshots
        observation=cli.load(capture/'observation.json')
        comparison=compare_snapshots(observation['before'],observation['after'])
        if observation.get('comparison')!=comparison:raise ValueError('Current CPU audit observation mismatch')
        if cli.verify_package(cli.ROOT)!=m:raise ValueError('CPU origin controller changed during audit')
        result=dict(mode=MODE,package_id=m['package_id'],passed=bool(facts.get('passed') and report and contained),
                    containment_verified=contained,native_admission_revalidated=bool(report and report.get('native_admission_revalidated')),
                    process_preserved=comparison['all_monitored_processes_preserved'],preservation_verified=preservation,
                    execution_permitted=False,calculation_verified=False,gpu_calls=0,compiler_calls=0,native_calls=0,full_goal_complete=False)
        cli.write(capture/'result.json',result);return result
    finally:cli.collect(capture,capture/'artifacts.json')


def smoke(cli,capture,workspace=None,timeout=30):
    from portable_staged_preflight import outside
    if type(timeout) is not int or not 1<=timeout<=60:raise ValueError('CPU smoke budget must be 1..60')
    m=cli.verify_package(cli.ROOT)
    if m.get('partitioned_diagnostic',{}).get('cuda_execution_admitted') is not False:raise ValueError('GPU-disabled immutable diagnostic required')
    capture=outside(capture,[cli.ROOT]);capture.mkdir(parents=True,exist_ok=False)
    os.environ['NIKKE_VALIDATION_JOB_MEMORY_MB']='2048'
    cli.write(capture/'run.json',dict(mode=MODE,package_id=m['package_id'],smoke=True))
    try:
        facts=cli.run_job(capture,'cuda',timeout,original_workspace=str(Path(workspace).resolve()) if workspace else None)
        receipt=cli.load(capture/'smoke.json') if (capture/'smoke.json').is_file() else None
        contained=None;native=None
        if os.name=='nt':
            rows=[json.loads(x) for x in (capture/'phases.jsonl').read_bytes().splitlines()] if (capture/'phases.jsonl').exists() else []
            contained,pid=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
            if contained and receipt and receipt.get('pid')==pid:native=cli.audit_native_smoke(capture,pid)
        passed=bool(facts.get('passed') and receipt and receipt.get('gpu_calls')==0 and receipt.get('compiler_calls')==0
                    and (os.name!='nt' or contained and native))
        result=dict(mode='partitioned-cuda-origin-smoke-v1',package_id=m['package_id'],passed=passed,containment_verified=contained,
                    gpu_calls=0,compiler_calls=0,native_battle_calls=0,calculation_verified=False,execution_permitted=False)
        cli.write(capture/'result.json',result);return result
    finally:cli.collect(capture,capture/'artifacts.json')
