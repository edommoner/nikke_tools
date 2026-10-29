"""One claimed snapshot -> existing shared execute; independent audit pending.

No public launch command until the parent/audit path is complete. The child
cannot turn a serialized preparation flag into execution ownership.
"""
import ctypes as C,json,os,time
from pathlib import Path
from portable_admission_authority import PROTOCOL,is_windows,same
from portable_admission_snapshot import binding,digest,hex_string
from portable_admission_handoff import Handoff
from portable_staged_preflight import exclusive,host

RUN_SCHEMA='prepared-execution-run-v1'
CLAIM_FIELDS={'schema','protocol','package_id','nonce','capture','consumer_package_id','preparation_package_id','authority','authority_sha256','snapshot_sha256','certificate_sha256'}


def ownership(cli,m,capture,expected_claim_sha256):
    """Check mirrored append-only ownership, fixed authority and source anchors."""
    capture=Path(capture).resolve()
    if not is_windows() or not hex_string(expected_claim_sha256,64):raise ValueError('Original-host pinned execution ownership required')
    raw=(cli.ROOT/'gpu-claimed-cuda.json').read_bytes()
    if digest(raw)!=expected_claim_sha256:raise ValueError('External execution claim SHA mismatch')
    claim=json.loads(raw)
    if (type(claim) is not dict or set(claim)!=CLAIM_FIELDS or claim['schema']!='prepared-execution-ownership-v1'
        or claim['protocol']!=PROTOCOL or claim['consumer_package_id']!=m['package_id']
        or claim['capture']!=str(capture)
        or any(not hex_string(claim[k],64) for k in ('package_id','consumer_package_id','preparation_package_id','authority_sha256','snapshot_sha256','certificate_sha256'))
        or not hex_string(claim['nonce'],32)):
        raise ValueError('Execution ownership identity/protocol mismatch')
    authority_path=Path(claim['authority'])
    authority_raw=authority_path.read_bytes()
    if digest(authority_raw)!=claim['authority_sha256']:raise ValueError('Execution authority changed')
    a=json.loads(authority_raw);b=binding(a['binding'])
    if (a['schema']!='prepared-admission-authority-v1' or a['protocol']!=PROTOCOL or a['authority_verified'] is not True
        or a['execution_admitted'] is not False or a['calculation_verified'] is not False
        or type(a['gpu_calls']) is not int or a['gpu_calls']!=0
        or a['consumer_package_id']!=m['package_id'] or b['owner_package_id']!=claim['package_id']
        or b['controller_package_id']!=claim['preparation_package_id'] or b['transaction_nonce']!=claim['nonce']
        or b['future_capture']!=str(capture) or a['snapshot_sha256']!=claim['snapshot_sha256']
        or a['certificate_sha256']!=claim['certificate_sha256'] or a['host']!=host(cli)
        or a['envelope']['containment_verified'] is not True or a['envelope']['process_preservation_verified'] is not True):
        raise ValueError('Execution authority binding/host mismatch')
    if (Path(a['transaction'])/'gpu-execution-claimed.json').read_bytes()!=raw or (authority_path.parent/'claim.json').read_bytes()!=raw:
        raise ValueError('Execution ownership mirrors incomplete or changed')
    # The child already ran the complete shared package verifier. Check its
    # identical record list rather than rereading all consumer files twice.
    consumer_rows=[*m['files'],*cli.file_records(cli.ROOT,['gpu-package.json'])]
    seen_consumer=False
    for anchor in a['anchors']:
        root=Path(anchor['root']).resolve()
        if root==cli.ROOT.resolve():
            if seen_consumer or not same(anchor['files'],consumer_rows):raise ValueError('Execution consumer source anchor mismatch')
            seen_consumer=True
        else:cli.check_records(root,anchor['files'])
    if not seen_consumer:raise ValueError('Execution consumer source anchor absent')
    return claim,a


def live_job():
    """Read-only shared Windows ABI; no CUDA/driver call."""
    from portable_job_limits import read_job_limits
    result=read_job_limits(C.WinDLL('kernel32',use_last_error=True),None,include_flags=True)
    if result['job_memory_limit_bytes']!=2147483648 or not result['job_limit_flags']&0x2000:
        raise ValueError('Prepared execution requires bounded kill-on-close 2GiB Job')
    return result


