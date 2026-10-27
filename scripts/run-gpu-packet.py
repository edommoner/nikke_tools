"""Bound the entire immutable-package stage, including CPU preflight.

No original-workspace file inventory or historical report hashing. Reuses the
existing fresh Job, gate, process observer and cleanup; no parallel job engine.
"""
import argparse,contextlib,importlib.util,json,os,site,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
COMPILE_STAGES=('compile-ptx','compile-cubin-o0','compile-cubin-o1')
OBJECT_STAGES={'recover-object':('source_package','source_capture','object_sha256'),'module-object':('source_package','source_capture','cache_entry','phases','ptxas'),
               'jit-link-object':('object_package','object_capture','object_sha256','nvjitlink')}
LINKED_STAGE='gpu-linked'
LINKED_FIELDS=('linked_package','linked_capture')
RECOVERY_STAGE='recover-readback'
RECOVERY_FIELDS=('source_package','source_capture','output_sha256')
NATIVE_GROUP_STAGE='audit-native-group'
NATIVE_GROUP_FIELDS=('source_package','source_capture','group_index','group_size')
STAGES=('tests','cpu','smoke','generation','gpu',LINKED_STAGE,RECOVERY_STAGE,NATIVE_GROUP_STAGE,*COMPILE_STAGES,*OBJECT_STAGES)

def is_windows():return os.name=='nt'

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def save(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())

def verified_generation(proof,package_id):
    """Source preparation cannot masquerade as a compiler or GPU receipt."""
    return bool(proof and proof.get('package_id')==package_id and proof.get('verified') is True
        and proof.get('sealed_generated_baseline_verified') is True
        and proof.get('mode','generation')=='generation' and proof.get('compiler_verified',False) is False
        and proof.get('calculation_verified') is False and proof.get('executable_battle_verified') is False
        and all(type(proof.get(key,0)) is int and proof.get(key,0)==0 for key in ('gpu_calls','driver_load_calls','nvrtc_compile_calls'))
        and 'gpu_calls' in proof)

def verified_tests(proof,package_id,patterns,rows):
    from portable_cpu_tests import complete
    return bool(proof and proof.get('mode')=='cpu-tests-only' and proof.get('package_id')==package_id
        and proof.get('cpu_tests_verified') is True and proof.get('cpu_reference_verified') is False
        and proof.get('calculation_verified') is False and proof.get('compiler_verified') is False
        and all(type(proof.get(key)) is int and proof[key]==0 for key in ('gpu_calls','driver_load_calls','native_preflight_calls'))
        and all(type(proof.get(key)) is int for key in ('groups','tests'))
        and complete(rows,patterns) and proof.get('groups')==len(rows)
        and proof.get('tests')==sum(r['tests'] for r in rows))


def run_tests(cli,plan):
    """Use the common CPU worker; no battle adapter or execution claim."""
    manifest=cli.verify_package(ROOT)
    if manifest['package_id']!=plan['package_id']:raise ValueError('Packet changed before CPU tests')
    proof=Path(plan['proof_capture']);proof.mkdir(exist_ok=False)
    try:
        with cli.forbid_gpu():rows=cli.cpu_test_groups(manifest,proof)
        result=dict(mode='cpu-tests-only',package_id=manifest['package_id'],cpu_tests_verified=True,
                    groups=len(rows),tests=sum(r['tests'] for r in rows),cpu_reference_verified=False,
                    counter_scope='Packet controller calls; unit-test doubles are not runtime calculation evidence',
                    calculation_verified=False,compiler_verified=False,gpu_calls=0,driver_load_calls=0,native_preflight_calls=0)
        if not verified_tests(result,manifest['package_id'],cli.SUITES[manifest['suite']]['tests'],rows):
            raise ValueError('Incomplete CPU test receipt')
        save(proof/'result.json',result)
    finally:cli.collect(proof,proof/'artifacts.json')


