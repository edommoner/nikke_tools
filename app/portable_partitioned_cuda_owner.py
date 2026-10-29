"""Private single-use resident CUDA execution after a retained launch failure."""
import argparse,json,os,sys,time,uuid
from pathlib import Path
from portable_partitioned_cli import CURRENT

MODE='partitioned-cuda-owner-v1'
CLAIM='partitioned-cuda-execution-claimed.json'
PREPARED='partitioned-cuda-preflight-claimed.json'
CURRENT_TESTS=('test_portable_partitioned_current.py','test_portable_partitioned_cuda_owner.py',
    'test_portable_partitioned_cuda_receipt.py','test_portable_partitioned_cuda_trace.py',
    'test_portable_partitioned_cuda_observer.py','test_portable_partitioned_transport.py','test_portable_partitioned_addresses.py')


def manifest(cli):
    m=cli.verify_package(cli.ROOT)
    meta=m.get('partitioned_cuda_execution',{})
    if meta.get('schema') not in (MODE,CURRENT) or meta.get('batch_size')!=16 or meta.get('maximum_gpu_seconds')!=60 or m.get('purpose')!='sealed':
        raise ValueError('Explicit immutable CUDA partitioned owner required')
    ref=cli.load(cli.ROOT/'research/partitioned-cuda-native-reference.json')
    if (cli.sha((cli.ROOT/'research/partitioned-cuda-native-reference.json').read_bytes())!=meta['native_reference_sha256']
        or ref.get('calculation_verified') is not True or ref['comparison']['entries']!=m['golden']['entries']
        or ref['comparison']['logical_output_sha256']!=m['golden']['output_sha256']):raise ValueError('Complete independent Metal/native baseline required')
    if meta['schema']==CURRENT:
        from portable_partitioned_cli import current_reference,PHYSICAL_REFERENCE_SHA
        from portable_partitioned_addresses import PROFILE,check_source
        config=cli.SUITES[m['suite']]
        if (meta.get('native_reference_sha256')!=PHYSICAL_REFERENCE_SHA or meta.get('prior_physical_reference_reused') is not True or m.get('partitioned_diagnostic',{}).get('wire_address_profile')!=PROFILE
            or ref['comparison'].get('input_sha256')!=m['golden']['input_sha256']):raise ValueError('Current physical wire identity changed')
        check_source(cli.ROOT,config['source'],config['output_words'])
        pin=current_reference(cli,cli.ROOT,cli.SUITES[m['suite']],m['golden'],(cli.ROOT/'research/partitioned-current-metal-reference.json').read_bytes())
        if meta.get('current_source_reference')!=pin or meta.get('prior_physical_reference_reused') is not True:
            raise ValueError('Current source Metal seal changed')
    return m,ref


def settings(request):
    os.environ.update(NIKKE_VALIDATION_JOB_MEMORY_MB='2048',NIKKE_SLANG_ROOT=request['slang_root'],
        NIKKE_SLANG_GENERATION_CACHE=request['generation_cache'],NIKKE_SLANG_GENERATION_REQUIRED='1',
        NIKKE_CUDA_CACHE_REQUIRED='1',NIKKE_CUDA_ARTIFACT='cubin',CUDA_CACHE_DISABLE='1')


def storage_preflight(cli,m,packed,path):
    from portable_partitioned_transport import plan
    from portable_capture_storage import space_status
    config=cli.SUITES[m['suite']]
    layout=plan(packed,config.get('input_words',115680),config['output_words'],16)
    if layout['input_count']!=len(m['golden']['entries']) or layout['input_sha256']!=m['golden']['input_sha256']:
        raise ValueError('Storage plan requires the complete frozen input')
    status=space_status(path,layout['staging_bytes']+len(packed)+64*1024*1024)
    if not status['passed']:raise RuntimeError('Insufficient retained-readback storage before CUDA claim')
    return status


