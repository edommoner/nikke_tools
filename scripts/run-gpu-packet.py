"""Bound the entire immutable-package stage, including CPU preflight.

No original-workspace file inventory or historical report hashing. Reuses the
existing fresh Job, gate, process observer and cleanup; no parallel job engine.
"""
import argparse,contextlib,importlib.util,json,os,site,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
COMPILE_STAGES=('compile-ptx','compile-cubin-o0')
STAGES=('cpu','smoke','generation','gpu',*COMPILE_STAGES)

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

def recipe(package_id,stage,backend,capture,original_workspace,timeout):
    if stage not in STAGES or backend not in ('metal','cuda') or type(timeout) is not int or not 1<=timeout<=180:raise ValueError('Invalid packet stage or budget')
    if stage in COMPILE_STAGES and backend!='cuda':raise ValueError('Compilation requires CUDA backend')
    capture=Path(capture).resolve();original=Path(original_workspace).resolve() if original_workspace else None
    if stage in COMPILE_STAGES and original is None:raise ValueError('Compilation requires an original workspace')
    if capture==ROOT or ROOT in capture.parents:raise ValueError('Stage capture must be outside the immutable package')
    if original is not None and (original==ROOT or original==capture or original in capture.parents):raise ValueError('Use an isolated capture outside the original workspace')
    if is_windows() and original is None:raise ValueError('Windows requires an explicit original workspace')
    plan=dict(schema=1,package_id=package_id,stage=stage,backend=backend,capture=str(capture),proof_capture=str(capture/'proof'),original_workspace=str(original) if original else None,timeout_seconds=timeout,inner_gpu_timeout_seconds=min(60,timeout),preparation_scope='Immutable package manifest only; never enumerate/hash original workspace, historical captures or SDK trees',memory_limit_mb=2048)
    if stage=='generation':
        cache=os.environ.get('NIKKE_SLANG_GENERATION_CACHE')
        if not cache or not Path(cache).is_absolute():raise ValueError('Generation stage requires an absolute Slang generation cache')
        plan['generation_cache']=str(Path(cache).resolve())
    return plan

def proof_arguments(plan):
    if plan['stage']=='generation':
        return ['generation','--out',plan['proof_capture'],'--generation-cache',plan['generation_cache'],'--packet-stage',plan['capture']]
    if plan['stage'] in COMPILE_STAGES:
        if not plan['original_workspace']:raise ValueError('Compilation requires an original workspace')
        kind='ptx' if plan['stage']=='compile-ptx' else 'cubin'
        arguments=['compile','--capture',plan['proof_capture'],'--timeout',str(plan['inner_gpu_timeout_seconds']),'--artifact-kind',kind,'--memory-limit-mb','2048','--original-workspace',plan['original_workspace']]
        if kind=='cubin':arguments.extend(['--ptxas-level','0'])
        return arguments
    arguments=['run','--backend',plan['backend'],'--capture',plan['proof_capture'],'--timeout',str(plan['inner_gpu_timeout_seconds'])]
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
    expected=recipe(manifest['package_id'],plan['stage'],plan['backend'],folder,plan['original_workspace'],plan['timeout_seconds'])
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
    os.chdir(ROOT);sys.argv=[str(ROOT/'scripts/nikke_gpu.py'),*proof_arguments(plan)]
    with contextlib.ExitStack() as stack:
        for name in ('verify_package','cpu_test_groups','cpu_preflight','run_job'):
            if not hasattr(cli,name):continue
            original=getattr(cli,name)
            def observed(*args,_fn=original,_name=name,**kwargs):
                def checked():
                    result=_fn(*args,**kwargs)
                    if _name=='verify_package' and result.get('package_id')!=plan['package_id']:raise ValueError('Packet changed after stage gate')
                    return result
                return journal.invoke('packet_'+_name,checked)
            stack.enter_context(patch.object(cli,name,observed))
        journal.invoke('packet_shared_cli',cli.main)

def run_stage(folder,stage,backend,timeout,original_workspace=None):
    started=time.monotonic()
    cli=load_module('packet_stage_cli',ROOT/'scripts/nikke_gpu.py');manifest=packet_header(cli)
    plan=recipe(manifest['package_id'],stage,backend,folder,original_workspace,timeout);folder=Path(plan['capture'])
    folder.mkdir(parents=True,exist_ok=False);save(folder/'recipe.json',plan)
    from portable_phase_audit import Journal
    journal=Journal(folder/'preparation.jsonl')
    journal.emit('packet_header_prepare','returned',elapsed_seconds=time.monotonic()-started)
    # A claim is durable before any launch; a missing result never permits retry.
    save(ROOT/('packet-stage-claimed-'+stage+'-'+backend+'.json'),dict(package_id=manifest['package_id'],capture=str(folder),created_unix_ns=time.time_ns()))
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
    key={'cpu':'cpu_verified','smoke':'smoke_verified','generation':'verified','gpu':'passed',**{name:'compiler_verified' for name in COMPILE_STAGES}}[stage]
    compiler_verified=bool(proof and proof.get('mode')=='compile-only' and proof.get('compiler_verified') is True and proof.get('calculation_verified') is False and type(proof.get('gpu_calls')) is int and proof['gpu_calls']==0 and type(proof.get('driver_load_calls')) is int and proof['driver_load_calls']==0)
    generation_verified=verified_generation(proof,manifest['package_id'])
    if stage not in COMPILE_STAGES:compiler_verified=False
    verified=compiler_verified if stage in COMPILE_STAGES else generation_verified if stage=='generation' else bool(proof and proof.get(key))
    stage_verified=bool(facts['passed'] and verified)
    result=dict(schema=1,package_id=manifest['package_id'],stage=stage,bounded_execution_verified=facts['passed'],proof_result=proof,compiler_verified=compiler_verified,generation_verified=generation_verified if stage=='generation' else False,calculation_verified=bool(stage not in (*COMPILE_STAGES,'generation') and proof and proof.get('calculation_verified')),cpu_verified=bool(proof and proof.get('cpu_verified')),smoke_verified=bool(proof and proof.get('smoke_verified')),whole_stage_process_preservation_verified=process_preserved if is_windows() else None,whole_stage_environment_preservation_verified=environment_preserved,stage_verified=stage_verified,stage_complete=bool(facts['passed'] and proof),gpu_retries=0,full_goal_complete=False)
    save(folder/'stage-result.json',result);return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--stage',choices=STAGES);parser.add_argument('--backend',choices=('metal','cuda'));parser.add_argument('--timeout',type=int,default=180);parser.add_argument('--original-workspace');parser.add_argument('--_child',action='store_true');args=parser.parse_args()
    if args._child:child(args.capture.resolve());return
    if not args.stage or not args.backend:parser.error('--stage and --backend required')
    result=run_stage(args.capture,args.stage,args.backend,args.timeout,args.original_workspace);print(json.dumps(result));raise SystemExit(0 if result['stage_verified'] else 1)
if __name__=='__main__':main()
