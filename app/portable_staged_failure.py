"""Read-only diagnosis of one narrowly identified pre-generation failure.

This never makes an execution claim reusable. Native admission, linked CUBIN
and any future recovery protocol still require their own complete checks.
"""
import json,sys
from pathlib import Path
from unittest.mock import patch

PATTERN=[('cuda_linked_origin','verified'),('shared_gpu_execute','entered'),('slang_build','entered'),
    ('slang_generation_identity','entered'),('slang_generation_identity','raised'),('slang_build','raised'),('shared_gpu_execute','raised')]


def validate_trace(rows):
    if type(rows) is not list or any(type(r) is not dict for r in rows):raise ValueError('Invalid failure trace rows')
    if [(r.get('stage'),r.get('state')) for r in rows]!=PATTERN:
        raise ValueError('Unknown failure trace; a missing CUDA marker alone is insufficient')
    if len({r.get('pid') for r in rows})!=1 or type(rows[0].get('pid')) is not int or rows[0]['pid']<=0:
        raise ValueError('Failure trace child identity changed')
    if any(r.get('exception') is not None for r in rows[:-3]) or any(r.get('exception')!='ValueError' for r in rows[-3:]):raise ValueError('Unknown generation exception')
    return rows[0]['pid']


def source_control_flow(cli,root):
    from portable_continuation_package import functions
    # Strict function identity: no textual exclusions or new generated-code
    # normalization. This proves the observed build failure precedes dispatch
    # under the same reviewed source, rather than inferring from absent logs.
    for name,selected in [('app/portable_backend.py',('execute',)),
        ('app/portable_slang_generation.py',('build',)),('app/portable_generation_cache.py',('identity',)),
        ('scripts/nikke_gpu.py',('child','saved_linked_provider')),
        ('research/portable_phase_audit.py',('observe','observe_generation'))]:
        old=functions((root/name).read_text(encoding='utf-8'));current=functions((cli.ROOT/name).read_text(encoding='utf-8'))
        if any(not old.get(n) or old[n]!=current.get(n) for n in selected):
            raise ValueError('Failure control flow differs from reviewed source: '+name)


def terminal(facts,limit,*,inner):
    if (facts.get('passed') is not False or type(facts.get('final_child_exit_code')) is not int or facts['final_child_exit_code']!=1
        or type(facts.get('timeout_seconds')) not in (int,float) or not 0<facts['timeout_seconds']<=limit
        or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error'))
        or facts.get('below_normal_priority') is not True):raise ValueError('Failure lacks a clean bounded terminal')
    if inner and (facts.get('timed_out') is not False or type(facts.get('child_exit_code')) is not int or facts['child_exit_code']!=1):
        raise ValueError('Generation child was interrupted or did not report failure')


