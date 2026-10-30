"""Reuse a bounded CPU admission, revalidate exact bytes at the GPU boundary.

No native values are cached. The complete source-host audit remains retained;
its fingerprints, Job envelope and consumed claims are bound to a small receipt.
The provider never repeats the producer audit or starts a compiler.
"""
from portable_product_programs import configuration as product_configuration
import contextlib,json
from pathlib import Path
from unittest.mock import patch

AUDITOR='97e9477eed96614e1ab8a916effb99ec939d9be17a6757fea11e6135b63e1872'
CURRENT='partitioned-current-cubin-admission-v1'
CURRENT_PACKAGE=('gpu-package.json','jit-link-object-claimed-cuda.json')
CURRENT_CAPTURE=('artifacts.json','run.json','result.json','execution.json','job.json','phases.jsonl',
                 'jit-link.json','object-request.json','observation.json')


def canonical(cli,value):return cli.sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())


def prepare(cli,manifest,auditor_root,capture,*,generated_cuda_source):
    from portable_continuation_package import owner_snapshot
    from portable_partitioned_cuda_origin import MODE,OWNER,failure_trace
    from portable_linked_artifact import valid_receipt,read_verified
    auditor_root=Path(auditor_root).resolve();capture=Path(capture).resolve()
    auditor=owner_snapshot(cli,auditor_root)['manifest']
    if auditor['package_id']!=AUDITOR or auditor['golden']!=manifest['golden']:raise ValueError('Exact audited corpus/source owner required')
    anchors=cli.load(capture/'artifacts.json')['files'];cli.check_records(capture,anchors)
    result=cli.load(capture/'result.json');origin=cli.load(capture/'origin.json');facts=cli.load(capture/'execution.json')
    rows=[json.loads(x) for x in (capture/'phases.jsonl').read_bytes().splitlines()]
    contained,pid=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
    if (result.get('mode')!=MODE or result.get('package_id')!=AUDITOR or result.get('passed') is not True
        or result.get('containment_verified') is not True or result.get('native_admission_revalidated') is not True
        or result.get('execution_permitted') is not False or result.get('calculation_verified') is not False
        or any(result.get(k)!=0 for k in ('gpu_calls','compiler_calls','native_calls'))
        or facts.get('passed') is not True or facts.get('timed_out') is not False
        or facts.get('child_exit_code')!=0 or facts.get('final_child_exit_code')!=0 or facts.get('below_normal_priority') is not True
        or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error')) or not contained
        or type(facts.get('timeout_seconds')) not in (int,float) or not 0<facts['timeout_seconds']<=180):
        raise ValueError('Complete bounded original-admission audit required')
    if (origin.get('schema')!=MODE or origin.get('original_package_id')!=OWNER or origin.get('golden')!=manifest['golden']
        or origin.get('native_admission_revalidated') is not True or origin.get('input_count')!=len(manifest['golden']['entries'])
        or origin.get('native_cases')!=product_configuration(cli.SUITES,manifest)['native'] or origin.get('claims_modified') is not False
        or origin.get('original_stage_passed') is not False or origin.get('execution_permitted') is not False
        or any(origin.get(k)!=0 for k in ('gpu_calls','compiler_calls','native_calls'))
        or not valid_receipt(origin.get('linked_receipt',{}))):raise ValueError('Original admission or saved CUBIN changed')
    failure_trace(origin['native_events'])
    small=['gpu-package.json']
    package_records=cli.file_records(auditor_root,small)
    capture_records=cli.file_records(capture,['artifacts.json','run.json','result.json','origin.json','execution.json','job.json','phases.jsonl'])
    run=cli.load(capture/'run.json');old_root=Path(run['source_package']);old_capture=Path(run['source_capture'])
    if cli.sha((old_capture/'proof/phases.jsonl').read_bytes())!=origin['original_failure_sha256']:raise ValueError('Consumed launch failure changed')
    claims=[]
    for row in origin['claims']:
        p=Path(row['path']);record=cli.file_records(p.parent,[p.name])[0]
        if record['sha256']!=row['sha256'] or record['bytes']!=row['bytes']:raise ValueError('Consumed original claim changed')
        claims.append(dict(path=str(p),bytes=record['bytes'],sha256=record['sha256']))
    state=dict(schema='partitioned-pinned-cubin-admission-v1',auditor_package_id=AUDITOR,auditor_root=str(auditor_root),
               source_capture=str(capture),package_records=package_records,capture_records=capture_records,
               old_source_root=str(old_root),old_capture=str(old_capture),old_failure_sha256=origin['original_failure_sha256'],
               claims=claims,linked_receipt=origin['linked_receipt'],linked_artifact=origin['linked_artifact'],
               golden_sha256=canonical(cli,manifest['golden']),native_cases=origin['native_cases'],input_count=origin['input_count'],
               audited_child_pid=pid,execution_permitted=False,native_values_reused=False,gpu_calls=0)
    # Recheck every retained audit artifact at the end of the CPU stage.
    with cli.forbid_gpu():read_verified(state['linked_receipt'],generated_cuda_source,state['linked_artifact'])
    cli.check_records(capture,anchors);check(cli,manifest,state)
    return state


