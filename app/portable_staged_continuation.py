"""Refine only an unfinished tail of the same unexecuted GPU attempt.

Keep original failed stages and completed fingerprint receipts in place.
No native values are loaded, persisted, or supplied to the GPU.
"""
from portable_product_programs import configuration as product_configuration
import json,os,uuid
from pathlib import Path
from types import SimpleNamespace
from portable_comparison_groups import partition
from portable_continuation_package import owner_snapshot,validate_lineage

CLAIM='preflight-continuation-claimed-'


def tail_groups(count,start,size,*,native_indices=None,reject_group_size=None):
    if type(start) is not int or not 0<=start<count:raise ValueError('Invalid continuation boundary')
    if reject_group_size is not None:
        if type(reject_group_size) is not int or not 1<=reject_group_size<=count:raise ValueError('Invalid rejected-input group size')
        if (type(native_indices) is not list or any(type(i) is not int or not 0<=i<count for i in native_indices)
            or native_indices!=sorted(set(native_indices))):raise ValueError('Exact native membership required')
        partition(count,size)
        native=set(native_indices);groups=[];group=[]
        for i in range(start,count):
            is_native=i in native
            if group and ((group[0] in native)!=is_native or len(group)>=(size if is_native else reject_group_size)):
                groups.append(group);group=[]
            group.append(i)
        if group:groups.append(group)
        return groups
    return [[i+start for i in indices] for indices in partition(count-start,size)]


