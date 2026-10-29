"""Bounded CPU-only reread of the successful current CUDA capture and claims."""
import importlib.util,json,os,time
from pathlib import Path
from types import SimpleNamespace

MODE='partitioned-current-saved-envelope-v1'


def inspect_current(cli,source,capture,peer_raw):
    from portable_partitioned_cuda_origin import gpu_forbidden
    from portable_partitioned_cuda_owner import manifest,prepared,ledger,CLAIM
    from portable_partitioned_cuda_trace import verify
    from portable_partitioned_addresses import check_source,view_file,WORDS
    from portable_partitioned_transport import plan
    from portable_linked_artifact import valid_marker,read_verified
    from portable_partitioned_witness import bind_summary
    from windows_validation_observer import compare_snapshots
    source=Path(source).resolve();capture=Path(capture).resolve()
    if source!=Path(cli.ROOT).resolve():raise ValueError('Original source CLI required')
    with gpu_forbidden(cli):
        m,_=manifest(cli);check_source(source,cli.SUITES[m['suite']]['source'],WORDS)
        artifact_file=capture/'artifacts.json';artifact_records=cli.load(artifact_file)['files']
        anchors=cli.file_records(capture,['artifacts.json']);cli.check_records(capture,artifact_records)
        request=cli.load(capture/'run.json');result=cli.load(capture/'result.json');facts=cli.load(capture/'execution.json')
        if (request.get('mode')!=m['partitioned_cuda_execution']['schema'] or request.get('stage')!='gpu'
            or request.get('package_id')!=m['package_id'] or result.get('gpu_execution_verified') is not True
            or result.get('stage_protocol_verified') is not True or result.get('passed') is not True
            or facts.get('passed') is not True or facts.get('timed_out') is not False
            or facts.get('child_exit_code')!=0 or facts.get('final_child_exit_code')!=0
            or facts.get('below_normal_priority') is not True
            or any(facts.get(k) is not None for k in ('error','cleanup_error','observation_error'))):
            raise ValueError('Successful terminal bounded CUDA stage required')
        prepared_root=Path(request['prepared']);context,state=prepared(cli,m,prepared_root,capture)
        claim=dict(package_id=m['package_id'],prepared=str(prepared_root.resolve()),capture=str(capture),nonce=context['nonce'])
        claim_paths=[source/CLAIM,ledger(cli,state)]
        claims=[dict(path=str(p),sha256=cli.sha(p.read_bytes()),bytes=p.stat().st_size) for p in claim_paths]
        if any(cli.load(p)!=claim for p in claim_paths):raise ValueError('Original CUDA single-use claims changed')
        rows=[json.loads(x) for x in (capture/'phases.jsonl').read_bytes().splitlines()]
        contained,pid=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
        evidence=cli.load(capture/'evidence.json');layout=cli.load(capture/'readback.bin.batches/plan.json')
        packed=(prepared_root/'input.bin').read_bytes()
        if (not contained or evidence.get('backend')!='cuda' or evidence.get('source_sha256')!=m['golden']['source_sha256']
            or evidence.get('input_sha256')!=m['golden']['input_sha256'] or cli.sha(packed)!=m['golden']['input_sha256']
            or cli.transport_input_receipt(m,packed,context['input']['input_words'])!=context['input']
            or layout!=plan(packed,context['input']['input_words'],WORDS,16,runtime_stride=143048)
            or evidence.get('plan')!=layout or not verify(rows,layout,[r['transport'] for r in evidence['dispatches']],pid=pid,require_arguments=True)):
            raise ValueError('Original CUDA input, sequence arguments, source or Job differs')
        markers=[r['receipt'] for r in rows if valid_marker(r)]
        if markers!=[state['linked_receipt']]:raise ValueError('Actually loaded artifact differs from prepared CUBIN')
        image,_=read_verified(state['linked_receipt'],capture/'generated.cu',capture/'compiled.cubin')
        generation=cli.load(prepared_root/'generation.json')
        if generation.get('generated_normalized')!=m['golden']['generated_normalized']:
            raise ValueError('Prepared generated code differs from sealed source')
        adapter=cli.open_suite(m)
        for backend,suffix in (('cuda','cu'),('metal','metal')):
            raw=(capture/('generated.'+suffix)).read_bytes();record=generation['generation']['artifacts'][backend]
            if (cli.sha(raw)!=record['sha256'] or len(raw)!=record['bytes']
                or cli.sha(raw)!=evidence['generated_sha256'][backend]
                or adapter.cross.normalized(raw)!=m['golden']['generated_normalized'][backend]):
                raise ValueError('Actual paired generation differs from prepared/dispatch source')
        view=view_file(capture/'readback.bin',layout,m['golden']['entries']);view['output_bytes']=layout['output_bytes']
        peer=bind_summary(cli,peer_raw,m,view)
        if (evidence.get('output_sha256')!=view['raw_joined_output_sha256'] or evidence.get('address_view')!={k:v for k,v in view.items() if k!='output_bytes'}):
            raise ValueError('Dispatch raw/address-view evidence differs from actual saved bytes')
        observation=cli.load(capture/'observation.json');comparison=compare_snapshots(observation['before'],observation['after'])
        if observation.get('comparison')!=comparison or comparison['missing_existing_processes']:
            raise ValueError('Original process preservation unverified')
        preservation=cli.environment_preserved(capture,facts,'cuda')
        if result.get('preservation_verified') is not preservation:raise ValueError('Original preservation claim differs')
        cli.check_records(capture,anchors);cli.check_records(capture,artifact_records)
        if (claims!=[dict(path=str(p),sha256=cli.sha(p.read_bytes()),bytes=p.stat().st_size) for p in claim_paths]
            or cli.verify_package(source)!=m):raise ValueError('Original CUDA source, claims or output changed during reread')
        return dict(schema=MODE,source_package_id=m['package_id'],input_count=peer['input_count'],native_reference_cases=peer['native_reference_cases'],
            input_sha256=m['golden']['input_sha256'],raw_output_sha256=view['raw_joined_output_sha256'],logical_output_sha256=view['logical_view_sha256'],
            output_bytes=layout['output_bytes'],cubin_sha256=cli.sha(image),original_capture_observed=True,
            original_claims_modified=False,original_containment_verified=True,original_process_preserved=True,
            original_environment_preservation_verified=preservation,original_sequence_arguments_verified=True,
            launch_calls=len(layout['batches']),readback_cases=layout['input_count'],paired_generation_verified=True,
            fresh_native_calls=0,gpu_calls=0,compiler_calls=0,calculation_verified=False,
            pending_native_witness_join=True,full_goal_complete=False,public_gpu_admitted=False)