def check(cli,package_root,capture,output,expected_package_id):
    from portable_continuation_package import owner_snapshot
    from portable_staged_preflight import exclusive,outside
    from windows_validation_observer import compare_snapshots
    root=Path(package_root).resolve();outer=Path(capture).resolve();proof=outer/'proof'
    transaction=Path(cli.load(proof/'staged-preflight.json')['transaction']).resolve()
    output=outside(output,[root,outer,transaction]);output.parent.mkdir(parents=True,exist_ok=True);exclusive(output,{})
    report=dict(schema='staged-failure-check-v1',mode='saved-staged-failure-audit',passed=False,execution_permitted=False,
        native_admission_revalidated=False,linked_artifact_revalidated=False,host_revalidated=False,calculation_verified=False,
        gpu_calls=0,compiler_calls=0,native_calls=0,claims_modified=False,full_goal_complete=False)
    try:
        header=cli.load(root/'gpu-package.json')
        if header.get('package_id')!=expected_package_id:raise ValueError('Failure package differs from requested immutable owner')
        info=owner_snapshot(cli,root);m=info['manifest']
        if m.get('purpose')!='sealed' or m['package_id']!=expected_package_id:raise ValueError('Sealed original package required')
        source_control_flow(cli,root)
        names=['recipe.json','execution.json','job.json','observation.json','preparation.jsonl',
            *['proof/'+n for n in ('run.json','runtime.json','execution.json','job.json','observation.json','staged-preflight.json','input-preflight.json','input.bin','phases.jsonl','stderr.log')]]
        anchors=cli.file_records(outer,names)
        run=cli.load(proof/'run.json');runtime=cli.load(proof/'runtime.json');inner=cli.load(proof/'execution.json');facts=cli.load(outer/'execution.json');plan=cli.load(outer/'recipe.json')
        with patch.object(sys,'dont_write_bytecode',True):packet=cli.module(root/'scripts/run-gpu-packet.py')
        if plan!=packet.recipe(m['package_id'],'staged-gpu-linked','cuda',outer,plan['original_workspace'],plan['timeout_seconds'],plan['object_request']):raise ValueError('Failed wrapper recipe changed')
        if run.get('package_id')!=m['package_id'] or run.get('backend')!='cuda' or run.get('mode')!='staged-gpu' or run.get('input_protocol')!='staged-prepared-v1' or type(run.get('gpu_retry_count')) is not int or run['gpu_retry_count']!=0:raise ValueError('Unknown failed execution mode')
        terminal(inner,60,inner=True);terminal(facts,180,inner=False)
        if runtime.get('slang_root') is not None or runtime.get('generation_cache_required') is not True or runtime.get('generation_cache_enabled') is not True:raise ValueError('Failure is outside the missing explicit Slang environment case')
        forbidden=('evidence.json','result.json','readback.bin','readback.bin.partial','compiled.cubin','comparison.json','artifacts.json')
        if any((proof/n).exists() or (proof/n).is_symlink() for n in forbidden):raise ValueError('Failure already has execution/result artifacts')
        trace=(proof/'phases.jsonl').read_bytes()
        if not trace.endswith(b'\n'):raise ValueError('Failure trace is truncated')
        rows=[json.loads(line) for line in trace.splitlines()];pid=validate_trace(rows)
        contained,actual_pid=cli.job_contained(proof,rows,memory_limit_bytes=2147483648)
        if not contained or pid!=actual_pid:raise ValueError('Failed child Job/phase timeline is not verified')
        prep=[json.loads(line) for line in (outer/'preparation.jsonl').read_text().splitlines()]
        job=cli.load(outer/'job.json')['records']
        if len(job)!=1 or any(r.get('pid') not in (job[0]['child_pid'],job[0]['wrapper_pid']) for r in prep):raise ValueError('Unknown whole-stage preparation process')
        if not cli.job_contained(outer,[r for r in prep if r.get('pid')==job[0]['child_pid']],memory_limit_bytes=2147483648)[0]:raise ValueError('Failed wrapper Job/phase timeline is not verified')
        preservation=[]
        for directory in (outer,proof):
            observation=cli.load(directory/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
            if observation.get('comparison')!=comparison or comparison['missing_existing_processes']:raise ValueError('Failure process observation changed or recorded missing processes')
            preservation.append(comparison['identified_nikke_service_preservation_verified'] is True)
        stderr=(proof/'stderr.log').read_text(encoding='utf-8',errors='replace')
        if 'ValueError: Slang cache compiler identity absent' not in stderr:raise ValueError('Failure diagnostic does not identify missing compiler identity')
        admission=cli.load(proof/'staged-preflight.json');transaction=Path(admission['transaction']).resolve();tx=cli.load(transaction/'transaction.json')
        tx_anchors=cli.file_records(transaction,['transaction.json','gpu-execution-claimed.json'])
        owner_anchors=cli.file_records(root,['gpu-package.json','gpu-claimed-cuda.json','packet-stage-claimed-staged-gpu-linked-cuda.json','app/portable_backend.py','app/portable_slang_generation.py','app/portable_generation_cache.py','scripts/nikke_gpu.py','research/portable_phase_audit.py'])
        if tx.get('package_id')!=m['package_id'] or tx.get('gpu_capture')!=str(proof) or tx.get('nonce')!=admission['transaction_nonce'] or tx.get('package_root')!=str(root) or admission.get('transaction_sha256')!=cli.sha((transaction/'transaction.json').read_bytes()):raise ValueError('Failed transaction anchor changed')
        if cli.load(root/'gpu-claimed-cuda.json')!=dict(package_id=m['package_id'],capture=str(proof),transaction=str(transaction),transaction_nonce=admission['transaction_nonce']):raise ValueError('Original GPU ownership claim changed')
        wrapper_claim=cli.load(root/'packet-stage-claimed-staged-gpu-linked-cuda.json')
        if wrapper_claim.get('package_id')!=m['package_id'] or wrapper_claim.get('capture')!=str(outer):raise ValueError('Original wrapper claim changed')
        claim=cli.load(transaction/'gpu-execution-claimed.json')
        if claim!=dict(package_id=m['package_id'],nonce=admission['transaction_nonce'],capture=str(proof)):raise ValueError('Failed execution claim changed')
        receipt=cli.transport_input_receipt(m,(proof/'input.bin').read_bytes(),admission['input']['input_words'])
        if receipt!=admission['input'] or receipt!=cli.load(proof/'input-preflight.json'):raise ValueError('Failed prepared input changed')
        cli.check_records(outer,anchors)
        cli.check_records(transaction,tx_anchors);cli.check_records(root,owner_anchors)
        report.update(passed=True,package_id=m['package_id'],pre_generation_failure_verified=True,child_pid=pid,
            source_control_flow_verified=True,containment_verified=True,process_preservation_verified=True,
            environment_preservation_verified=all(preservation),prepared_input_verified=True,
            input_count=receipt['input_count'],input_sha256=receipt['input_sha256'],execution_claim_consumed=True,
            failure_artifacts=anchors,transaction_artifacts=tx_anchors,owner_artifacts=owner_anchors,
            scope='Saved failure only; original claims remain consumed. No native-admission/cache/host recertification or recovery execution is authorized.')
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error)
        raise
    finally:cli.write(output,report)
    return report
