"""One new execution owner after an audited, pre-device configuration failure.

Reuses complete fingerprint evidence, not native calculation values. The old
claims stay consumed; a separate stable ledger makes recovery single-use too.
"""
import argparse,json,os,sys,uuid
from pathlib import Path

FIELDS=('source_package','source_capture','origin_package','origin_capture','gpu_capture',
        'linked_package','linked_capture','slang_root','generation_cache')


def canonical(cli,value):return cli.sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())


def settings(request):return {k:str(Path(request[k]).resolve()) for k in ('slang_root','generation_cache')}


def check_environment(cli,request):
    expected=settings(request)
    if os.environ.get('NIKKE_SLANG_GENERATION_REQUIRED')!='1' or any(os.environ.get(e)!=expected[k] for k,e in
        (('slang_root','NIKKE_SLANG_ROOT'),('generation_cache','NIKKE_SLANG_GENERATION_CACHE'))):raise ValueError('Recovery generation environment differs from the fixed request')
    packet=cli.module(cli.ROOT/'scripts/run-gpu-packet.py')
    packet.required_generation_environment(os.environ)
    return expected


def origin_terminal(cli,root,manifest,request):
    """Reuse the existing Job timeline and process observer, without service guesses."""
    from windows_validation_observer import compare_snapshots
    outer=Path(root).resolve();plan=cli.load(outer/'recipe.json');facts=cli.load(outer/'execution.json')
    packet=cli.module(cli.ROOT/'scripts/run-gpu-packet.py')
    expected_request=dict(source_package=request['source_package'],source_capture=request['source_capture'],expected_package_id=request['base_package_id'])
    expected=packet.recipe(manifest['package_id'],packet.ORIGIN_STAGE,'cuda',outer,plan['original_workspace'],plan['timeout_seconds'],expected_request)
    proof=cli.load(outer/'proof/result.json');stage=cli.load(outer/'stage-result.json')
    if (plan!=expected or not packet.verified_origin(proof,expected_request)
        or stage.get('package_id')!=manifest['package_id'] or stage.get('stage')!=packet.ORIGIN_STAGE
        or stage.get('stage_verified') is not True or stage.get('proof_result')!=proof or stage.get('calculation_verified') is not False
        or facts.get('passed') is not True or facts.get('timed_out') is not False
        or type(facts.get('child_exit_code')) is not int or facts['child_exit_code']!=0
        or type(facts.get('final_child_exit_code')) is not int or facts['final_child_exit_code']!=0
        or facts.get('below_normal_priority') is not True
        or type(facts.get('timeout_seconds')) not in (int,float) or not 0<facts['timeout_seconds']<=plan['timeout_seconds']
        or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error'))):raise ValueError('Origin audit lacks its complete bounded terminal')
    job=cli.load(outer/'job.json')['records']
    if len(job)!=1:raise ValueError('Origin audit Job count changed')
    rows=[json.loads(line) for line in (outer/'preparation.jsonl').read_text().splitlines()]
    if any(r.get('pid') not in (job[0]['child_pid'],job[0]['wrapper_pid']) for r in rows):raise ValueError('Unknown origin preparation process')
    if not cli.job_contained(outer,[r for r in rows if r.get('pid')==job[0]['child_pid']],memory_limit_bytes=2147483648)[0]:raise ValueError('Origin audit Job is not verified')
    observation=cli.load(outer/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
    if observation['comparison']!=comparison or comparison['missing_existing_processes']:raise ValueError('Origin audit process preservation is not verified')
    return proof


def origin_evidence(cli,m,request):
    from portable_gpu_recovery_package import validate_lineage
    from portable_staged_origin import evidence_roots,inventory,validate_admission
    from portable_staged_failure import source_control_flow,validate_trace
    base=Path(request['source_package']).resolve();outer=Path(request['source_capture']).resolve()
    auditor=Path(request['origin_package']).resolve();audit=Path(request['origin_capture']).resolve();proof=audit/'proof'
    original=validate_lineage(cli,m,base);meta=m['controller_gpu_recovery']
    inspector=cli.load(auditor/'gpu-package.json')
    if inspector.get('package_id')!=meta['auditor_package_id'] or cli.package_id(inspector)!=meta['auditor_package_id'] or cli.sha((auditor/'gpu-package.json').read_bytes())!=meta['auditor_manifest_sha256']:raise ValueError('Origin auditor source owner changed')
    cli.check_records(auditor,inspector['files'])
    req=dict(request,base_package_id=original['package_id']);report=origin_terminal(cli,audit,inspector,req)
    admission=cli.load(proof/'admission.json');closure=cli.load(proof/'origin-inventory.json')
    if (closure.get('schema')!='staged-origin-inventory-v1' or closure.get('package_id')!=original['package_id']
        or closure.get('source_package')!=str(base) or closure.get('source_capture')!=str(outer)
        or closure.get('admission_sha256')!=cli.sha((proof/'admission.json').read_bytes())
        or report.get('inventory_sha256')!=cli.sha((proof/'origin-inventory.json').read_bytes())
        or admission!=cli.load(outer/'proof/staged-preflight.json')):raise ValueError('Origin receipt/inventory anchors changed')
    validate_admission(cli,base,outer,admission,original['package_id'])
    roots=evidence_roots(cli,base,outer,admission)
    if inventory(cli,roots)!=closure['evidence']:raise ValueError('Original evidence no longer matches the complete audited inventory')
    failure=cli.load(proof/'failure-audit.json');packet=cli.module(cli.ROOT/'scripts/run-gpu-packet.py')
    if not packet.verified_failure(failure,dict(expected_package_id=original['package_id'])):raise ValueError('Unknown original failure')
    source_control_flow(cli,base)
    validate_trace([json.loads(line) for line in (outer/'proof/phases.jsonl').read_text().splitlines()])
    if any((outer/'proof'/n).exists() or (outer/'proof'/n).is_symlink() for n in ('readback.bin','readback.bin.partial','result.json','evidence.json','compiled.cubin')):raise ValueError('Original failure has device/result artifacts')
    for directory,key in ((base,'owner_artifacts'),(outer,'failure_artifacts'),(Path(admission['transaction']),'transaction_artifacts')):cli.check_records(directory,failure[key])
    if report.get('input_count')!=admission['input_count'] or report.get('native_cases')!=admission['native_cases']:raise ValueError('Origin audit counts changed')
    # Record the entire small audit capture, independently of its saved report.
    capture_inventory=inventory(cli,[audit])
    summary=dict(source_package=str(base),source_capture=str(outer),origin_package=str(auditor),origin_capture=str(audit),
        base_package_id=original['package_id'],auditor_package_id=inspector['package_id'],
        inventory_sha256=report['inventory_sha256'],audit_capture_sha256=canonical(cli,capture_inventory),
        admission_sha256=closure['admission_sha256'])
    return original,admission,summary,roots


def ledger_path(cli,request,base_package_id):
    outer=Path(request['source_capture']).resolve();saved=cli.load(outer/'proof/staged-preflight.json')
    claim=Path(saved['transaction'])/'gpu-execution-claimed.json'
    key=canonical(cli,dict(package_id=base_package_id,claim_sha256=cli.sha(claim.read_bytes())))
    return outer.parent/'.gpu-recovery-claims'/(key+'.json')


def ledger_value(m,c):
    return dict(schema='staged-gpu-recovery-claim-v1',package_id=m['package_id'],nonce=c['nonce'],
        transaction=c['transaction'],gpu_capture=c['gpu_capture'],host=c['host'],input=c['input'],
        native_indices=c['native_indices'],recovery_parent=c['recovery_parent'])


def begin(cli,capture,request):
    from portable_staged_preflight import SCHEMA,host,outside,exclusive,static_input
    from portable_phase_audit import Journal
    m=cli.verify_package(cli.ROOT)
    if 'controller_gpu_recovery' not in m:raise ValueError('A reviewed recovery capsule is required')
    request={k:str(Path(request[k]).resolve()) for k in FIELDS};check_environment(cli,request)
    capture=Path(capture).resolve();gpu=Path(request['gpu_capture']).resolve()
    outside(capture,[cli.ROOT,*[Path(request[k]) for k in ('source_package','source_capture','origin_package','origin_capture','linked_package','linked_capture','slang_root','generation_cache')]])
    outside(gpu,[cli.ROOT,capture,*[Path(request[k]) for k in ('source_package','source_capture','origin_package','origin_capture','linked_package','linked_capture','slang_root','generation_cache')]])
    claim=cli.ROOT/'gpu-claimed-cuda.json';ledger=ledger_path(cli,request,m['controller_gpu_recovery']['base_package_id'])
    if capture.exists() or gpu.exists() or claim.exists() or ledger.exists():raise FileExistsError('Recovery owner, capture or origin is already consumed')
    capture.mkdir(parents=True,exist_ok=False);j=Journal(capture/'phases.jsonl')
    try:
        # Original four generation consumers and all GPU bytes are unchanged.
        # This method has its own file-only/no-library/no-compiler guard; an
        # outer forbid_gpu would mask its intentionally cached build function.
        _,generation=j.invoke('recovery_required_generation',cli.required_generation_snapshot,m)
        exclusive(capture/'generation-preflight.json',generation)
        with cli.forbid_gpu():
            original,parent,summary,roots=j.invoke('recovery_origin',origin_evidence,cli,m,request)
            _,entries,data,input_receipt=j.invoke('recovery_static_input',static_input,cli,m)
            old_tx=Path(parent['transaction']);old_context=cli.load(old_tx/'transaction.json')
            indices=[i for i,(_,_,domain) in enumerate(entries) if domain is not None]
            if (data!=(old_tx/'input.bin').read_bytes() or indices!=old_context['native_indices']
                or input_receipt!=dict(parent['input'],package_id=m['package_id'])):raise ValueError('Recovery changed original input or native membership')
            linked=j.invoke('recovery_linked_cubin',cli.saved_linked_admission,m,dict(package=request['linked_package'],capture=request['linked_capture']))
        exclusive(capture/'linked-preflight.json',linked)
        # The original failed attempt selected this same artifact producer.
        old_link=cli.load(Path(request['source_capture'])/'proof/linked-artifact-request.json')
        if old_link!=dict(package=request['linked_package'],capture=request['linked_capture']):raise ValueError('Recovery substituted a different linked artifact')
        outside(ledger,[cli.ROOT,capture,gpu,*roots,Path(request['origin_capture']),Path(request['origin_package'])])
        c=dict(schema=SCHEMA,package_id=m['package_id'],manifest_sha256=cli.sha((cli.ROOT/'gpu-package.json').read_bytes()),
            package_root=str(cli.ROOT.resolve()),transaction=str(capture),nonce=uuid.uuid4().hex,backend='cuda',gpu_capture=str(gpu),
            host=host(cli),group_size=1,case_groups=[],native_indices=indices,input=input_receipt,
            recovery_parent=dict(request=request,origin=summary,ledger=str(ledger),linked_sha256=canonical(cli,linked),generation_key=generation['generation']['key']))
        # Never alter either old claim. A stable sibling ledger prevents the
        # same failed origin being assigned to two different new packages.
        ledger.parent.mkdir(parents=True,exist_ok=True);exclusive(ledger,ledger_value(m,c))
        exclusive(claim,dict(package_id=m['package_id'],capture=str(gpu),transaction=str(capture),transaction_nonce=c['nonce']))
        cli.publish_transport_input(m,capture,data,input_receipt['input_words']);exclusive(capture/'transaction.json',c)
        j.emit('recovery_ready','returned')
        result=dict(mode='staged-preflight-recovery-only',package_id=m['package_id'],transaction_ready=True,
            input_count=parent['input_count'],native_cases=parent['native_cases'],native_oracles_run=0,native_values_reused=False,
            original_claims_modified=False,original_failure_promoted=False,calculation_verified=False,gpu_calls=0,driver_load_calls=0)
        exclusive(capture/'result.json',result);return result
    except BaseException as error:
        exclusive(capture/'failure.json',dict(error=type(error).__name__+': '+str(error),gpu_calls=0));raise
    finally:cli.collect(capture,capture/'artifacts.json')


def admit_context(cli,m,c):
    from portable_staged_preflight import SCHEMA,terminal_cpu_stage
    request=c['recovery_parent']['request'];check_environment(cli,request)
    tx=Path(c['transaction']);cli.check_records(tx,cli.load(tx/'artifacts.json')['files'])
    stage=terminal_cpu_stage(cli,tx,m,'preflight-recover')
    original,parent,summary,_=origin_evidence(cli,m,request)
    ledger=ledger_path(cli,request,original['package_id'])
    if (c['recovery_parent']['origin']!=summary or c['recovery_parent']['ledger']!=str(ledger)
        or cli.load(ledger)!=ledger_value(m,c) or c['gpu_capture']!=request['gpu_capture']
        or c['native_indices']!=cli.load(Path(parent['transaction'])/'transaction.json')['native_indices']
        or c['input']!=dict(parent['input'],package_id=m['package_id'])):raise ValueError('Recovery origin, ledger or input identity changed')
    receipt=cli.transport_input_receipt(m,(tx/'input.bin').read_bytes(),c['input']['input_words'])
    if receipt!=c['input']:raise ValueError('Recovery prepared input changed')
    linked=cli.load(tx/'linked-preflight.json');generation=cli.load(tx/'generation-preflight.json')
    if canonical(cli,linked)!=c['recovery_parent']['linked_sha256'] or generation['generation']['key']!=c['recovery_parent']['generation_key']:raise ValueError('Recovery artifact or generation receipt changed')
    gpu=Path(c['gpu_capture'])
    if gpu.exists():
        run=cli.load(gpu/'run.json')
        if (run.get('package_id')!=m['package_id'] or run.get('mode')!='staged-gpu' or run.get('backend')!='cuda'
            or run.get('input_protocol')!='staged-prepared-v1'
            or cli.load(gpu/'linked-artifact-request.json')!=dict(package=request['linked_package'],capture=request['linked_capture'])):raise ValueError('Recovery execution mode or linked request changed')
    return dict(schema=SCHEMA,package_id=m['package_id'],transaction=str(tx),transaction_nonce=c['nonce'],
        transaction_sha256=cli.sha((tx/'transaction.json').read_bytes()),host=c['host'],input=c['input'],
        native_cases=parent['native_cases'],input_count=parent['input_count'],groups=parent['groups'],fresh_child_pids=parent['fresh_child_pids'],
        stage_envelopes=parent['stage_envelopes']+[dict(capture=str(tx),**stage)],group_anchors=parent['group_anchors'],
        continuation_parent=parent.get('continuation_parent'),original_timeout=parent.get('original_timeout'),
        recovery_origin=summary,original_failure_promoted=False,native_values_reused=False,native_oracles_run=0,
        all_native_preflight_verified=True,calculation_verified=False,gpu_calls=0)


def dispatch(cli,original_main,argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]=='preflight-recover':
        p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--capture',type=Path,required=True)
        for name in FIELDS:p.add_argument('--'+name.replace('_','-'),required=True)
        a=p.parse_args(args);result=begin(cli,a.capture,{k:getattr(a,k) for k in FIELDS})
        print(json.dumps(result,indent=2));return result
    if args and args[0] in ('run','preflight-begin','preflight-plan','preflight-resume','preflight-native-group','preflight-test-group'):
        raise ValueError('Recovery capsule only admits its bound recovery transaction')
    if args and args[0]=='_child':
        p=argparse.ArgumentParser(add_help=False);p.add_argument('--capture',type=Path,required=True);a,_=p.parse_known_args(args[1:])
        run=cli.load(a.capture/'run.json')
        if run.get('mode')!='staged-gpu' or run.get('input_protocol')!='staged-prepared-v1':raise ValueError('Recovery child requires its staged prepared input')
    return original_main(argv)