def _failed_timeout(cli,m,c,index):
    """A failed stage is eligible for refinement, never promoted to success."""
    claim=cli.load(Path(c['transaction'])/('group-claim-'+str(index)+'.json'))
    proof=Path(claim['capture']).resolve();outer=proof.parent
    if claim!=dict(capture=str(proof),nonce=c['nonce'],group_index=index):raise ValueError('Failed native claim changed')
    if any((proof/name).exists() for name in ('result.json','artifacts.json')):
        raise ValueError('Only an incomplete timed-out native stage may be refined')
    plan=cli.load(outer/'recipe.json');facts=cli.load(outer/'execution.json')
    packet=cli.module(cli.ROOT/'scripts/run-gpu-packet.py')
    expected=packet.recipe(m['package_id'],'preflight-native-group',c['backend'],outer,plan['original_workspace'],plan['timeout_seconds'],plan['object_request'])
    request=dict(transaction=c['transaction'],group_index=str(index))
    if (plan!=expected or plan['object_request']!=request or Path(plan['proof_capture']).resolve()!=proof
        or facts.get('timed_out') is not True or facts.get('passed') is not False
        or type(facts.get('timeout_seconds')) not in (int,float) or not 0<facts['timeout_seconds']<=180
        or facts.get('final_child_exit_code') is None or facts.get('cleanup_error') is not None or facts.get('observation_error') is not None):
        raise ValueError('Original native stage is not a clean bounded timeout')
    envelope=dict(original_stage_verified=False,original_timed_out=True,preservation_verified=None,containment_verified=None)
    if os.name=='nt':
        from windows_validation_observer import compare_snapshots
        rows=[json.loads(line) for line in (proof/'phases.jsonl').read_text().splitlines()]
        contained,pid=cli.job_contained(outer,rows,memory_limit_bytes=2147483648)
        observation=cli.load(outer/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
        if (not contained or facts.get('below_normal_priority') is not True or plan['memory_limit_mb']!=2048
            or observation['comparison']!=comparison or comparison['missing_existing_processes']):
            raise ValueError('Original timeout Job/observation did not finish safely')
        envelope.update(containment_verified=True,child_pid=pid,preservation_verified=cli.environment_preserved(outer,facts))
    paths=[p.relative_to(outer).as_posix() for p in outer.rglob('*') if p.is_file()]
    return dict(capture=str(proof),envelope=envelope,files=cli.file_records(outer,paths))


def parent_evidence(cli,current,parent_transaction,*,expected=None):
    from portable_staged_preflight import context,host,native_evidence,terminal_cpu_stage
    from portable_staged_tests import admit_tests
    transaction=Path(parent_transaction).resolve();old=cli.load(transaction/'transaction.json');root=Path(old['package_root']).resolve()
    info=owner_snapshot(cli,root);m=info['manifest'];validate_lineage(cli,current,m,root)
    if info['config']!=product_configuration(cli.SUITES,current) or old.get('resume_parent'):
        raise ValueError('Continuation requires unchanged suite and an original transaction')
    owner=SimpleNamespace(**{**vars(cli),'ROOT':root,'SMOKE_TESTS':info['smoke'],
        'verify_package':lambda path:m if Path(path).resolve()==root else (_ for _ in ()).throw(ValueError('Original owner root changed'))})
    actual,c=context(owner,transaction)
    gpu=Path(c['gpu_capture'])
    if actual!=m or c['host']!=host(cli) or (transaction/'gpu-execution-claimed.json').exists():
        raise ValueError('Continuation requires the same host before GPU execution')
    if gpu.exists():
        run=cli.load(gpu/'run.json') if (gpu/'run.json').is_file() else {}
        if (expected is None or run.get('package_id')!=current['package_id'] or run.get('backend')!=c['backend']
            or run.get('mode')!='staged-gpu' or run.get('input_protocol')!='staged-prepared-v1'):
            raise ValueError('Continuation requires an original attempt before GPU execution')
    cli.check_records(transaction,cli.load(transaction/'artifacts.json')['files'])
    stages=[dict(capture=str(transaction),**terminal_cpu_stage(owner,transaction,m,'preflight-plan' if 'test_groups' in c else 'preflight-begin'))]
    stages+=admit_tests(owner,m,c)
    prefix=0
    for index in range(len(c['case_groups'])):
        p=transaction/('group-claim-'+str(index)+'.json')
        if not p.exists():break
        target=Path(cli.load(p)['capture'])
        if not (target/'result.json').is_file() or not (target/'artifacts.json').is_file():break
        prefix+=1
    if prefix>=len(c['case_groups']):raise ValueError('Original native preflight already complete')
    if any((transaction/('group-claim-'+str(i)+'.json')).exists() for i in range(prefix+1,len(c['case_groups']))):
        raise ValueError('Original groups continued after failure')
    failed=_failed_timeout(owner,m,c,prefix)
    evidence=native_evidence(owner,m,c,range(prefix));stages+=evidence['stages']
    count=len(evidence['entries'])
    if [row['case_index'] for row in evidence['entries']]!=list(range(count)):
        raise ValueError('Original native receipts are not a complete prefix')
    metadata=dict(transaction=str(transaction),package_root=str(root),package_id=m['package_id'],
        manifest_sha256=cli.sha((root/'gpu-package.json').read_bytes()),transaction_sha256=cli.sha((transaction/'transaction.json').read_bytes()),
        transaction_nonce=c['nonce'],failed_group_index=prefix,completed_inputs=count,gpu_capture=c['gpu_capture'],backend=c['backend'])
    if expected is not None and metadata!=expected:raise ValueError('Original continuation lineage changed')
    return dict(parent=metadata,context=c,evidence=evidence,stages=stages,failed=failed)


def gate(cli,m,c):
    """Revalidate original receipts each time; do not cache numerical results."""
    from portable_staged_preflight import terminal_cpu_stage
    parent=c.get('resume_parent')
    if parent is None:
        from portable_staged_tests import admit_tests
        return dict(evidence=dict(native=0,entries=[],pids=[],stages=[],anchors=[]),
            stages=[dict(capture=c['transaction'],**terminal_cpu_stage(cli,Path(c['transaction']),m,'preflight-plan' if 'test_groups' in c else 'preflight-begin'))]+admit_tests(cli,m,c))
    original=parent_evidence(cli,m,parent['transaction'],expected=parent)
    if cli.load(Path(c['transaction'])/'original-evidence.json')!=original:raise ValueError('Original continuation evidence bytes changed')
    if (c['gpu_capture']!=parent['gpu_capture'] or c['backend']!=parent['backend'] or c['input']['input_sha256']!=original['context']['input']['input_sha256']
        or c['native_indices']!=original['context']['native_indices']):raise ValueError('Continuation changed original run input/membership')
    claim=cli.load(Path(parent['package_root'])/(CLAIM+c['backend']+'.json'))
    if claim!=dict(package_id=m['package_id'],transaction=c['transaction'],transaction_nonce=c['nonce'],parent_transaction=parent['transaction'],gpu_capture=c['gpu_capture']):
        raise ValueError('Original continuation ownership changed')
    stages=original['stages']+[dict(capture=c['transaction'],**terminal_cpu_stage(cli,Path(c['transaction']),m,'preflight-resume'))]
    return dict(evidence=original['evidence'],stages=stages,parent=parent,failed=original['failed'])


def resume(cli,capture,parent_transaction,group_size,backend,*,reject_group_size=None):
    from portable_staged_preflight import SCHEMA,host,outside,static_input,exclusive
    from portable_phase_audit import Journal
    m=cli.verify_package(cli.ROOT);original=parent_evidence(cli,m,parent_transaction)
    parent=original['parent'];old=original['context']
    if backend!=parent['backend']:raise ValueError('Continuation backend changed')
    if type(group_size) is not int or not 1<=group_size<old['group_size']:
        raise ValueError('Continuation must use strictly smaller native groups')
    capture=outside(capture,[cli.ROOT,Path(parent['package_root']),Path(parent_transaction),Path(parent['gpu_capture'])])
    capture.mkdir(parents=True,exist_ok=False);j=Journal(capture/'phases.jsonl');nonce=uuid.uuid4().hex
    try:
        cli.capture_storage_preflight(m,capture)
        _,entries,data,receipt=j.invoke('continuation_static_input',static_input,cli,m)
        if data!=(Path(parent_transaction)/'input.bin').read_bytes():raise ValueError('Continuation prepared input differs')
        native_indices=[i for i,(_,_,d) in enumerate(entries) if d is not None]
        if native_indices!=old['native_indices']:raise ValueError('Continuation native membership differs')
        c=dict(schema=SCHEMA,package_id=m['package_id'],manifest_sha256=cli.sha((cli.ROOT/'gpu-package.json').read_bytes()),
            package_root=str(cli.ROOT.resolve()),transaction=str(capture),nonce=nonce,backend=parent['backend'],gpu_capture=parent['gpu_capture'],
            host=host(cli),group_size=group_size,case_groups=tail_groups(len(entries),parent['completed_inputs'],group_size,
                native_indices=native_indices,reject_group_size=reject_group_size),
            native_indices=native_indices,input=receipt,resume_parent=parent,admission_schema='same-attempt-continuation-v1')
        if reject_group_size is not None:c['reject_group_size']=reject_group_size
        exclusive(Path(parent['package_root'])/(CLAIM+c['backend']+'.json'),dict(package_id=m['package_id'],transaction=str(capture),transaction_nonce=nonce,parent_transaction=parent['transaction'],gpu_capture=c['gpu_capture']))
        exclusive(cli.ROOT/('gpu-claimed-'+c['backend']+'.json'),dict(package_id=m['package_id'],capture=c['gpu_capture'],transaction=str(capture),transaction_nonce=nonce))
        cli.publish_transport_input(m,capture,data,receipt['input_words']);exclusive(capture/'transaction.json',c)
        exclusive(capture/'original-evidence.json',original)
        j.emit('continuation_ready','returned')
        result=dict(mode='staged-preflight-resume-only',package_id=m['package_id'],transaction_ready=True,
            original_completed_inputs=parent['completed_inputs'],original_native_cases=original['evidence']['native'],
            original_failed_stage_verified=False,cpu_test_evidence_retained_from_same_attempt=True,
            native_values_reused=False,native_oracles_run=0,calculation_verified=False,gpu_calls=0,driver_load_calls=0)
        exclusive(capture/'result.json',result);return result
    except BaseException as error:
        exclusive(capture/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_calls=0));raise
    finally:cli.collect(capture,capture/'artifacts.json')
