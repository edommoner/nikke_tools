"""Immutable Metal-only validation of shared partitioned file transport.

The CUDA API is shared, but a new Windows admission after its consumed launch
failure is deliberately not enabled by this diagnostic controller.
"""
import argparse,ast,copy,hashlib,json,os,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
from types import SimpleNamespace

ADDED=('app/portable_partitioned_transport.py','app/portable_partitioned_cli.py','app/portable_partitioned_addresses.py',
       'app/portable_partitioned_native.py','tests/test_portable_partitioned_transport.py',
       'tests/test_portable_partitioned_addresses.py','tests/test_portable_partitioned_native.py',
       'app/portable_partitioned_cuda_trace.py','app/portable_partitioned_cuda_observer.py',
       'tests/test_portable_partitioned_cuda_trace.py','tests/test_portable_partitioned_cuda_observer.py',
       'app/portable_partitioned_cuda_origin.py','tests/test_portable_partitioned_cuda_origin.py')
MODE='partitioned-file-diagnostic-v1'


def patched_cli(text):
    tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    main.name='_pre_partitioned_main'
    dispatcher=ast.parse('''
def main(argv=None):
    from portable_partitioned_cli import dispatch
    return dispatch(SimpleNamespace(**globals()),_pre_partitioned_main,argv)
''').body[0]
    tree.body.insert(tree.body.index(main)+1,dispatcher)
    return ast.unparse(ast.fix_missing_locations(tree))+'\n'