def object_request(stage,value):
    if stage not in (*OBJECT_STAGES,LINKED_STAGE,RECOVERY_STAGE,NATIVE_GROUP_STAGE):
        if value is not None:raise ValueError('Only saved-object or saved-linked GPU stages accept a request')
        return None
    fields=NATIVE_GROUP_FIELDS if stage==NATIVE_GROUP_STAGE else RECOVERY_FIELDS if stage==RECOVERY_STAGE else LINKED_FIELDS if stage==LINKED_STAGE else OBJECT_STAGES[stage]
    if type(value) is not dict or set(value)!=set(fields):raise ValueError('Exact saved-object request fields required')
    result={}
    for key in fields:
        item=value[key]
        if not isinstance(item,str) or not item or any(c in item for c in ('\x00','\r','\n')):raise ValueError('Invalid saved-object request value')
        if key in ('group_index','group_size'):
            if not item.isascii() or not item.isdigit() or str(int(item))!=item or not (0 if key=='group_index' else 1)<=int(item)<=65536:
                raise ValueError('Canonical bounded native group integer required')
            result[key]=item
        elif key in ('object_sha256','output_sha256'):
            if len(item)!=64 or any(c not in '0123456789abcdef' for c in item):raise ValueError('Exact saved-object SHA256 required')
            result[key]=item
        else:
            if not Path(item).is_absolute():raise ValueError('Absolute saved-object paths required')
            result[key]=str(Path(item).resolve())
    return result


def verified_object(proof,stage):
    return bool(proof and stage in OBJECT_STAGES and proof.get('mode')==stage+'-only'
        and proof.get('object_verified') is True and proof.get('containment_verified') is True
        and proof.get('calculation_verified') is False
        and proof.get('link_verified') is (stage=='jit-link-object')
        and type(proof.get('kernel_calls')) is int and proof['kernel_calls']==0
        and (stage!='recover-object' or (type(proof.get('native_tool_calls')) is int
            and proof['native_tool_calls']==0 and proof.get('original_stage_verified') is False
            and proof.get('original_capture_modified') is False and proof.get('original_outer_timed_out') is True))
        and all(type(proof.get(k,0)) is int and proof.get(k,0)==0 for k in ('gpu_calls','driver_load_calls','nvrtc_compile_calls')))


def verified_readback(proof):
    return bool(proof and proof.get('mode')=='recover-readback-only'
        and proof.get('calculation_verified') is True and proof.get('containment_verified') is True
        and proof.get('preservation_verified') is True
        and proof.get('original_outer_timed_out') is True
        and proof.get('original_stage_verified') is False and proof.get('original_capture_modified') is False
        and all(type(proof.get(k)) is int and proof[k]==0 for k in ('gpu_calls','driver_load_calls','native_tool_calls')))


def verified_native_group(proof,request):
    if not proof or proof.get('mode')!='saved-native-group-only' or proof.get('backend')!='cuda':return False
    if proof.get('group_index')!=int(request['group_index']) or proof.get('group_size')!=int(request['group_size']):return False
    if proof.get('source_package')!=request['source_package'] or proof.get('source_capture')!=request['source_capture']:return False
    group=proof.get('group',{});audit=group.get('audit',{});comparison=group.get('comparison',{})
    from portable_comparison_groups import partition
    count=comparison.get('total_input_count');bound=proof.get('per_group_timeout_seconds')
    if type(count) is not int or not 1<=count<=65536 or type(bound) is not int or not 1<=bound<=180:return False
    planned=partition(count,int(request['group_size']));index=int(request['group_index'])
    if index>=len(planned) or proof.get('planned')!=planned:return False
    indices=planned[index];pid=group.get('child_pid');elapsed=group.get('elapsed_seconds');native=comparison.get('native_oracles')
    if (comparison.get('case_indices')!=indices or comparison.get('input_count')!=len(indices)
        or len(comparison.get('entries',[]))!=len(indices) or group.get('package_id')!=proof.get('package_id')
        or type(pid) is not int or pid<=0 or pid==os.getpid()
        or type(elapsed) not in (int,float) or not 0<=elapsed<=bound+1
        or type(native) is not int or not 0<=native<=len(indices)):return False
    return bool(proof.get('comparison_subset_verified') is True and proof.get('calculation_verified') is False
        and type(proof.get('gpu_calls')) is int and proof['gpu_calls']==0
        and group.get('live_parent_receipt_present') is False
        and comparison.get('comparison_subset_verified') is True and comparison.get('calculation_verified') is False
        and comparison.get('mismatches')==[] and 'parent_oracles' not in comparison
        and type(comparison.get('audit_gpu_calls')) is int and comparison['audit_gpu_calls']==0
        and audit.get('transport_core_verified') is True and audit.get('containment_verified') is True
        and audit.get('calculation_verified') is False and audit.get('comparison_error') is None)