def prepared(cli,m,folder,gpu_capture=None):
    from portable_staged_preflight import host
    from portable_partitioned_cuda_receipt import check,canonical
    folder=Path(folder).resolve();cli.check_records(folder,cli.load(folder/'artifacts.json')['files'])
    context=cli.load(folder/'prepared.json');state=cli.load(folder/'pinned-cubin.json')
    from portable_partitioned_cuda_receipt import CURRENT as CURRENT_STATE
    if (state.get('schema')==CURRENT_STATE)!=(m['partitioned_cuda_execution']['schema']==CURRENT):
        raise ValueError('Prepared CUBIN admission belongs to another source-owner mode')
    if (context.get('package_id')!=m['package_id'] or context.get('host')!=host(cli)
        or context.get('prepared')!=str(folder) or context.get('state_sha256')!=canonical(cli,state)
        or cli.load(cli.ROOT/PREPARED)!=context
        or gpu_capture is not None and context.get('gpu_capture')!=str(Path(gpu_capture).resolve())):raise ValueError('Prepared CUDA ownership/input host changed')
    facts=cli.load(folder/'execution.json');result=cli.load(folder/'result.json')
    rows=[json.loads(x) for x in (folder/'phases.jsonl').read_bytes().splitlines()]
    contained,_=cli.job_contained(folder,rows,memory_limit_bytes=2147483648)
    if facts.get('passed') is not True or result.get('prepared') is not True or not contained:raise ValueError('Bounded CPU preflight is incomplete')
    check(cli,m,state);return context,state


def ledger(cli,state):
    from portable_partitioned_cuda_receipt import canonical
    from portable_partitioned_cuda_receipt import CURRENT as CURRENT_STATE
    if state.get('schema')==CURRENT_STATE:
        return Path(state['linked_root']).parent/'.partitioned-current-cuda-claims'/(canonical(cli,dict(cubin=state['linked_receipt']['key'],golden=state['golden_sha256']))+'.json')
    return Path(state['old_capture']).parent/'.partitioned-cuda-claims'/(canonical(cli,dict(failure=state['old_failure_sha256'],claims=state['claims']))+'.json')


def child(cli,capture):
    from portable_phase_audit import Journal,observe
    from portable_staged_preflight import exclusive,host,static_input
    from portable_partitioned_cuda_origin import gpu_forbidden
    from portable_partitioned_cuda_receipt import prepare as pin,prepare_current,canonical,provider
    deadline=time.monotonic()+60
    while not (capture/'start.json').exists():
        if time.monotonic()>deadline:raise RuntimeError('CUDA owner containment gate not released')
        time.sleep(.02)
    journal=Journal(capture/'phases.jsonl');m,ref=journal.invoke('partitioned_cuda_verify_owner',manifest,cli)
    request=cli.load(capture/'run.json')
    if request.get('mode')!=m['partitioned_cuda_execution']['schema'] or request.get('package_id')!=m['package_id']:raise ValueError('Unknown CUDA owner stage')
    if request['stage']=='smoke':
        if os.name=='nt':journal.invoke('partitioned_cuda_native_job_smoke',cli.native_smoke_child,capture)
        facts=dict(pid=os.getpid(),gpu_calls=0)
        if request['mode']==CURRENT:
            from portable_cpu_tests import run_groups,complete
            with gpu_forbidden(cli):rows=run_groups(cli.ROOT,capture,CURRENT_TESTS,cli.write)
            if not complete(rows,CURRENT_TESTS):raise ValueError('Current source CPU control checks incomplete')
            facts.update(cpu_groups=len(rows),cpu_tests=sum(r['tests'] for r in rows))
        exclusive(capture/'smoke.json',facts);return
    settings(request['settings'])
    if request['stage']=='prepare':
        current=request['mode']==CURRENT
        if not current and cli.sha((Path(request['auditor_capture'])/'origin.json').read_bytes())!=m['partitioned_cuda_execution']['origin_audit_sha256']:
            raise ValueError('The fixed source-host CPU audit changed')
        _,generation=journal.invoke('partitioned_cuda_generation',cli.required_generation_snapshot,m)
        exclusive(capture/'generation.json',generation)
        source=cli.ROOT/'research/portable-build'/ (Path(cli.SUITES[m['suite']]['source']).stem+'.cu')
        with gpu_forbidden(cli):
            _,entries,data,input_receipt=journal.invoke('partitioned_cuda_static_input',static_input,cli,m)
            if current:exclusive(capture/'storage.json',storage_preflight(cli,m,data,capture))
            if current:
                state=journal.invoke('partitioned_cuda_pin_admission',prepare_current,cli,m,request['linked_root'],request['linked_capture'],generated_cuda_source=source)
            else:
                state=journal.invoke('partitioned_cuda_pin_admission',pin,cli,m,request['auditor_root'],request['auditor_capture'],generated_cuda_source=source)
            cli.publish_transport_input(m,capture,data,input_receipt['input_words'])
        exclusive(capture/'pinned-cubin.json',state)
        context=dict(package_id=m['package_id'],host=host(cli),prepared=str(capture),gpu_capture=request['gpu_capture'],
                     nonce=uuid.uuid4().hex,state_sha256=canonical(cli,state),input=input_receipt,settings=request['settings'])
        exclusive(cli.ROOT/PREPARED,context);exclusive(capture/'prepared.json',context);return
    if request['stage']!='gpu':raise ValueError('Unknown CUDA stage')
    context,state=journal.invoke('partitioned_cuda_prepared_input',prepared,cli,m,request['prepared'],capture)
    if request['settings']!=context['settings']:raise ValueError('CUDA generation settings changed')
    claim=dict(package_id=m['package_id'],prepared=str(Path(request['prepared']).resolve()),capture=str(capture),nonce=context['nonce'])
    if cli.load(cli.ROOT/CLAIM)!=claim or cli.load(ledger(cli,state))!=claim:raise ValueError('CUDA single-use claim changed')
    packed=(Path(request['prepared'])/'input.bin').read_bytes()
    if cli.transport_input_receipt(m,packed,context['input']['input_words'])!=context['input']:raise ValueError('Prepared complete CUDA input changed')
    import portable_backend as backend
    from portable_partitioned_transport import execute
    from portable_partitioned_addresses import PROFILE
    with observe(backend,journal),provider(cli,m,state,capture,journal):
        _,evidence=journal.invoke('partitioned_cuda_shared_execute',execute,cli.SUITES[m['suite']]['source'],'portableEvents',packed,
            context['input']['input_words'],cli.SUITES[m['suite']]['output_words'],'cuda',readback_path=capture/'readback.bin',
            expected_input_sha256=m['golden']['input_sha256'],expected_output_sha256=m['golden']['output_sha256'],
            expected_source_sha256=m['golden']['source_sha256'],expected_generated_normalized=m['golden']['generated_normalized'],
            batch_size=16,address_profile=PROFILE,cuda_argument_journal=journal)
    if evidence['output_sha256']!=ref['comparison']['raw_output_sha256']:raise ValueError('Full CUDA physical wire differs from saved partitioned Metal')
    cli.copy_generated(capture,m['suite']);exclusive(capture/'evidence.json',evidence)