def check(cli,manifest,state):
    """Small receipt anchors plus original claims; no recursive producer audit."""
    if state.get('schema')==CURRENT:return check_current(cli,manifest,state)
    from portable_linked_artifact import valid_receipt
    if (state.get('schema')!='partitioned-pinned-cubin-admission-v1' or state.get('auditor_package_id')!=AUDITOR
        or state.get('golden_sha256')!=canonical(cli,manifest['golden']) or state.get('execution_permitted') is not False
        or state.get('native_values_reused') is not False or not valid_receipt(state.get('linked_receipt',{}))
        or state.get('input_count')!=len(manifest['golden']['entries']) or state.get('native_cases')!=product_configuration(cli.SUITES,manifest)['native']):raise ValueError('Pinned admission identity changed')
    identity=state['linked_receipt']['identity']
    if identity.get('source_closure')!=manifest['golden']['source_sha256'] or identity.get('generated_normalized')!=manifest['golden']['generated_normalized']:
        raise ValueError('Pinned CUBIN differs from complete frozen GPU source')
    if [r['path'] for r in state['package_records']]!=['gpu-package.json'] or {r['path'] for r in state['capture_records']}!={'artifacts.json','run.json','result.json','origin.json','execution.json','job.json','phases.jsonl'}:
        raise ValueError('Complete pinned receipt anchors required')
    cli.check_records(Path(state['auditor_root']),state['package_records'])
    cli.check_records(Path(state['source_capture']),state['capture_records'])
    original=cli.load(Path(state['source_capture'])/'origin.json')
    if original['linked_receipt']!=state['linked_receipt'] or original['linked_artifact']!=state['linked_artifact'] or original['claims']!=state['claims']:
        raise ValueError('Pinned artifact or claims differ from the audited origin')
    original_claim=cli.load(Path(state['claims'][0]['path']))
    if Path(original_claim['capture']).resolve()!=(Path(state['old_capture'])/'proof').resolve():
        raise ValueError('Pinned origin path differs from the consumed execution claim')
    if cli.sha((Path(state['old_capture'])/'proof/phases.jsonl').read_bytes())!=state['old_failure_sha256']:raise ValueError('Original launch failure changed after CPU audit')
    for r in state['claims']:
        p=Path(r['path']);record=cli.file_records(p.parent,[p.name])[0]
        if record['bytes']!=r['bytes'] or record['sha256']!=r['sha256']:raise ValueError('Original consumed claim changed after CPU audit')
    return True


def prepare_current(cli,manifest,linked_root,linked_capture,*,generated_cuda_source):
    """Audit the new source's complete producer/object/link chain once, CPU only."""
    from portable_linked_artifact import read_verified
    linked_root=Path(linked_root).resolve();linked_capture=Path(linked_capture).resolve()
    with cli.forbid_gpu():checked=cli.saved_linked_admission(manifest,dict(package=str(linked_root),capture=str(linked_capture)))
    state=dict(schema=CURRENT,linked_root=str(linked_root),source_capture=str(linked_capture),
        package_records=cli.file_records(linked_root,CURRENT_PACKAGE),capture_records=cli.file_records(linked_capture,CURRENT_CAPTURE),
        linked_receipt=checked['receipt'],linked_artifact=checked['artifact'],golden_sha256=canonical(cli,manifest['golden']),
        input_count=len(manifest['golden']['entries']),native_cases=product_configuration(cli.SUITES,manifest)['native'],
        execution_permitted=False,native_values_reused=False,gpu_calls=0)
    with cli.forbid_gpu():read_verified(state['linked_receipt'],generated_cuda_source,state['linked_artifact'])
    check_current(cli,manifest,state)
    return state


