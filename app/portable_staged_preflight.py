"""One immutable run's fresh CPU gates, bounded independently of GPU time.

Receipts contain fingerprints only, never native values or GPU state. Normal
run preflight is unchanged. The GPU stage still awaits an independent audit.
"""
from portable_product_programs import configuration as product_configuration
import json,os,platform,sys,uuid
from pathlib import Path
from portable_comparison_groups import partition

SCHEMA='staged-native-preflight-v1'
PROTOCOL='staged-prepared-v1'


def exclusive(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())


def host(cli):
    return dict(platform=sys.platform,machine=platform.machine(),python_version=sys.version,
        python_sha256=cli.sha(Path(getattr(sys,'_base_executable',sys.executable)).resolve().read_bytes()))


def outside(path,roots):
    path=Path(path).resolve()
    if any(path==p or p in path.parents or path in p.parents for p in map(lambda p:Path(p).resolve(),roots)):
        raise ValueError('Staged output must be outside immutable/original evidence')
    return path


def static_input(cli,m):
    with cli.forbid_gpu():
        adapter=cli.open_suite(m);entries,data=cli.prepare_entries(adapter,m)
    receipt=cli.transport_input_receipt(m,data,adapter.suite.INPUT)
    if [n for n,_,_ in entries]!=[r['name'] for r in m['golden']['entries']]:
        raise ValueError('Staged case identities differ from sealed input')
    return adapter,entries,data,receipt


def context(cli,transaction,backend=None,gpu_capture=None):
    transaction=Path(transaction).resolve();m=cli.verify_package(cli.ROOT)
    c=cli.load(transaction/'transaction.json')
    if (c.get('schema')!=SCHEMA or c.get('package_id')!=m['package_id']
        or c.get('manifest_sha256')!=cli.sha((cli.ROOT/'gpu-package.json').read_bytes())
        or c.get('host')!=host(cli) or c.get('backend') not in ('metal','cuda') or cli.is_development(m) or cli.compiler_only(m)
        or c.get('transaction')!=str(transaction) or c.get('package_root')!=str(cli.ROOT.resolve())
        or backend is not None and c.get('backend')!=backend
        or gpu_capture is not None and c.get('gpu_capture')!=str(Path(gpu_capture).resolve())):
        raise ValueError('Staged transaction identity/source/host mismatch')
    if 'resume_parent' in c:
        from portable_staged_continuation import tail_groups
        if 'reject_group_size' in c and type(c['reject_group_size']) is not int:raise ValueError('Invalid rejected-input group size')
        expected_groups=tail_groups(len(m['golden']['entries']),c['resume_parent']['completed_inputs'],c['group_size'],
            native_indices=c.get('native_indices'),reject_group_size=c.get('reject_group_size'))
    else:
        if 'reject_group_size' in c:raise ValueError('Rejected-input grouping requires a continuation')
        expected_groups=partition(len(m['golden']['entries']),c['group_size'])
    if json.dumps(c['case_groups'])!=json.dumps(expected_groups):
        raise ValueError('Staged native plan changed')
    indices=c.get('native_indices')
    if (not isinstance(indices,list) or any(type(i) is not int or not 0<=i<len(m['golden']['entries']) for i in indices)
        or indices!=sorted(set(indices)) or len(indices)!=product_configuration(cli.SUITES,m)['native']):
        raise ValueError('Staged native membership changed')
    from portable_staged_tests import validate_plan
    validate_plan(cli,m,c)
    claim=cli.load(cli.ROOT/('gpu-claimed-'+c['backend']+'.json'))
    expected=dict(package_id=m['package_id'],capture=c['gpu_capture'],transaction=str(transaction),transaction_nonce=c['nonce'])
    if claim!=expected:raise ValueError('Staged GPU ownership claim mismatch')
    return m,c