def recipe(package_id,stage,backend,capture,original_workspace,timeout,request=None):
    if stage not in STAGES or backend not in ('metal','cuda') or type(timeout) is not int or not 1<=timeout<=180:raise ValueError('Invalid packet stage or budget')
    if stage in (*COMPILE_STAGES,*OBJECT_STAGES,LINKED_STAGE,RECOVERY_STAGE,NATIVE_GROUP_STAGE) and backend!='cuda':raise ValueError('Compilation requires CUDA backend')
    request=object_request(stage,request)
    capture=Path(capture).resolve();original=Path(original_workspace).resolve() if original_workspace else None
    if stage in (*COMPILE_STAGES,*OBJECT_STAGES,LINKED_STAGE,RECOVERY_STAGE,NATIVE_GROUP_STAGE) and original is None:raise ValueError('Compilation requires an original workspace')
    if capture==ROOT or ROOT in capture.parents:raise ValueError('Stage capture must be outside the immutable package')
    if original is not None and (original==ROOT or original==capture or original in capture.parents):raise ValueError('Use an isolated capture outside the original workspace')
    if is_windows() and original is None:raise ValueError('Windows requires an explicit original workspace')
    plan=dict(schema=1,package_id=package_id,stage=stage,backend=backend,capture=str(capture),proof_capture=str(capture/'proof'),original_workspace=str(original) if original else None,timeout_seconds=timeout,inner_gpu_timeout_seconds=min(60,timeout),preparation_scope='Immutable package manifest only; never enumerate/hash original workspace, historical captures or SDK trees',memory_limit_mb=2048)
    if stage=='generation':
        cache=os.environ.get('NIKKE_SLANG_GENERATION_CACHE')
        if not cache or not Path(cache).is_absolute():raise ValueError('Generation stage requires an absolute Slang generation cache')
        plan['generation_cache']=str(Path(cache).resolve())
    if request is not None:plan['object_request']=request
    return plan