def child(cli,capture,expected_claim_sha256):
    if not is_windows():raise ValueError('Prepared CUDA child requires Windows')
    capture=Path(capture).resolve()
    if os.path.lexists(capture/'prepared-child-started.json'):raise FileExistsError('Prepared child attempt already started')
    deadline=time.monotonic()+60
    while not (capture/'start.json').is_file():
        if time.monotonic()>=deadline:raise RuntimeError('Prepared execution start gate not released')
        time.sleep(.02)
    from portable_phase_audit import Journal,observe
    journal=Journal(capture/'phases.jsonl')
    m=journal.invoke('prepared_child_verify_package',cli.verify_package,cli.ROOT)
    if cli.is_development(m) or cli.compiler_only(m):raise ValueError('Prepared child requires a sealed battle package')
    claim,a=journal.invoke('prepared_child_ownership',ownership,cli,m,capture,expected_claim_sha256)
    run=cli.load(capture/'run.json');config=cli.SUITES[m['suite']]
    if (run.get('schema')!=RUN_SCHEMA or run.get('input_protocol')!=PROTOCOL or run.get('mode')!='snapshot-gpu'
        or run.get('backend')!='cuda' or run.get('package_id')!=m['package_id'] or run.get('capture')!=str(capture)
        or run.get('claim_sha256')!=expected_claim_sha256 or run.get('authority_sha256')!=claim['authority_sha256']
        or not same(run.get('binding'),a['binding'])):
        raise ValueError('Prepared child run/ownership mismatch')
    requested=run.get('resource_observation_requested',False)
    if type(requested) is not bool or os.environ.get('NIKKE_CUDA_RESOURCE_OBSERVATION','0')!=str(int(requested)):
        raise ValueError('Prepared child resource observation setting mismatch')
    if (os.environ.get('NIKKE_SLANG_GENERATION_REQUIRED')!='1' or os.environ.get('NIKKE_CUDA_ARTIFACT')!='cubin'
        or any(not os.environ.get(k) or not Path(os.environ[k]).is_absolute() or not Path(os.environ[k]).is_dir()
            for k in ('NIKKE_SLANG_ROOT','NIKKE_SLANG_GENERATION_CACHE'))):
        raise ValueError('Prepared child requires explicit paired generation cache and saved CUBIN')
    limits=live_job();journal.emit('prepared_child_job','verified',limits=limits)
    # The marker is exclusive and durable before any GPU/driver request. An
    # interrupted or failed child never permits a second launch of this claim.
    exclusive(capture/'prepared-child-started.json',dict(package_id=m['package_id'],claim_sha256=expected_claim_sha256,pid=os.getpid(),calculation_verified=False))
    entered=False
    try:
        with Handoff(cli,a['snapshot'],a['snapshot_sha256'],certificate_sha256=a['certificate_sha256'],
                expected_binding=a['binding'],expected_suite=m['suite'],expected_golden=m['golden'],consumer_package_id=m['package_id'],header_materials=a.get('header_materials')) as handoff:
            data,words=handoff.read_input()
            # Retain the exact frozen input for the existing independent native
            # comparator. Never reconstruct or overwrite an interrupted capture.
            with (capture/'input.bin').open('xb') as stream:
                stream.write(data);stream.flush();os.fsync(stream.fileno())
            import portable_backend
            with handoff.saved_provider('cuda',journal),observe(portable_backend,journal):
                entered=True
                raw,evidence=journal.invoke('shared_gpu_execute',portable_backend.execute,config['source'],'portableEvents',data,
                    words,config.get('output_words',786432),'cuda',readback_path=capture/'readback.bin')
            if raw is not None:raise ValueError('Prepared file transport returned a whole readback')
            exclusive(capture/'evidence.json',evidence)
            cli.copy_generated(capture,m['suite'])
            output=cli.file_records(capture,['readback.bin'])[0]
            expected_bytes=len(m['golden']['entries'])*config.get('output_words',786432)*4
            if (output['bytes']!=expected_bytes or output['sha256']!=evidence['output_sha256']
                or evidence['transport'].get('cases')!=len(m['golden']['entries'])
                or evidence['transport'].get('input_bytes')!=len(data) or evidence['transport'].get('output_bytes')!=expected_bytes):
                raise ValueError('Prepared file readback/evidence mismatch')
            if (evidence.get('backend')!='cuda' or evidence.get('gpu_execution_verified') is not True
                or evidence['input_sha256']!=a['binding']['input_sha256'] or evidence['transport']['command_status']!='completed'):
                raise ValueError('Prepared shared execution did not complete')
        from portable_phase_audit import verify_cuda_trace
        rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
        if not verify_cuda_trace(rows,pid=os.getpid()):raise ValueError('Prepared CUDA native trace incomplete')
        exclusive(capture/'dispatch.json',dict(schema=RUN_SCHEMA,protocol=PROTOCOL,package_id=m['package_id'],claim_sha256=expected_claim_sha256,
            gpu_execution_completed=True,calculation_verified=False,independent_post_audit_required=True,
            input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256']))
    except BaseException as error:
        exclusive(capture/'prepared-child-failure.json',dict(error=type(error).__name__+': '+str(error),shared_execute_entered=entered,
            gpu_calls=None if entered else 0,calculation_verified=False,execution_claim_retained=True))
        raise