def terminal_cpu_stage(cli,proof,m,stage):
    """Reuse the ordinary Job timeline and process observer on Windows."""
    if os.name!='nt':return dict(containment_verified=None,preservation_verified=None)
    outer=Path(proof).parent;plan=cli.load(outer/'recipe.json');facts=cli.load(outer/'execution.json')
    packet=cli.module(cli.ROOT/'scripts/run-gpu-packet.py')
    expected=packet.recipe(m['package_id'],stage,'cuda',outer,plan['original_workspace'],plan['timeout_seconds'],plan['object_request'])
    if plan!=expected:raise ValueError('Staged CPU recipe changed')
    if (plan.get('package_id')!=m['package_id'] or plan.get('stage')!=stage or plan.get('backend')!='cuda'
        or Path(plan['proof_capture']).resolve()!=Path(proof).resolve()
        or type(plan.get('timeout_seconds')) is not int or not 1<=plan['timeout_seconds']<=180
        or plan.get('memory_limit_mb')!=2048 or facts.get('passed') is not True
        or facts.get('timed_out') is not False or facts.get('child_exit_code')!=0
        or facts.get('final_child_exit_code')!=0 or facts.get('below_normal_priority') is not True
        or type(facts.get('timeout_seconds')) not in (int,float) or not 0<facts['timeout_seconds']<=plan['timeout_seconds']
        or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error'))):
        raise ValueError('Staged CPU gate is not a successful bounded stage')
    rows=[json.loads(line) for line in (proof/'phases.jsonl').read_text().splitlines()]
    contained,pid=cli.job_contained(outer,rows,memory_limit_bytes=2147483648)
    from windows_validation_observer import compare_snapshots
    observation=cli.load(outer/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
    if not contained or observation['comparison']!=comparison or comparison['missing_existing_processes']:
        raise ValueError('Staged CPU Job/observation gate not verified')
    return dict(containment_verified=True,child_pid=pid,preservation_verified=cli.environment_preserved(outer,facts),
        outer_files=cli.file_records(outer,['recipe.json','execution.json','job.json','observation.json']))


def begin(cli,capture,backend,gpu_capture,group_size,*,test_group_size=None,split_test_pattern=None,test_case_group_size=None):
    from portable_phase_audit import Journal
    if backend not in ('metal','cuda'):raise ValueError('Explicit staged backend required')
    partition(1,group_size)
    m=cli.verify_package(cli.ROOT)
    if cli.is_development(m) or cli.compiler_only(m):raise ValueError('Staged preflight requires a sealed battle')
    if test_group_size is not None:partition(len(product_configuration(cli.SUITES,m)['tests']),test_group_size)
    split=split_test_pattern is not None or test_case_group_size is not None
    if split:
        from portable_staged_tests import case_plan
        with cli.forbid_gpu():test_groups,test_cases=case_plan(cli,m,test_group_size,split_test_pattern,test_case_group_size)
    capture=outside(capture,[cli.ROOT]);gpu_capture=outside(gpu_capture,[cli.ROOT,capture])
    if gpu_capture.exists():raise FileExistsError(gpu_capture)
    capture.mkdir(parents=True,exist_ok=False);nonce=uuid.uuid4().hex
    with cli.forbid_gpu():cli.capture_storage_preflight(m,capture)
    exclusive(cli.ROOT/('gpu-claimed-'+backend+'.json'),dict(package_id=m['package_id'],capture=str(gpu_capture),transaction=str(capture),transaction_nonce=nonce))
    j=Journal(capture/'phases.jsonl')
    try:
        with cli.forbid_gpu():
            if test_group_size is None:j.invoke('staged_cpu_tests',cli.cpu_test_groups,m,capture)
            adapter,entries,data,receipt=j.invoke('staged_static_input',static_input,cli,m)
        native_indices=[i for i,(_,_,d) in enumerate(entries) if d is not None]
        if len(native_indices)!=product_configuration(cli.SUITES,m)['native']:raise ValueError('Staged native count differs from registered suite')
        cli.publish_transport_input(m,capture,data,adapter.suite.INPUT)
        c=dict(schema=SCHEMA,package_id=m['package_id'],manifest_sha256=cli.sha((cli.ROOT/'gpu-package.json').read_bytes()),
            package_root=str(cli.ROOT.resolve()),transaction=str(capture),nonce=nonce,backend=backend,gpu_capture=str(gpu_capture),
            host=host(cli),group_size=group_size,case_groups=partition(len(entries),group_size),native_indices=native_indices,input=receipt)
        if test_group_size is not None:
            from portable_staged_tests import plan
            c.update(test_group_size=test_group_size,test_groups=test_groups if split else plan(cli,m,test_group_size))
        if split:c.update(split_test_pattern=split_test_pattern,test_case_group_size=test_case_group_size,test_case_groups=test_cases)
        exclusive(capture/'transaction.json',c)
        if cli.verify_package(cli.ROOT)!=m:raise ValueError('Staged package changed during begin')
        j.emit('staged_begin_complete','returned')
        result=dict(mode='staged-preflight-begin-only' if test_group_size is None else 'staged-preflight-plan-only',package_id=m['package_id'],transaction_nonce=nonce,
            transaction_ready=True,native_groups=len(c['case_groups']),native_oracles_run=0,
            counter_scope='Transaction preflight only; CPU unit-test work is not counted as native preflight',
            cpu_tests_verified=test_group_size is None,calculation_verified=False,gpu_calls=0,driver_load_calls=0)
        exclusive(capture/'result.json',result);return result
    except BaseException as e:
        exclusive(capture/'failure.json',dict(error=type(e).__name__+': '+str(e),gpu_calls=0));raise
    finally:cli.collect(capture,capture/'artifacts.json')


def group(cli,transaction,index,capture):
    from portable_phase_audit import Journal
    from portable_parent_oracles import stamp
    transaction=Path(transaction).resolve();m,c=context(cli,transaction)
    if type(index) is not int or not 0<=index<len(c['case_groups']):raise ValueError('Staged native group outside plan')
    capture=outside(capture,[cli.ROOT,transaction,Path(c['gpu_capture'])]);capture.mkdir(parents=True,exist_ok=False)
    exclusive(transaction/('group-claim-'+str(index)+'.json'),dict(capture=str(capture),nonce=c['nonce'],group_index=index))
    j=Journal(capture/'phases.jsonl')
    try:
        cli.check_records(transaction,cli.load(transaction/'artifacts.json')['files'])
        from portable_staged_continuation import gate
        gate(cli,m,c)
        with cli.forbid_gpu():
            adapter,entries,data,receipt=j.invoke('staged_static_input',static_input,cli,m)
            if receipt!=c['input'] or data!=(transaction/'input.bin').read_bytes():raise ValueError('Staged prepared input changed')
            rows=[]
            for i in c['case_groups'][index]:
                name,_,domain=entries[i];before=stamp(domain)
                value=j.invoke('staged_native_reference',cli.native_value,adapter,domain,event_facts=dict(case_index=i,native=domain is not None))
                digest=adapter.cross.digest(value)
                if digest!=m['golden']['entries'][i]['native_sha256'] or stamp(domain)!=before:
                    raise ValueError('Staged native fingerprint/domain mismatch: '+name)
                rows.append(dict(case_index=i,name=name,input_sha256=m['golden']['entries'][i]['input_sha256'],native_sha256=digest,is_native=domain is not None))
        context(cli,transaction)
        j.emit('staged_group_complete','returned')
        result=dict(mode='staged-preflight-native-group-only',package_id=m['package_id'],transaction_nonce=c['nonce'],
            transaction_sha256=cli.sha((transaction/'transaction.json').read_bytes()),group_index=index,case_indices=c['case_groups'][index],
            entries=rows,native_cases=sum(r['is_native'] for r in rows),child_pid=os.getpid(),
            native_group_verified=True,all_native_preflight_verified=False,calculation_verified=False,gpu_calls=0,driver_load_calls=0)
        exclusive(capture/'result.json',result);return result
    except BaseException as e:
        exclusive(capture/'failure.json',dict(error=type(e).__name__+': '+str(e),gpu_calls=0));raise
    finally:cli.collect(capture,capture/'artifacts.json')


def native_evidence(cli,m,c,group_indices):
    transaction=Path(c['transaction'])
    pids=[];native=0;entries=[];anchors=[];stages=[]
    for index in group_indices:
        indices=c['case_groups'][index]
        claim=cli.load(transaction/('group-claim-'+str(index)+'.json'));proof=Path(claim['capture']).resolve()
        if type(claim.get('group_index')) is not int or claim!={'capture':str(proof),'nonce':c['nonce'],'group_index':index}:raise ValueError('Staged native group claim mismatch')
        cli.check_records(proof,cli.load(proof/'artifacts.json')['files'])
        row=cli.load(proof/'result.json');pid=row.get('child_pid')
        if (row.get('mode')!='staged-preflight-native-group-only' or row.get('package_id')!=m['package_id']
            or row.get('transaction_nonce')!=c['nonce'] or row.get('transaction_sha256')!=cli.sha((transaction/'transaction.json').read_bytes())
            or type(row.get('group_index')) is not int or row['group_index']!=index or json.dumps(row.get('case_indices'))!=json.dumps(indices)
            or row.get('native_group_verified') is not True or row.get('all_native_preflight_verified') is not False
            or row.get('calculation_verified') is not False or type(row.get('gpu_calls')) is not int or row['gpu_calls']!=0
            or type(row.get('driver_load_calls')) is not int or row['driver_load_calls']!=0
            or type(pid) is not int or pid<=0 or pid in pids or len(row.get('entries',[]))!=len(indices)):
            raise ValueError('Staged native group identity/scope mismatch')
        count=0
        for i,item in zip(indices,row['entries'],strict=True):
            want=dict(case_index=i,name=m['golden']['entries'][i]['name'],input_sha256=m['golden']['entries'][i]['input_sha256'],native_sha256=m['golden']['entries'][i]['native_sha256'],is_native=i in c['native_indices'])
            if json.dumps(item,sort_keys=True)!=json.dumps(want,sort_keys=True):raise ValueError('Staged native row differs from complete plan')
            count+=want['is_native'];entries.append(item)
        if type(row.get('native_cases')) is not int or row['native_cases']!=count:raise ValueError('Staged native count mismatch')
        pids.append(pid);native+=count
        envelope=terminal_cpu_stage(cli,proof,m,'preflight-native-group')
        if envelope.get('containment_verified') is True and envelope.get('child_pid')!=pid:
            raise ValueError('Staged native PID differs from bounded Job child')
        stages.append(dict(capture=str(proof),**envelope))
        names=['result.json','artifacts.json','phases.jsonl']
        anchors.append(dict(capture=str(proof),files=cli.file_records(proof,names)))
    return dict(native=native,entries=entries,pids=pids,stages=stages,anchors=anchors)


def admit(cli,m,transaction,backend,gpu_capture):
    transaction=Path(transaction).resolve();actual,c=context(cli,transaction,backend,gpu_capture)
    if actual!=m:raise ValueError('Staged execution package differs')
    cli.check_records(transaction,cli.load(transaction/'artifacts.json')['files'])
    from portable_staged_continuation import gate
    admitted=gate(cli,m,c);stages=admitted['stages'];prefix=admitted['evidence']
    expected=cli.transport_input_receipt(m,(transaction/'input.bin').read_bytes(),c['input']['input_words'])
    if expected!=c['input']:raise ValueError('Staged input receipt changed')
    evidence=native_evidence(cli,m,c,range(len(c['case_groups'])))
    pids=prefix['pids']+evidence['pids'];native=prefix['native']+evidence['native'];entries=prefix['entries']+evidence['entries'];anchors=prefix['anchors']+evidence['anchors'];stages+=evidence['stages']
    if len(set(pids))!=len(pids):raise ValueError('Continuation reused a native child PID')
    if native!=len(c['native_indices']) or len(entries)!=len(m['golden']['entries']):raise ValueError('Staged native preflight incomplete')
    return dict(schema=SCHEMA,package_id=m['package_id'],transaction=str(transaction),transaction_nonce=c['nonce'],
        transaction_sha256=cli.sha((transaction/'transaction.json').read_bytes()),host=c['host'],input=c['input'],
        native_cases=native,input_count=len(entries),groups=len(pids),fresh_child_pids=pids,stage_envelopes=stages,
        group_anchors=anchors,continuation_parent=admitted.get('parent'),original_timeout=admitted.get('failed'),
        all_native_preflight_verified=True,calculation_verified=False,gpu_calls=0)


def prepare_gpu_input(cli,m,transaction,capture,backend):
    receipt=admit(cli,m,transaction,backend,capture)
    _,_,data,static=static_input(cli,m)
    if static!=receipt['input']:raise ValueError('GPU static input differs from fresh native gates')
    cli.publish_transport_input(m,capture,data,static['input_words'])
    exclusive(capture/'staged-preflight.json',receipt)
    return receipt


def claim_execution(cli,transaction,capture):
    transaction=Path(transaction).resolve();m,c=context(cli,transaction,gpu_capture=capture)
    exclusive(transaction/'gpu-execution-claimed.json',dict(package_id=m['package_id'],nonce=c['nonce'],capture=str(Path(capture).resolve())))


def read_gpu_input(cli,m,capture):
    saved=cli.load(capture/'staged-preflight.json');transaction=Path(saved['transaction'])
    actual=admit(cli,m,transaction,cli.load(capture/'run.json')['backend'],capture)
    if actual!=saved:raise ValueError('Staged native admission changed after GPU claim')
    claim=cli.load(transaction/'gpu-execution-claimed.json')
    if claim!=dict(package_id=m['package_id'],nonce=saved['transaction_nonce'],capture=str(capture.resolve())):raise ValueError('Staged GPU execution claim mismatch')
    data=(capture/'input.bin').read_bytes();receipt=cli.transport_input_receipt(m,data,saved['input']['input_words'])
    if receipt!=saved['input'] or cli.load(capture/'input-preflight.json')!=receipt:raise ValueError('Staged GPU input changed')
    return data,receipt['input_words']


def finish_gpu(cli,m,capture,facts,backend):
    """Durable dispatch receipt, explicitly awaiting fresh native comparison."""
    from portable_phase_audit import summarize,verify_cuda_trace
    error=None;completed=False;matched=False;containment=None
    try:
        read_gpu_input(cli,m,capture)
        evidence=cli.load(capture/'evidence.json')
        raw=cli.file_records(capture,['readback.bin'])[0]
        expected_bytes=len(m['golden']['entries'])*product_configuration(cli.SUITES,m).get('output_words',786432)*4
        matched=bool(raw['bytes']==expected_bytes and raw['sha256']==m['golden']['output_sha256']==evidence['output_sha256'])
        completed=bool(facts.get('passed') is True and evidence['backend']==backend
            and evidence['gpu_execution_verified'] is True and evidence['transport']['command_status']=='completed'
            and evidence['transport']['cases']==len(m['golden']['entries'])
            and evidence['source_sha256']==m['golden']['source_sha256'])
        if backend=='cuda':
            rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
            containment,pid=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
            completed &= bool(containment and verify_cuda_trace(rows,pid=pid))
        cli.audit_generation_capture(m,capture)
    except (ValueError,KeyError,OSError) as e:error=type(e).__name__+': '+str(e);completed=False
    return dict(mode='staged-gpu-pending-native-audit',package_id=m['package_id'],gpu_execution_completed=bool(completed),
        readback_fingerprint_matches=matched,staged_preflight_verified=error is None,
        pending_native_audit=True,calculation_verified=False,containment_verified=containment,
        preservation_verified=cli.environment_preserved(capture,facts,backend),passed=False,
        error=error,gpu_retries=0,scope='Dispatch and sealed-output fingerprint only; fresh saved-result native audit remains required')