def run(cli,stage,capture,workspace,*,auditor_root=None,auditor_capture=None,linked_root=None,linked_capture=None,gpu_capture=None,prepare_capture=None,slang_root=None,generation_cache=None,timeout=None):
    from portable_staged_preflight import outside,exclusive
    from portable_partitioned_cuda_trace import verify
    from portable_partitioned_cuda_receipt import check
    if stage not in ('smoke','prepare','gpu'):raise ValueError('Explicit CUDA stage required')
    bound=180 if stage=='prepare' else 60;timeout=bound if timeout is None else timeout
    if type(timeout) is not int or not 1<=timeout<=bound:raise ValueError('CUDA owner budget exceeds its fixed stage limit')
    if os.name!='nt' and stage!='smoke':raise ValueError('CUDA execution/admission requires the original Windows host')
    m,ref=manifest(cli);mode=m['partitioned_cuda_execution']['schema'];current=mode==CURRENT
    if current and (auditor_root is not None or auditor_capture is not None) or not current and (linked_root is not None or linked_capture is not None):raise ValueError('Source owner requires its own admission family')
    capture=outside(capture,[cli.ROOT,*[p for p in (auditor_root,auditor_capture,linked_root,linked_capture,prepare_capture) if p is not None]])
    storage=None
    if stage=='prepare':
        if (cli.ROOT/PREPARED).exists() or (cli.ROOT/CLAIM).exists():raise FileExistsError('CUDA owner already prepared or consumed')
        first,second=(linked_root,linked_capture) if current else (auditor_root,auditor_capture)
        if any(p is None for p in (first,second,gpu_capture,slang_root,generation_cache)):raise ValueError('Complete source admission and generation paths required')
        if current and any(not Path(p).is_absolute() for p in (first,second,gpu_capture,slang_root,generation_cache)):
            raise ValueError('Absolute current-source admission paths required')
        request=dict(settings=dict(slang_root=str(Path(slang_root).resolve()),generation_cache=str(Path(generation_cache).resolve())),
                     gpu_capture=str(outside(gpu_capture,[cli.ROOT,capture,Path(first),Path(second)])))
        request.update(dict(linked_root=str(Path(first).resolve()),linked_capture=str(Path(second).resolve())) if current else dict(auditor_root=str(Path(first).resolve()),auditor_capture=str(Path(second).resolve())))
    elif stage=='gpu':
        context,state=prepared(cli,m,prepare_capture,capture);check(cli,m,state)
        if current:storage=storage_preflight(cli,m,(Path(prepare_capture)/'input.bin').read_bytes(),capture)
        claim=dict(package_id=m['package_id'],prepared=str(Path(prepare_capture).resolve()),capture=str(capture),nonce=context['nonce'])
        origins=[state['linked_root'],state['source_capture']] if current else [state['old_capture'],state['auditor_root'],state['source_capture']]
        target=outside(ledger(cli,state),[cli.ROOT,capture,Path(prepare_capture),*[Path(p) for p in origins]])
        if target.exists() or (cli.ROOT/CLAIM).exists() or capture.exists():raise FileExistsError('Original failed launch already assigned a new execution owner')
        target.parent.mkdir(parents=True,exist_ok=True);exclusive(target,claim);exclusive(cli.ROOT/CLAIM,claim)
        request=dict(prepared=str(Path(prepare_capture).resolve()),settings=context['settings'])
    else:request={}
    capture.mkdir(parents=True,exist_ok=False)
    if storage is not None:exclusive(capture/'storage.json',storage)
    exclusive(capture/'run.json',dict(mode=mode,package_id=m['package_id'],stage=stage,**request))
    if 'settings' in request:settings(request['settings'])
    os.environ['NIKKE_VALIDATION_JOB_MEMORY_MB']='2048'
    try:
        facts=cli.run_job(capture,'cuda',timeout,original_workspace=str(Path(workspace).resolve()) if workspace else None)
        rows=[json.loads(x) for x in (capture/'phases.jsonl').read_bytes().splitlines()] if (capture/'phases.jsonl').exists() else []
        contained,pid=cli.job_contained(capture,rows,memory_limit_bytes=2147483648) if os.name=='nt' else (None,None)
        good=bool(facts.get('passed') and (os.name!='nt' or contained));evidence=None
        if stage=='gpu':
            evidence=cli.load(capture/'evidence.json') if (capture/'evidence.json').is_file() else None
            good=bool(good and evidence and verify(rows,evidence['plan'],[r['transport'] for r in evidence['dispatches']],pid=pid,require_arguments=True)
                      and evidence['output_sha256']==ref['comparison']['raw_output_sha256'] and evidence['logical_wire_equivalence_verified'])
        elif stage=='smoke':
            smoke=cli.load(capture/'smoke.json') if (capture/'smoke.json').is_file() else None
            good=bool(good and smoke and smoke.get('gpu_calls')==0)
            if good and os.name=='nt':good=bool(smoke['pid']==pid and cli.audit_native_smoke(capture,pid))
            if good and current:
                from portable_cpu_tests import complete
                checks=cli.load(capture/'cpu-tests.json')
                good=bool(complete(checks,CURRENT_TESTS) and smoke.get('cpu_groups')==len(checks) and smoke.get('cpu_tests')==sum(r['tests'] for r in checks))
        else:good=bool(good and (capture/'prepared.json').is_file())
        result=dict(mode=mode,stage=stage,package_id=m['package_id'],passed=good,prepared=bool(good and stage=='prepare'),
            containment_verified=contained,preservation_verified=cli.environment_preserved(capture,facts,'cuda'),
            gpu_execution_verified=bool(good and stage=='gpu'),shared_metal_wire_equivalence_verified=bool(good and stage=='gpu'),
            calculation_verified=False,full_goal_complete=False,public_gpu_admitted=False)
        if current:result.update(current_source_metal_seal_verified=True,prior_physical_reference_reused=True,pending_independent_native_audit=True,
            stage_protocol_verified=good,overall_stage_passed=bool(good and result['preservation_verified'] is True))
        exclusive(capture/'result.json',result);return result
    finally:cli.collect(capture,capture/'artifacts.json')