def proof_arguments(plan):
    if plan['stage']=='tests':return ['_tests','--capture',plan['proof_capture']]
    if plan['stage']==RECOVERY_STAGE:
        request=object_request(RECOVERY_STAGE,plan['object_request'])
        return [RECOVERY_STAGE,'--source-package',request['source_package'],'--source-capture',request['source_capture'],'--out',plan['proof_capture'],'--output-sha256',request['output_sha256']]
    if plan['stage']==NATIVE_GROUP_STAGE:
        request=object_request(NATIVE_GROUP_STAGE,plan['object_request'])
        return ['saved-battle-audit','--backend','cuda','--package-root',request['source_package'],
            '--capture',request['source_capture'],'--group-index',request['group_index'],'--group-size',request['group_size'],
            '--timeout',str(plan['timeout_seconds']),'--out',str(Path(plan['proof_capture'])/'result.json')]
    if plan['stage']=='recover-object':
        request=object_request('recover-object',plan['object_request'])
        return ['recover-object','--source-package',request['source_package'],'--source-capture',request['source_capture'],'--out',plan['proof_capture'],'--object-sha256',request['object_sha256']]
    if plan['stage'] in OBJECT_STAGES:
        request=object_request(plan['stage'],plan['object_request'])
        arguments=[plan['stage'],'--capture',plan['proof_capture'],'--timeout',str(plan['inner_gpu_timeout_seconds']),'--original-workspace',plan['original_workspace']]
        for key in OBJECT_STAGES[plan['stage']]:arguments.extend(['--'+key.replace('_','-'),request[key]])
        return arguments
    if plan['stage']=='generation':
        return ['generation','--out',plan['proof_capture'],'--generation-cache',plan['generation_cache'],'--packet-stage',plan['capture']]
    if plan['stage'] in COMPILE_STAGES:
        if not plan['original_workspace']:raise ValueError('Compilation requires an original workspace')
        kind='ptx' if plan['stage']=='compile-ptx' else 'cubin'
        arguments=['compile','--capture',plan['proof_capture'],'--timeout',str(plan['inner_gpu_timeout_seconds']),'--artifact-kind',kind,'--memory-limit-mb','2048','--original-workspace',plan['original_workspace']]
        if kind=='cubin':arguments.extend(['--ptxas-level','1' if plan['stage']=='compile-cubin-o1' else '0'])
        return arguments
    arguments=['run','--backend',plan['backend'],'--capture',plan['proof_capture'],'--timeout',str(plan['inner_gpu_timeout_seconds'])]
    if plan['stage']==LINKED_STAGE:
        request=object_request(LINKED_STAGE,plan['object_request'])
        for key in LINKED_FIELDS:arguments.extend(['--'+key.replace('_','-'),request[key]])
    if plan['stage']=='cpu':arguments.append('--cpu-only')
    elif plan['stage']=='smoke':arguments.append('--smoke')
    if plan['original_workspace']:arguments.extend(['--original-workspace',plan['original_workspace']])
    return arguments

def packet_header(cli):
    # Parent preparation reads this small identity document only. Full member
    # hashing belongs to the gated, bounded child, never a historical tree.
    manifest=cli.load(ROOT/'gpu-package.json')
    if manifest.get('schema')!=cli.SCHEMA or manifest.get('suite') not in cli.SUITES or manifest.get('package_id')!=cli.package_id(manifest):raise ValueError('Invalid packet header')
    return manifest

def child(folder):
    plan=json.loads((folder/'recipe.json').read_text())
    if plan['capture']!=str(folder.resolve()):raise ValueError('Stage recipe directory changed')
    cli=load_module('packet_child_cli',ROOT/'scripts/nikke_gpu.py');manifest=packet_header(cli)
    expected=recipe(manifest['package_id'],plan['stage'],plan['backend'],folder,plan['original_workspace'],plan['timeout_seconds'],plan.get('object_request'))
    if plan!=expected:raise ValueError('Packet stage recipe changed')
    save(folder/'child.json',dict(pid=os.getpid(),ppid=os.getppid(),package_id=manifest['package_id'],started_unix_ns=time.time_ns(),scope='Identity record only; liveness requires the owning process handle'))
    deadline=time.monotonic()+30
    while not (folder/'start.json').exists():
        if time.monotonic()>=deadline:raise RuntimeError('Whole-stage containment gate was not released')
        time.sleep(.02)
    # Shared run_capture performs full byte/source verification before every
    # CPU/GPU gate. Do not duplicate that scan or import a second CLI instance.
    # These observers time the original functions; none replaces their checks.
    from portable_phase_audit import Journal
    journal=Journal(folder/'preparation.jsonl')
    os.chdir(ROOT)
    if plan['stage']=='tests':
        journal.invoke('packet_cpu_tests',run_tests,cli,plan);return
    sys.argv=[str(ROOT/'scripts/nikke_gpu.py'),*proof_arguments(plan)]
    with contextlib.ExitStack() as stack:
        for name in ('verify_package','cpu_test_groups','cpu_preflight','run_job'):
            if not hasattr(cli,name):continue
            original=getattr(cli,name)
            def observed(*args,_fn=original,_name=name,**kwargs):
                def checked():
                    result=_fn(*args,**kwargs)
                    # Saved-artifact admission also verifies its historical
                    # producer package. Its identity must stay distinct; the
                    # full verifier and lineage admission still check it.
                    if _name=='verify_package':
                        verified_root=Path(args[0] if args else kwargs['root']).resolve()
                        if verified_root==ROOT.resolve() and result.get('package_id')!=plan['package_id']:raise ValueError('Packet changed after stage gate')
                    return result
                return journal.invoke('packet_'+_name,checked)
            stack.enter_context(patch.object(cli,name,observed))
        journal.invoke('packet_shared_cli',cli.main)

