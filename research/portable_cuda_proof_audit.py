"""Shared CPU-only audit of bounded CUDA proofs against frozen Metal fingerprints."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def audit(*,version,source,expected_file,native_cases,rejected_cases,case_counts,cpu_tests):
 def load(name):return json.loads((ROOT/'research'/name).read_text())
 def sha(raw):return hashlib.sha256(raw).hexdigest()
 def blob(path):return subprocess.check_output(['git','show',source+':'+path],cwd=ROOT)
 s=load(f'windows-portable-world-v{version}-summary.json');e=load(f'portable-world-v{version}-execution.json');r=load(f'portable-cross-v{version}-receipt.json');expected=load(expected_file);inputs=native_cases+rejected_cases+49
 assert s['passed'] and s['backend']=='cuda' and s['source_commit']==r['source_commit']==source
 assert s['comparison']==expected['comparison'] and s['changed_keys']==[] and s['expected_sha256']==sha(blob('research/'+expected_file))
 c=s['comparison'];assert c['native_cases']==native_cases and c['rejected_cases']==rejected_cases and c['preserved_cases']==49 and len(c['cases'])==inputs
 assert e['passed'] and not e['timed_out'] and e['child_exit_code']==e['final_child_exit_code']==0 and e['error'] is None and e['cleanup_error'] is None and e['below_normal_priority'] and e['timeout_seconds']==180 and e['cleanup_wait_seconds']==5 and e['elapsed_seconds']<180
 assert e['gpu_retry_count']==r['gpu_retry_count']==r['normal4682_execution_count']==0 and r['actual_gpu_execution_count']==1
 assert r['passed'] and r['original_head_equal'] and r['original_status_equal'] and r['existing_gpu_service_preserved'] and r['residual_verification_process_count']==0
 pre=r['cpu_preflight'];assert pre['source_commit']==source and pre['passed'] and pre['source_unchanged'] and pre['cpu_only'] and pre['job_object_descendants_verified'] and pre['gpu_sentinel_call_count']==0 and pre['gpu_sentinel_calls']==[] and pre['input_equal']
 assert pre['trace_is_none'] and pre['profile_is_none'] and not pre['sitecustomize_loaded']
 tests=[v for k,v in pre.items() if k in ('cpu_tests','cpu_overlay_tests')];assert all(v['exit_code']==0 and '\nOK\n' in v['stderr'] for v in tests);assert sum(int(re.search(r'Ran (\d+) tests',v['stderr'])[1]) for v in tests)==cpu_tests
 assert pre['case_counts']==case_counts and sum(case_counts)==native_cases and pre['total_inputs']==inputs and pre['rejections']==rejected_cases and pre['prior_inputs']==49 and pre['input_sha256']==c['input_sha256']==pre['expected_input_sha256']
 manifest=r['manifest'];assert manifest['source_commit']==source and manifest['inputs']==inputs and not manifest['normal4682_repeated']
 for path,h in manifest['files'].items():assert sha(blob(path))==h
 for path,h in c['source_sha256'].items():assert sha(blob(path))==h
 phase=r['phase_rows'];assert len(phase)==e['phase']['events']==50 and all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(phase,phase[1:])) and not any(x['state']=='raised' for x in phase)
 last=-1
 for stage in ('nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):
  rows=[(i,x) for i,x in enumerate(phase) if x['stage']==stage];assert len(rows)==2 and rows[0][1]['state']=='entered' and rows[1][1]['state']=='returned' and rows[1][1]['return_code']==0 and rows[0][0]>last;last=rows[1][0]
 assert phase[-1]['stage']=='shared_world_overlay_suite' and phase[-1]['state']=='returned'
 assert all(e['phase'][key] for key in ('nvrtc_compile_returned_success','cuda_launch_returned_success','cuda_synchronize_returned_success','cuda_readback_returned_success'))
 names=[f'windows-portable-world-v{version}-summary.json',f'portable-world-v{version}-execution.json',f'portable-cross-v{version}-receipt.json']
 result=dict(passed=True,source_commit=source,inputs=inputs,native_cases=native_cases,rejected_cases=rejected_cases,prior_world49_full_output_preserved=True,full_input_output_native_actual_source_generated_fingerprints_equal=True,cuda_elapsed_seconds=e['elapsed_seconds'],actual_cuda_executions=1,normal4682_execution_count=0,gpu_retry_count=0,cpu_preflight_gpu_calls=0,cpu_tests=cpu_tests,phase_events=50,residual_windows_verification_processes=0,original_windows_work_and_service_preserved=True,files={n:sha((ROOT/'research'/n).read_bytes()) for n in names},audit_gpu_executions=0,full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False)
 (ROOT/f'research/portable-world-v{version}-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');return result