def check_current(cli,manifest,state):
    from portable_linked_artifact import valid_receipt
    if (state.get('schema')!=CURRENT or state.get('execution_permitted') is not False
        or state.get('native_values_reused') is not False or type(state.get('gpu_calls')) is not int or state.get('gpu_calls')!=0
        or state.get('golden_sha256')!=canonical(cli,manifest['golden'])
        or state.get('input_count')!=len(manifest['golden']['entries'])
        or state.get('native_cases')!=product_configuration(cli.SUITES,manifest)['native']
        or not valid_receipt(state.get('linked_receipt',{}))):raise ValueError('Current source CUBIN admission changed')
    for key,names in (('package_records',CURRENT_PACKAGE),('capture_records',CURRENT_CAPTURE)):
        rows=state.get(key,[])
        if len(rows)!=len(names) or {r['path'] for r in rows}!=set(names):raise ValueError('Complete current admission anchors required')
    root=Path(state['linked_root']);capture=Path(state['source_capture'])
    cli.check_records(root,state['package_records']);cli.check_records(capture,state['capture_records'])
    receipt=state['linked_receipt'];identity=receipt['identity'];anchors=identity['anchors']
    if (identity.get('source_closure')!=manifest['golden']['source_sha256']
        or identity.get('generated_normalized')!=manifest['golden']['generated_normalized']
        or anchors['package_id']!=cli.load(root/'gpu-package.json')['package_id']
        or anchors['manifest_sha256']!=cli.sha((root/'gpu-package.json').read_bytes())
        or anchors['artifacts_sha256']!=cli.sha((capture/'artifacts.json').read_bytes())
        or anchors['claim_sha256']!=cli.sha((root/'jit-link-object-claimed-cuda.json').read_bytes())):
        raise ValueError('Current CUBIN source or owner anchors changed')
    proof=cli.load(capture/'jit-link.json')['receipt']
    if (proof['identity']!=identity['link_identity'] or proof['key']!=anchors['link_receipt_key']
        or proof['artifact']['sha256']!=receipt['artifact_sha256'] or proof['artifact']['bytes']!=receipt['artifact_bytes']
        or Path(state['linked_artifact']).resolve()!=(capture/'jit-linked.cubin').resolve()
        or Path(cli.load(root/'jit-link-object-claimed-cuda.json')['capture']).resolve()!=capture.resolve()):
        raise ValueError('Current CUBIN link receipt or original claim changed')
    return True


@contextlib.contextmanager
def provider(cli,manifest,state,capture,journal):
    import portable_backend as backend
    from portable_linked_artifact import read_verified,STAGE
    check(cli,manifest,state);calls=0
    def saved(source,*,artifact_kind=None):
        nonlocal calls
        if calls or (artifact_kind or backend.cuda_artifact_kind())!='cubin':raise ValueError('One exact saved CUBIN activation required')
        check(cli,manifest,state)
        image,receipt=journal.invoke('cuda_pinned_linked_artifact',read_verified,state['linked_receipt'],source,state['linked_artifact'])
        calls+=1
        with (Path(capture)/'compiled.cubin').open('xb') as out:out.write(image)
        journal.emit(STAGE,'verified',receipt=receipt)
        return image,receipt
    def forbidden(*a,**k):raise RuntimeError('Compiler fallback forbidden by pinned CUBIN admission')
    with patch.object(backend,'compile_cuda_source',saved),patch.object(backend,'compile_cuda_artifact',forbidden):
        yield
        if calls!=1:raise ValueError('Pinned CUBIN was not activated exactly once')
        check(cli,manifest,state)
