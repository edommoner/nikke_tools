"""One CPU proof auditor for typed Actor CUDA/Metal short suites."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def audit(*,version,source,expected_file,inputs,native_oracles,test_counts,phase_suite,old_replays,payload_files,payload_bytes):
 def load(p):return json.loads((ROOT/'research'/p).read_text())
 def blob(p):return subprocess.check_output(['git','show',source+':'+p],cwd=ROOT)
 summary_name=f'windows-portable-world-v{version}-summary.json';execution_name=f'portable-world-v{version}-execution.json';receipt_name=f'portable-cross-v{version}-receipt.json'
 s=load(summary_name);e=load(execution_name);r=load(receipt_name);g=load(expected_file);receipt=load(f'portable-cross-v{version}-import-receipt.json');payload=load(f'portable-world-v{version}-source-payload.json')
 assert json.loads(blob('research/'+expected_file))==g
 assert s['passed'] and s['input_count']==inputs and s['input_sha256']==g['input_sha256'] and s['output_sha256']==g['output_sha256'] and s['entries']==g['entries'] and s['generated_normalized']==g['generated_normalized'] and len(s['entries'])==inputs
 evidence=s['evidence'];assert evidence['backend']=='cuda' and evidence['gpu_execution_verified'] and evidence['source_sha256']==g['source_sha256'];assert evidence['input_sha256']==g['input_sha256'] and evidence['output_sha256']==g['output_sha256']
 for p,h in g['source_sha256'].items():assert sha(blob(p))==h
 assert receipt['source_commit']==r['source_commit']==payload['source_commit']==source and payload['file_count']==payload_files
 for p in payload['files']:assert len(blob(p['path']))==p['bytes'] and sha(blob(p['path']))==p['sha256']
 assert sum(p['bytes'] for p in payload['files'])==payload_bytes
 assert {a['local_name'] for a in receipt['artifacts']}=={summary_name,execution_name,receipt_name} and len(receipt['artifacts'])==3
 for a in receipt['artifacts']:
  data=(ROOT/'research'/a['local_name']).read_bytes();assert len(data)==a['bytes'] and sha(data)==a['sha256']
 assert e['passed'] and not e['timed_out'] and e['child_exit_code']==e['final_child_exit_code']==0 and e['error'] is None and e['cleanup_error'] is None and e['below_normal_priority'] and e['timeout_seconds']==180 and e['cleanup_wait_seconds']==5 and e['elapsed_seconds']<180
 assert r['passed'] and r['original_head_equal'] and r['original_status_equal'] and r['existing_gpu_service_preserved'] and r['residual_verification_process_count']==0 and r['actual_gpu_execution_count']==1
 assert r['gpu_retry_count']==e['gpu_retry_count']==0
 for n in old_replays:assert r[n+'_execution_count']==s[n+'_reexecutions']==0
 pre=r['cpu_preflight'];assert pre['source_commit']==source and pre['passed'] and pre['cpu_short']['exit_code']==0 and pre['original_head_before']=='61a43e91301841c272badce519e4d8984bb5efae'
 cpu=pre['cpu_short_report'];assert cpu['passed'] and cpu['input_count']==inputs and cpu['native_oracles']==native_oracles and cpu['input_sha256']==g['input_sha256'] and cpu['source_sha256']==g['source_sha256'] and cpu['gpu_calls']==dict(build=0,execute=0)
 tests=pre['cpu_tests'];assert [(x['pattern'],x['expected_count']) for x in tests]==test_counts
 for test in tests:assert test['exit_code']==0 and test['stderr'].rstrip().endswith('OK') and int(re.search(r'Ran (\d+) tests',test['stderr'])[1])==test['expected_count']
 phases=r['phase_rows'];assert len(phases)==e['phase']['events']==50 and all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(phases,phases[1:])) and not any(p['state']=='raised' for p in phases)
 last=-1
 for stage in ('nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):
  hits=[(i,p) for i,p in enumerate(phases) if p['stage']==stage];assert len(hits)==2 and hits[0][1]['state']=='entered' and hits[1][1]['state']=='returned' and hits[1][1]['return_code']==0 and hits[0][0]>last;last=hits[1][0]
 assert phases[-1]['stage']==phase_suite and phases[-1]['state']=='returned'
 assert all(e['phase'][k] for k in ['nvrtc_compile_returned_success','cuda_launch_returned_success','cuda_synchronize_returned_success','cuda_readback_returned_success'])
 return dict(passed=True,source_commit=source,inputs=inputs,all_input_output_bytes_native_and_generated_fingerprints_equal=True,actual_cuda_executions=1,cuda_elapsed_seconds=e['elapsed_seconds'],cpu_tests=sum(n for _,n in test_counts),cpu_native_oracles=native_oracles,cpu_gpu_calls=0,phase_events=50,**{n+'_reexecutions':0 for n in old_replays},gpu_retries=0,residual_processes=0,original_windows_work_and_service_preserved=True,imported_bytes=sum(a['bytes'] for a in receipt['artifacts']),source_payload_bytes=payload_bytes,audit_gpu_calls=0,full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False)
