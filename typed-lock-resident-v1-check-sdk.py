import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent

def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def gate(d,artifact=False):
 e=load(d/'execution.json');o=load(d/'observation.json');j=load(d/'job.json')['records'];assert not e['timed_out'] and not any(e.get(k) for k in ('error','cleanup_error','observation_error')),'Execution error';assert 'comparison' in o and not o['comparison']['missing_existing_processes'] and not o.get('comparison_error'),'Observation/missing failure';assert j and all(x['pre_gate_verified'] and not x['inspection_error'] and x['post_wait']['job_members']==[] and x['pre_gate']['job_memory_limit_bytes']==x['post_wait']['job_memory_limit_bytes']==2147483648 for x in j),'Enforced Job gate incomplete';assert e['child_exit_code'] in ([0,2] if artifact else [0]),'Child stage failed'
 return dict(child_exit_code=e['child_exit_code'],reported_execution_passed=e['passed'],elapsed_seconds=e['elapsed_seconds'],timeout_seconds=e['timeout_seconds'],timed_out=False,cleanup_error=None,observation_error=None,missing_processes=0,pre_gate_verified=True,post_wait_empty=True,job_memory_limit_bytes=2147483648,job_peak_memory_bytes=max(x['post_wait']['job_peak_memory_bytes'] for x in j),below_normal=e['below_normal_priority'])
def main(name,stage,runner_exit):
 assert not (R/'stop.json').exists();P=R/name;program=load(P/'program.json');cfg=load(P/'sdk-paths.json');capture={'unpack':'unpack','plans':'plans','host-tests':'host-tests','ptx-audit':'ptx-audit','generation':'generation-v1','compile-ptx':'compile-ptx-v1','module-object':'module-object-v1','jit-link-object':'jit-link-v1'}[stage];D=P/capture;facts=gate(D,stage in ('compile-ptx','module-object','jit-link-object'));facts['runner_exit_code']=runner_exit
 if stage in ('unpack','plans','host-tests','ptx-audit'):assert runner_exit==0
 else:
  result=load(D/'stage-result.json');flag={'generation':'generation_verified','compile-ptx':'compiler_verified','module-object':'object_verified','jit-link-object':'link_verified'}[stage];assert result[flag] and result['package_id']==program['owner'];facts.update(artifact_verified=True,reported_stage_verified=result['stage_verified'],reported_stage_complete=result['stage_complete'],reported_whole_environment_preservation_verified=result['whole_stage_environment_preservation_verified'])
  if stage!='generation':facts['inner']=gate(D/'proof')
 if stage in ('host-tests','ptx-audit'):
  proof=load(D/'verification.json');assert proof['passed']
  if stage=='host-tests':
   assert type(program['windows_targeted_tests']) is int and program['windows_targeted_tests']>0
   assert proof['tests']==program['windows_targeted_tests']
   assert proof['selected_unit_tests_verified'] and proof['all_registered_unit_tests_verified'] is False
   assert proof['selection_sha256']==program['unit_selection_sha256']
 if stage=='generation':assert load(D/'stage-result.json')['proof_result']['sealed_generated_baseline_verified'] and runner_exit==0
 if stage=='compile-ptx':
  c=load(D/'proof/compiler.json');g=load(D/'proof/generation-cache.json');assert g['hit'] and g['compiler_invocations']==0
  write(P/'module-object-v1-request.json',dict(source_package=cfg['packet'],source_capture=str(D/'proof'),cache_entry=str(Path(cfg['compile_cache'])/(c['compile_artifact']['key']+'.json')),phases=str(D/'proof/phases.jsonl'),ptxas=cfg['ptxas']))
 if stage=='module-object':
  o=load(D/'proof/object.json');assert o['origin']['source_bytes_unchanged'] and not o['origin']['source_partitioned'];lib=R.parent/'nikke-jit-link-d1594d9-diagnostic/component/libnvjitlink-windows-x86_64-12.4.127-archive/bin/nvJitLink_120_0.dll';assert hashlib.sha256(lib.read_bytes()).hexdigest()=='2da9da786b85c100ba122f931a49c5c1eda83c32e3fa36814c2ef470e45fa9b1';write(P/'jit-link-v1-request.json',dict(object_package=cfg['packet'],object_capture=str(D/'proof'),object_sha256=o['receipt']['artifact']['sha256'],nvjitlink=str(lib)))
 if stage=='jit-link-object':
  link=load(D/'proof/jit-link.json')['receipt'];assert all(e['return_code']==0 for e in link['api_diagnostic']['events']) and link['api_diagnostic']['program_driver_api_calls']==0
 write(P/(stage+'-verified.json'),facts);print(json.dumps(dict(program=name,stage=stage,passed=True,outer_exit=facts['child_exit_code'],peak_bytes=facts['job_peak_memory_bytes'])),flush=True)
if __name__=='__main__':
 name,stage=sys.argv[1:3]
 try:main(name,stage,int(sys.argv[3]))
 except BaseException as e:
  if not (R/'stop.json').exists():write(R/'stop.json',dict(program=name,stage=stage,error_type=type(e).__name__,message=str(e),retries_allowed=False))
  print(json.dumps(dict(program=name,stage=stage,passed=False,error_type=type(e).__name__,message=str(e))),flush=True);raise SystemExit(1)