def child(cli,capture):
    from portable_phase_audit import Journal
    from portable_partitioned_cuda_origin import gpu_forbidden
    from portable_partitioned_witness import bind_current_source
    deadline=time.monotonic()+60
    while not (capture/'start.json').exists():
        if time.monotonic()>deadline:raise RuntimeError('Saved CUDA audit Job gate not released')
        time.sleep(.02)
    j=Journal(capture/'phases.jsonl');request=cli.load(capture/'run.json');m=cli.verify_package(cli.ROOT)
    if request.get('mode')!=MODE or request.get('package_id')!=m['package_id']:raise ValueError('Unknown saved envelope request')
    root=Path(request['source_package']);source_m=cli.load(root/'gpu-package.json')
    if cli.package_id(source_m)!=source_m['package_id']:raise ValueError('Original package identity differs')
    cli.check_records(root,source_m['files']);bind_current_source(cli,m,root,source_m)
    with gpu_forbidden(cli):
        spec=importlib.util.spec_from_file_location('saved_cuda_original_cli',root/'scripts/nikke_gpu.py')
        c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
        report=j.invoke('current_saved_cuda_envelope',inspect_current,SimpleNamespace(**vars(c)),root,
            Path(request['source_capture']),(cli.ROOT/'tests/fixtures/resident-current-cuda-v2-summary.json').read_bytes())
    cli.write(capture/'envelope.json',report)


def run(cli,source_package,source_capture,capture,workspace,timeout=180):
    from portable_staged_preflight import outside,exclusive
    if os.name!='nt' or type(timeout) is not int or not 1<=timeout<=180:raise ValueError('Windows saved CPU audit with at most 180 seconds required')
    m=cli.verify_package(cli.ROOT);capture=outside(capture,[cli.ROOT,Path(source_package),Path(source_capture)])
    capture.mkdir(parents=True,exist_ok=False)
    exclusive(capture/'run.json',dict(mode=MODE,package_id=m['package_id'],source_package=str(Path(source_package).resolve()),source_capture=str(Path(source_capture).resolve())))
    os.environ['NIKKE_VALIDATION_JOB_MEMORY_MB']='2048'
    try:
        facts=cli.run_job(capture,'cuda',timeout,original_workspace=str(Path(workspace).resolve()))
        rows=[json.loads(x) for x in (capture/'phases.jsonl').read_bytes().splitlines()] if (capture/'phases.jsonl').exists() else []
        contained,_=cli.job_contained(capture,rows,memory_limit_bytes=2147483648)
        report=cli.load(capture/'envelope.json') if (capture/'envelope.json').is_file() else None
        result=dict(schema=MODE,package_id=m['package_id'],passed=bool(facts.get('passed') and contained and report),
            containment_verified=contained,preservation_verified=cli.environment_preserved(capture,facts,'cuda'),
            original_capture_observed=bool(report and report.get('original_capture_observed') is True),
            gpu_calls=0,compiler_calls=0,native_calls=0,calculation_verified=False,full_goal_complete=False,public_gpu_admitted=False)
        exclusive(capture/'result.json',result);return result
    finally:cli.collect(capture,capture/'artifacts.json')
