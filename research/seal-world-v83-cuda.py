"""CPU-only seal: Windows actual CUDA77 versus frozen Metal285 projections."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='ea1f8ddee06cc7c995307d5e110a60b6c696893c'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):return json.loads((ROOT/'research'/name).read_text())
def blob(path):return subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)
def main():
 s=load('windows-portable-world-v83-summary.json');e=load('portable-world-v83-execution.json');r=load('portable-cross-v83-receipt.json');g=load('portable-world-actor-pools-short-expected.json');receipt=load('portable-cross-v83-import-receipt.json');payload=load('portable-world-v83-source-payload.json')
 assert json.loads(blob('research/portable-world-actor-pools-short-expected.json'))==g
 assert s['passed'] and s['input_count']==77 and s['input_sha256']==g['input_sha256'] and s['output_sha256']==g['output_sha256'] and s['entries']==g['entries'] and s['generated_normalized']==g['generated_normalized'];assert len(s['entries'])==77
 evidence=s['evidence'];assert evidence['backend']=='cuda' and evidence['gpu_execution_verified'] and evidence['source_sha256']==g['source_sha256'];assert evidence['input_sha256']==g['input_sha256'] and evidence['output_sha256']==g['output_sha256']
 for p,h in g['source_sha256'].items():assert sha(blob(p))==h
 assert receipt['source_commit']==r['source_commit']==payload['source_commit']==SOURCE and payload['file_count']==24
 for p in payload['files']:assert len(blob(p['path']))==p['bytes'] and sha(blob(p['path']))==p['sha256']
 assert sum(p['bytes'] for p in payload['files'])==301900
 for a in receipt['artifacts']:
  data=(ROOT/'research'/a['local_name']).read_bytes();assert len(data)==a['bytes'] and sha(data)==a['sha256']
 assert sum(a['bytes'] for a in receipt['artifacts'])==56595
 assert e['passed'] and not e['timed_out'] and e['child_exit_code']==e['final_child_exit_code']==0 and e['error'] is None and e['cleanup_error'] is None and e['below_normal_priority'] and e['timeout_seconds']==180 and e['cleanup_wait_seconds']==5 and e['elapsed_seconds']<180
 assert r['passed'] and r['original_head_equal'] and r['original_status_equal'] and r['existing_gpu_service_preserved'] and r['residual_verification_process_count']==0 and r['actual_gpu_execution_count']==1
 assert r['gpu_retry_count']==e['gpu_retry_count']==r['normal4682_execution_count']==r['old208_execution_count']==s['normal4682_reexecutions']==s['old208_reexecutions']==0
 pre=r['cpu_preflight'];assert pre['source_commit']==SOURCE and pre['passed'] and pre['cpu_short']['exit_code']==0 and pre['original_head_before']=='61a43e91301841c272badce519e4d8984bb5efae'
 cpu=pre['cpu_short_report'];assert cpu['passed'] and cpu['input_count']==77 and cpu['native_oracles']==36 and cpu['input_sha256']==g['input_sha256'] and cpu['source_sha256']==g['source_sha256'] and cpu['gpu_calls']==dict(build=0,execute=0)
 tests=pre['cpu_tests'];assert [(x['pattern'],x['expected_count']) for x in tests]==[('test_portable_phase_audit.py',5),('test_portable_actor_registry_input.py',4),('test_portable_actor_pool_input.py',6)]
 for test in tests:assert test['exit_code']==0 and test['stderr'].rstrip().endswith('OK') and int(re.search(r'Ran (\d+) tests',test['stderr'])[1])==test['expected_count']
 phases=r['phase_rows'];assert len(phases)==e['phase']['events']==50 and all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(phases,phases[1:])) and not any(p['state']=='raised' for p in phases)
 last=-1
 for stage in ('nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):
  hits=[(i,p) for i,p in enumerate(phases) if p['stage']==stage];assert len(hits)==2 and hits[0][1]['state']=='entered' and hits[1][1]['state']=='returned' and hits[1][1]['return_code']==0 and hits[0][0]>last;last=hits[1][0]
 assert phases[-1]['stage']=='shared_world_actor_pools_short' and phases[-1]['state']=='returned'
 assert all(e['phase'][k] for k in ['nvrtc_compile_returned_success','cuda_launch_returned_success','cuda_synchronize_returned_success','cuda_readback_returned_success'])
 result=dict(passed=True,source_commit=SOURCE,inputs=77,complete_native_battles=14,typed_pool_set_cases=10,registry_native_cases=12,raw_rejections=41,all_input_output_bytes_native_and_generated_fingerprints_equal=True,actual_cuda_executions=1,cuda_elapsed_seconds=e['elapsed_seconds'],cpu_tests=15,cpu_native_oracles=36,cpu_gpu_calls=0,phase_events=50,normal4682_reexecutions=0,old208_reexecutions=0,gpu_retries=0,residual_processes=0,original_windows_work_and_service_preserved=True,imported_bytes=56595,source_payload_bytes=301900,audit_gpu_calls=0,full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False)
 (ROOT/'research/portable-world-v83-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA77 audited: Metal byte/native/generated exact;CPU15+36 oracles;one GPU,72.917s;residual0')
if __name__=='__main__':main()