def run_stage(folder,stage,backend,timeout,original_workspace=None,request=None):
    started=time.monotonic()
    cli=load_module('packet_stage_cli',ROOT/'scripts/nikke_gpu.py');manifest=packet_header(cli)
    plan=recipe(manifest['package_id'],stage,backend,folder,original_workspace,timeout,request);folder=Path(plan['capture'])
    folder.mkdir(parents=True,exist_ok=False);save(folder/'recipe.json',plan)
    from portable_phase_audit import Journal
    journal=Journal(folder/'preparation.jsonl')
    journal.emit('packet_header_prepare','returned',elapsed_seconds=time.monotonic()-started)
    # A claim is durable before any launch; a missing result never permits retry.
    claim_stage=stage+('-'+plan['object_request']['group_index'] if stage==NATIVE_GROUP_STAGE else '')
    save(ROOT/('packet-stage-claimed-'+claim_stage+'-'+backend+'.json'),dict(package_id=manifest['package_id'],capture=str(folder),created_unix_ns=time.time_ns()))
    bounded=cli.bounded_module();env=cli.validation_environment(folder)
    if stage=='generation':env['NIKKE_SLANG_GENERATION_REQUIRED']='0'
    env['NIKKE_VALIDATION_JOB_MEMORY_MB']='2048'
    env['PYTHONPATH']=os.pathsep.join([*site.getsitepackages(),env.get('PYTHONPATH','')])
    interpreter=getattr(sys,'_base_executable',sys.executable) if is_windows() else sys.executable
    command=[interpreter,str(Path(__file__).resolve()),'--_child','--capture',str(folder)]
    save(folder/'command.json',dict(argv=command,cwd=str(ROOT),shell=False,base_python=interpreter,timeout_seconds=timeout,preparation_scope=plan['preparation_scope']))
    remaining=timeout-(time.monotonic()-started)
    if remaining<=0:raise TimeoutError('Packet header preparation exhausted budget; no child launched')
    observation={}
    def before():
        from windows_validation_observer import capture_snapshot
        observation['before']=capture_snapshot(plan['original_workspace'],ROOT);cli.write(folder/'observation.json',observation)
    def after():
        from windows_validation_observer import capture_snapshot,compare_snapshots
        observation['after']=capture_snapshot(plan['original_workspace'],ROOT)
        if 'before' in observation:observation['comparison']=compare_snapshots(observation['before'],observation['after'])
        cli.write(folder/'observation.json',observation)
    with patch.dict(os.environ,{'NIKKE_VALIDATION_JOB_MEMORY_MB':'2048'}):
        if is_windows():
            from windows_validation_observer import observe_job
            with observe_job(bounded,folder/'job.json'):
                facts=journal.invoke('packet_bounded_stage',bounded.run_bounded,command,folder,remaining,cwd=ROOT,env=env,before_gate=lambda:journal.invoke('packet_before_observation',before),after_wait=lambda:journal.invoke('packet_after_observation',after))
        else:facts=journal.invoke('packet_bounded_stage',bounded.run_bounded,command,folder,remaining,cwd=ROOT,env=env)
    proof_path=folder/('proof/generation.json' if stage=='generation' else 'proof/result.json');proof=json.loads(proof_path.read_text()) if proof_path.is_file() else None
    comparison=observation.get('comparison',{})
    process_preserved=comparison.get('all_monitored_processes_preserved')
    environment_preserved=bool(process_preserved is True and comparison.get('identified_nikke_service_preservation_verified') is True and facts.get('observation_error') is None) if is_windows() else None
    key={'tests':'cpu_tests_verified','cpu':'cpu_verified','smoke':'smoke_verified','generation':'verified','gpu':'passed',LINKED_STAGE:'passed',RECOVERY_STAGE:'passed',NATIVE_GROUP_STAGE:'comparison_subset_verified',**{name:'compiler_verified' for name in COMPILE_STAGES},**{name:'object_verified' for name in OBJECT_STAGES}}[stage]
    compiler_verified=bool(proof and proof.get('mode')=='compile-only' and proof.get('compiler_verified') is True and proof.get('calculation_verified') is False and type(proof.get('gpu_calls')) is int and proof['gpu_calls']==0 and type(proof.get('driver_load_calls')) is int and proof['driver_load_calls']==0)
    generation_verified=verified_generation(proof,manifest['package_id'])
    if stage not in COMPILE_STAGES:compiler_verified=False
    diagnostic_verified=verified_object(proof,stage) if stage in OBJECT_STAGES else False
    tests_verified=False
    if stage=='tests':
        rows_path=folder/'proof/cpu-tests.json';rows=json.loads(rows_path.read_text()) if rows_path.is_file() else []
        tests_verified=verified_tests(proof,manifest['package_id'],cli.SUITES[manifest['suite']]['tests'],rows)
    verified=tests_verified if stage=='tests' else compiler_verified if stage in COMPILE_STAGES else diagnostic_verified if stage in OBJECT_STAGES else generation_verified if stage=='generation' else bool(proof and proof.get(key))
    if stage==RECOVERY_STAGE:verified=verified_readback(proof)
    if stage==NATIVE_GROUP_STAGE:
        verified=verified_native_group(proof,plan['object_request'])
    stage_verified=bool(facts['passed'] and verified)
    result=dict(schema=1,package_id=manifest['package_id'],stage=stage,bounded_execution_verified=facts['passed'],proof_result=proof,compiler_verified=compiler_verified,generation_verified=generation_verified if stage=='generation' else False,calculation_verified=bool(stage not in (*COMPILE_STAGES,*OBJECT_STAGES,'generation','tests') and proof and proof.get('calculation_verified')),cpu_verified=bool(proof and proof.get('cpu_verified')),smoke_verified=bool(proof and proof.get('smoke_verified')),whole_stage_process_preservation_verified=process_preserved if is_windows() else None,whole_stage_environment_preservation_verified=environment_preserved,stage_verified=stage_verified,stage_complete=bool(facts['passed'] and proof),gpu_retries=0,full_goal_complete=False)
    if stage=='tests':result.update(cpu_tests_verified=tests_verified,cpu_reference_verified=False)
    if stage in OBJECT_STAGES:result.update(diagnostic_verified=diagnostic_verified,object_verified=diagnostic_verified,link_verified=bool(diagnostic_verified and stage=='jit-link-object'))
    save(folder/'stage-result.json',result);return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--stage',choices=STAGES);parser.add_argument('--backend',choices=('metal','cuda'));parser.add_argument('--timeout',type=int,default=180);parser.add_argument('--original-workspace');parser.add_argument('--request',type=Path);parser.add_argument('--_child',action='store_true');args=parser.parse_args()
    if args._child:child(args.capture.resolve());return
    if not args.stage or not args.backend:parser.error('--stage and --backend required')
    request=None
    if args.request:
        if args.request.stat().st_size>16384:raise ValueError('Saved-object request exceeds16KiB')
        request=json.loads(args.request.read_text(encoding='utf-8'))
    result=run_stage(args.capture,args.stage,args.backend,args.timeout,args.original_workspace,request);print(json.dumps(result));raise SystemExit(0 if result['stage_verified'] else 1)
if __name__=='__main__':main()