def make(cli,source,output):
    from portable_continuation_package import owner_snapshot
    from portable_staged_preflight import outside
    source=Path(source).resolve();output=outside(output,[source])
    if output.exists():raise FileExistsError(output)
    info=owner_snapshot(cli,source);old=info['manifest']
    if old['suite']!='coordinate-resident-frames' or old.get('purpose')!='sealed' or old.get('partitioned_diagnostic'):raise ValueError('Original sealed complete resident-frame baseline required')
    payload={r['path']:(source/r['path']).read_bytes() for r in old['files']}
    if set(ADDED)&set(payload):raise ValueError('Partitioned helpers already exist in base')
    payload['scripts/nikke_gpu.py']=patched_cli(payload['scripts/nikke_gpu.py'].decode()).encode()
    for name in ADDED:payload[name]=(cli.ROOT/name).read_bytes()
    with tempfile.TemporaryDirectory(prefix='nikke-partitioned-packet-') as tmp:
        root=Path(tmp)
        for name,raw in payload.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        m=copy.deepcopy(old);m.pop('package_id');m['files']=cli.file_records(root,payload)
        if 'payload_projection' in m:
            # No re-projection: preserve every old selected member and omission.
            # The old owner's normal validator checks these updated counts.
            projection=m['payload_projection'];names=set(payload);omitted=set(projection['omitted'])
            if names&omitted:raise ValueError('New helpers collide with original omissions')
            projection.update(retained_files=len(names),original_files=len(names|omitted),
                original_names_sha256=cli.sha(json.dumps(sorted(names|omitted),separators=(',',':')).encode()))
        m['partitioned_diagnostic']=dict(schema=MODE,base_package_id=old['package_id'],base_manifest_sha256=cli.sha((source/'gpu-package.json').read_bytes()),
            added=list(ADDED),replaced=['scripts/nikke_gpu.py'],cuda_execution_admitted=False)
        from portable_partitioned_addresses import PROFILE,check_source
        check_source(source,info['config']['source'],info['config']['output_words'])
        m['partitioned_diagnostic']['wire_address_profile']=PROFILE
        m['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=cli.ROOT,text=True).strip()
        m['working_tree_dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=cli.ROOT,text=True).strip());m['package_id']=cli.package_id(m)
        if owner_snapshot(cli,source)!=info:raise ValueError('Original baseline changed during diagnostic packaging')
        with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('gpu-package.json',json.dumps(m,indent=2))
            for name,raw in payload.items():z.writestr(name,raw)
    return dict(package_id=m['package_id'],base_package_id=old['package_id'],files=len(payload),archive_bytes=output.stat().st_size,archive_sha256=cli.sha(output.read_bytes()),gpu_calls=0)


def run(cli,capture,backend,batch_size,timeout):
    if backend!='metal' or sys.platform!='darwin':raise ValueError('Partitioned diagnostic currently admits Metal only')
    from portable_staged_preflight import outside,exclusive
    from portable_capture_storage import space_status
    from portable_phase_audit import Journal
    m=cli.verify_package(cli.ROOT)
    if m.get('partitioned_diagnostic',{}).get('schema')!=MODE:raise ValueError('Immutable partitioned diagnostic packet required')
    if type(batch_size) is not int or not 1<=batch_size<=16 or type(timeout) is not int or not 1<=timeout<=180:raise ValueError('Bounded diagnostic batch/budget required')
    capture=outside(capture,[cli.ROOT]);capture.mkdir(parents=True,exist_ok=False);j=Journal(capture/'preparation.jsonl')
    try:
        with cli.forbid_gpu():iw=cli.open_suite(m).suite.INPUT
        count=len(m['golden']['entries']);ow=cli.SUITES[m['suite']]['output_words'];size=4+count*iw*4
        from portable_wire_layout import check_metal
        exclusive(capture/'metal-wire-preflight.json',check_metal(cli.ROOT,ow))
        needed=2*count*ow*4+2*size+4*((count+batch_size-1)//batch_size)+64*1024*1024
        storage=space_status(capture,needed);exclusive(capture/'storage.json',storage)
        if not storage['passed']:raise RuntimeError('Partitioned diagnostic lacks retained-readback storage')
        _,generation=j.invoke('partitioned_required_generation',cli.required_generation_snapshot,m)
        exclusive(capture/'generation-preflight.json',generation)
        with cli.forbid_gpu():cpu=j.invoke('partitioned_fresh_preflight',cli.cpu_preflight,m,input_capture=capture)
        exclusive(capture/'cpu.json',cpu)
        recipe=dict(mode=MODE,package_id=m['package_id'],backend='metal',batch_size=batch_size,timeout_seconds=timeout,
            input_words=iw,output_words=ow,cpu_sha256=cli.sha((capture/'cpu.json').read_bytes()),input_sha256=m['golden']['input_sha256'],
            wire_address_profile=m['partitioned_diagnostic']['wire_address_profile'])
        exclusive(capture/'run.json',recipe)
        exclusive(cli.ROOT/'partitioned-metal-claimed.json',dict(package_id=m['package_id'],capture=str(capture),recipe=recipe))
        facts=cli.run_job(capture,'metal',timeout)
        evidence=cli.load(capture/'evidence.json') if (capture/'evidence.json').is_file() else None
        result=dict(mode=MODE,package_id=m['package_id'],passed=bool(facts.get('passed') and evidence and evidence.get('logical_wire_equivalence_verified')
                and evidence.get('wire_address_profile')==m['partitioned_diagnostic']['wire_address_profile']),
            gpu_execution_verified=bool(evidence and evidence.get('gpu_execution_verified')),preflight_native_oracles=cpu['native_oracles'],
            input_count=count,calculation_verified=False,pending_independent_native_audit=True,full_goal_complete=False)
        exclusive(capture/'result.json',result);return result
    except BaseException as error:
        exclusive(capture/'failure.json',dict(error=type(error).__name__+': '+str(error)));raise
    finally:cli.collect(capture,capture/'artifacts.json')


def child(cli,capture,backend):
    from portable_phase_audit import Journal,observe,observe_generation
    import portable_backend
    import portable_partitioned_transport as partitioned
    deadline=time.monotonic()+60
    while not (capture/'start.json').is_file():
        if time.monotonic()>=deadline:raise RuntimeError('Partitioned containment gate was not released')
        time.sleep(.02)
    if backend!='metal':raise ValueError('Partitioned CUDA admission is not enabled')
    m=cli.verify_package(cli.ROOT);run=cli.load(capture/'run.json');cpu=cli.load(capture/'cpu.json')
    claim=cli.load(cli.ROOT/'partitioned-metal-claimed.json')
    if (run.get('mode')!=MODE or run.get('package_id')!=m['package_id'] or run.get('backend')!='metal'
        or claim!=dict(package_id=m['package_id'],capture=str(capture),recipe=run)
        or run.get('cpu_sha256')!=cli.sha((capture/'cpu.json').read_bytes()) or cpu.get('passed') is not True
        or cpu.get('input_count')!=len(m['golden']['entries']) or cpu.get('native_oracles')!=cli.SUITES[m['suite']]['native']
        or run.get('wire_address_profile')!=m['partitioned_diagnostic'].get('wire_address_profile')):raise ValueError('Partitioned fresh preflight or claim changed')
    packed=(capture/'input.bin').read_bytes()
    receipt=cli.transport_input_receipt(m,packed,run['input_words'])
    if receipt!=cli.load(capture/'input-preflight.json') or receipt!=cpu['transport_input']:raise ValueError('Partitioned prepared input changed')
    journal=Journal(capture/'phases.jsonl')
    with observe(portable_backend,journal),observe_generation(journal):
        _,evidence=journal.invoke('partitioned_file_execute',partitioned.execute,cli.SUITES[m['suite']]['source'],'portableEvents',
            packed,run['input_words'],run['output_words'],'metal',readback_path=capture/'readback.bin',batch_size=run['batch_size'],
            expected_input_sha256=m['golden']['input_sha256'],expected_output_sha256=m['golden']['output_sha256'],
            expected_source_sha256=m['golden']['source_sha256'],expected_generated_normalized=m['golden']['generated_normalized'],address_profile=run['wire_address_profile'])
    cli.copy_generated(capture,m['suite']);cli.write(capture/'evidence.json',evidence)


def dispatch(cli,original,argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0]=='partitioned-origin-smoke':
        p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--capture',type=Path,required=True)
        p.add_argument('--original-workspace',type=Path);p.add_argument('--timeout',type=int,default=30);a=p.parse_args(args)
        from portable_partitioned_cuda_origin import smoke as smoke_origin
        result=smoke_origin(cli,a.capture,a.original_workspace,a.timeout);print(json.dumps(result,indent=2))
        if not result['passed']:raise SystemExit(1)
        return result
    if args and args[0]=='partitioned-origin-audit':
        p=argparse.ArgumentParser();p.add_argument('command')
        for flag in ('source-package','source-capture','capture','original-workspace','slang-root','generation-cache'):p.add_argument('--'+flag,type=Path,required=True)
        p.add_argument('--timeout',type=int,default=180);a=p.parse_args(args)
        from portable_partitioned_cuda_origin import run as audit_origin
        result=audit_origin(cli,a.source_package,a.source_capture,a.capture,a.original_workspace,a.slang_root,a.generation_cache,a.timeout)
        print(json.dumps(result,indent=2))
        if not result['passed']:raise SystemExit(1)
        return result
    if args and args[0]=='partitioned-native-audit':
        p=argparse.ArgumentParser();p.add_argument('command')
        for flag in ('source-package','capture','out'):p.add_argument('--'+flag,type=Path,required=True)
        p.add_argument('--timeout',type=int,default=240);p.add_argument('--group-size',type=int,default=16);a=p.parse_args(args)
        from portable_partitioned_native import run as native_audit
        with cli.forbid_gpu():result=native_audit(cli,a.source_package,a.capture,a.out,a.timeout,a.group_size)
        print(json.dumps({k:result[k] for k in ('schema','package_id','calculation_verified','original_stage_passed','gpu_calls','elapsed_seconds')},indent=2))
        return result
    if args and args[0]=='partitioned-run':
        p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--capture',type=Path,required=True);p.add_argument('--backend',choices=('metal',),default='metal')
        p.add_argument('--batch-size',type=int,default=16);p.add_argument('--timeout',type=int,default=180)
        for flag in ('slang-root','generation-cache','metal-pipeline-cache','swift-module-cache'):p.add_argument('--'+flag,type=Path,required=True)
        a=p.parse_args(args)
        for k,e in (('slang_root','NIKKE_SLANG_ROOT'),('generation_cache','NIKKE_SLANG_GENERATION_CACHE'),('metal_pipeline_cache','NIKKE_METAL_PIPELINE_CACHE'),('swift_module_cache','NIKKE_METAL_MODULE_CACHE')):os.environ[e]=str(getattr(a,k).resolve())
        os.environ['NIKKE_SLANG_GENERATION_REQUIRED']='1';os.environ['NIKKE_METAL_PIPELINE_REQUIRED']='1'
        result=run(cli,a.capture,a.backend,a.batch_size,a.timeout);print(json.dumps(result,indent=2))
        if not result['passed']:raise SystemExit(1)
        return result
    if args and args[0]=='_child':
        p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--capture',type=Path,required=True);p.add_argument('--backend',required=True);a=p.parse_args(args)
        if cli.load(a.capture/'run.json').get('mode')=='partitioned-cuda-origin-audit-v1':
            if a.backend!='cuda':raise ValueError('Saved CUDA origin audit requires its host-bound CUDA identity')
            from portable_partitioned_cuda_origin import child as audit_origin_child
            return audit_origin_child(cli,a.capture.resolve())
        return child(cli,a.capture.resolve(),a.backend)
    if args and args[0] in ('run','staged-run','preflight-begin','preflight-plan','preflight-resume','preflight-native-group','preflight-test-group'):
        raise ValueError('Use the explicit Metal-only partitioned diagnostic entry')
    return original(argv)
