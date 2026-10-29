"""CPU-only partial native audit for snapshot-prepared CUDA captures.

Uses the existing comparator, generation verifier, Job/trace verifier and group
aggregator contract. A subset is never a complete calculation certificate.
"""
import json,os,threading
from pathlib import Path
from unittest.mock import patch
from portable_admission_authority import same,base_python
from portable_admission_handoff import Handoff
from portable_prepared_execution import ownership,RUN_SCHEMA
from portable_comparison_groups import selection
from portable_phase_audit import verify_cuda_trace,summarize
from windows_validation_observer import compare_snapshots

_COMPARISON=threading.Lock()


def current_pid():return os.getpid()


def envelope(cli,m,capture,claim_sha256):
    """Authenticate the actual completed child, separately from native parity."""
    capture=Path(capture).resolve();claim,a=ownership(cli,m,capture,claim_sha256)
    run=cli.load(capture/'run.json');facts=cli.load(capture/'execution.json')
    if (run.get('schema')!=RUN_SCHEMA or run.get('mode')!='snapshot-gpu'
        or run.get('input_protocol')!=claim['protocol'] or run.get('backend')!='cuda'
        or run.get('package_id')!=m['package_id'] or run.get('capture')!=str(capture)
        or run.get('claim_sha256')!=claim_sha256 or run.get('authority_sha256')!=claim['authority_sha256']
        or not same(run.get('binding'),a['binding'])):
        raise ValueError('Prepared audit run/ownership mismatch')
    if (facts.get('passed') is not True or facts.get('timed_out') is not False
        or any(type(facts.get(k)) is not int or facts[k]!=0 for k in ('child_exit_code','final_child_exit_code'))
        or facts.get('below_normal_priority') is not True
        or type(facts.get('timeout_seconds')) not in (int,float) or not 0<facts['timeout_seconds']<=60
        or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error'))):
        raise ValueError('Prepared GPU child did not complete within its bound')
    command=cli.load(capture/'command.json');python=str(base_python())
    argv=[python,str(cli.ROOT/'scripts/nikke_gpu.py'),'_prepared_child','--capture',str(capture),'--claim-sha256',claim_sha256]
    if (not same(command.get('argv'),argv) or command.get('cwd')!=str(cli.ROOT)
        or command.get('base_python')!=python or command.get('shell') is not False
        or type(command.get('timeout_seconds')) is not int or command['timeout_seconds']!=facts['timeout_seconds']):
        raise ValueError('Prepared child command identity mismatch')
    rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
    requested=run.get('resource_observation_requested',False)
    runtime=cli.load(capture/'runtime.json') if (capture/'runtime.json').exists() else {}
    if type(requested) is not bool or runtime.get('cuda_resource_observation_enabled',False) is not requested:
        raise ValueError('Prepared runtime resource observation setting mismatch')
    from portable_cuda_memory_observation import summarize as memory_summary
    memory=memory_summary(rows)
    for stage in ('prepared_child_verify_package','prepared_child_ownership','shared_gpu_execute'):
        if [r['state'] for r in rows if r['stage']==stage]!=['entered','returned']:
            raise ValueError('Prepared child execution journal incomplete')
    limits=[r.get('limits') for r in rows if r['stage']=='prepared_child_job' and r['state']=='verified']
    if (len(limits)!=1 or limits[0].get('job_memory_limit_bytes')!=2147483648
        or type(limits[0].get('job_limit_flags')) is not int or not limits[0]['job_limit_flags']&0x2000
        or any(r['state']=='raised' for r in rows)):
        raise ValueError('Prepared live Job limit journal incomplete')
    contained,pid=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
    if not contained or not verify_cuda_trace(rows,pid=pid):raise ValueError('Prepared GPU Job/native trace not verified')
    started=cli.load(capture/'prepared-child-started.json')
    if (type(started.get('pid')) is not int or started['pid']!=pid or started.get('package_id')!=m['package_id']
        or started.get('claim_sha256')!=claim_sha256 or started.get('calculation_verified') is not False):
        raise ValueError('Prepared GPU child ownership marker mismatch')
    if (capture/'prepared-child-failure.json').exists():raise ValueError('Prepared child failure must remain failed')
    dispatch=cli.load(capture/'dispatch.json');e=cli.load(capture/'evidence.json')
    expected=dict(schema=RUN_SCHEMA,protocol=claim['protocol'],package_id=m['package_id'],claim_sha256=claim_sha256,
        gpu_execution_completed=True,calculation_verified=False,independent_post_audit_required=True,
        input_sha256=e['input_sha256'],output_sha256=e['output_sha256'])
    if not same(dispatch,expected) or e.get('backend')!='cuda' or e.get('gpu_execution_verified') is not True:
        raise ValueError('Prepared dispatch/evidence mismatch')
    if (e['input_sha256']!=a['binding']['input_sha256'] or e['transport'].get('command_status')!='completed'
        or type(e['transport'].get('cases')) is not int or e['transport']['cases']!=len(m['golden']['entries'])):
        raise ValueError('Prepared transport input/count mismatch')
    observation=cli.load(capture/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
    wait=facts.get('wait_completed_unix_ns');after=observation['after']['observed_unix_ns']
    if not same(observation.get('comparison'),comparison) or type(wait) is not int or not 0<=after-wait<=30_000_000_000:
        raise ValueError('Prepared immediate observation not verified')
    preserved=cli.environment_preserved(capture,facts)
    return a,dict(calculation_verified=False,passed=False,comparison_error=None,
        transport_core_verified=True,containment_verified=True,preservation_verified=preserved,
        transport_verified=preserved,process_preservation_verified=not comparison['missing_existing_processes'],
        phase=summarize(capture/'phases.jsonl'),audit_gpu_calls=0,gpu_retries=0,
        resource_observation=dict(requested=requested,recorded=memory['memory_observations_present'],complete=memory['memory_observation_complete']))


def generation(cli,m,capture,rows):
    """Same paired artifact/reflection audit as legacy captures, mandatory hit."""
    runtime=cli.load(capture/'runtime.json');receipt=cli.load(capture/'generation-cache.json')
    if (runtime.get('generation_cache_enabled') is not True or runtime.get('generation_cache_required') is not True
        or runtime.get('cuda_artifact_kind')!='cubin' or receipt.get('hit') is not True
        or type(receipt.get('compiler_invocations')) is not int or receipt['compiler_invocations']!=0):
        raise ValueError('Prepared execution requires a paired generation hit and no compiler')
    from portable_generation_cache import audit_receipt
    result=audit_receipt(receipt,m['golden']['source_sha256'],
        {t:capture/('generated.'+suffix) for t,suffix in (('cuda','cu'),('metal','metal'))})
    if any(r['stage']=='slang_compiler' for r in rows):raise ValueError('Prepared execution invoked Slang')
    if [r.get('receipt') for r in rows if r['stage']=='slang_generation_cache' and r['state']=='verified']!=[receipt]:
        raise ValueError('Prepared paired generation journal mismatch')
    return result


def compare_group(cli,capture,claim_sha256,indices):
    """Call the original whole-output comparator with only its link provider adapted.

    The original linked audit reopens mutable producer files. This protocol
    instead verifies the same receipt/image/source through the authenticated
    frozen Handoff. All normalization, raw hashes and native comparisons remain
    the original comparator. No live-parent oracle or cached native result.
    """
    if not _COMPARISON.acquire(blocking=False):raise RuntimeError('One prepared comparison per process')
    try:
        with cli.forbid_gpu():
            m=cli.verify_package(cli.ROOT)
            if cli.is_development(m) or cli.compiler_only(m):raise ValueError('Prepared audit requires sealed battle')
            selected=selection(len(m['golden']['entries']),indices)
            if indices is None:raise ValueError('Explicit partial comparison indices required')
            capture=Path(capture).resolve();a,audit=envelope(cli,m,capture,claim_sha256)
            if current_pid()==cli.load(capture/'prepared-child-started.json')['pid']:
                raise ValueError('Fresh independent CPU process required')
            names={r['path'] for r in cli.load(capture/'artifacts.json')['files']}
            names.update(('artifacts.json','run.json','command.json','execution.json','runtime.json','evidence.json','phases.jsonl','job.json',
                'observation.json','prepared-child-started.json','dispatch.json','input.bin','readback.bin',
                'generated.cu','generated.metal','compiled.cubin','generation-cache.json',
                'generated.cu.reflection.json','generated.metal.reflection.json'))
            cli.check_records(capture,cli.load(capture/'artifacts.json')['files'])
            anchors=cli.file_records(capture,names)
            rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
            with Handoff(cli,a['snapshot'],a['snapshot_sha256'],certificate_sha256=a['certificate_sha256'],
                    expected_binding=a['binding'],expected_suite=m['suite'],expected_golden=m['golden'],
                    consumer_package_id=m['package_id'],header_materials=a.get('header_materials')) as handoff:
                packed,_=handoff.read_input()
                if (capture/'input.bin').read_bytes()!=packed:raise ValueError('Prepared audit input differs from frozen bytes')
                image,receipt=handoff.image_for_source((capture/'generated.cu').read_bytes())
                if (capture/'compiled.cubin').read_bytes()!=image:raise ValueError('Prepared audit CUBIN differs from frozen bytes')
                e=cli.load(capture/'evidence.json')
                if not same(e['transport'].get('compile_artifact'),receipt):raise ValueError('Prepared compile receipt differs from frozen bytes')
                generation(cli,m,capture,rows)
                calls=[]
                def linked(manifest,path,value):
                    if not same(manifest,m) or Path(path).resolve()!=capture or not same(value,receipt):
                        raise ValueError('Prepared linked comparator arguments changed')
                    calls.append('linked')
                def generated(manifest,path):
                    if not same(manifest,m) or Path(path).resolve()!=capture:raise ValueError('Prepared generation comparator arguments changed')
                    calls.append('generation')
                    return generation(cli,m,capture,rows)
                # The existing CLI also scopes adapters this way for grouped
                # comparison. Restore both callbacks on every exception.
                with patch.dict(cli.compare_readback.__globals__,audit_saved_linked_artifact=linked,audit_generation_capture=generated):
                    result=cli.compare_readback(m,capture,case_indices=selected)
                if calls!=['generation','linked']:raise ValueError('Prepared comparison did not verify both artifact boundaries exactly once')
            if (result.get('calculation_verified') is not False or result.get('comparison_subset_verified') is not True
                or result.get('mismatches')!=[] or result.get('case_indices')!=selected or 'parent_oracles' in result):
                raise ValueError('Prepared partial native comparison failed')
            cli.check_records(capture,anchors)
            if not same(cli.verify_package(cli.ROOT),m):raise ValueError('Prepared audit source changed')
            after,after_audit=envelope(cli,m,capture,claim_sha256)
            if not same(after,a) or not same(after_audit,audit):raise ValueError('Prepared audit ownership/envelope changed')
            return dict(package_id=m['package_id'],audit=audit,comparison=result,
                child_pid=current_pid(),live_parent_receipt_present=False)
    finally:_COMPARISON.release()
