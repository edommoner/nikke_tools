"""CPU-only audit of one bounded CUDA146 proof imported from existing connection."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='6c8aaa5a10e9baf86397675f18c3651977775c2c'
def load(name):return json.loads((ROOT/'research'/name).read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def blob(path):return subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT)
def main():
 s=load('windows-portable-world-v81-summary.json');e=load('portable-world-v81-execution.json');r=load('portable-cross-v81-receipt.json');expected=load('portable-world-cleanse-expected.json')
 assert s['passed'] and s['backend']=='cuda' and s['source_commit']==r['source_commit']==SOURCE
 assert s['comparison']==expected['comparison'] and s['changed_keys']==[] and s['expected_sha256']==sha(blob('research/portable-world-cleanse-expected.json'))
 assert e['passed'] and not e['timed_out'] and e['child_exit_code']==e['final_child_exit_code']==0 and e['error'] is None and e['cleanup_error'] is None and e['below_normal_priority'] and e['timeout_seconds']==180 and e['cleanup_wait_seconds']==5 and e['elapsed_seconds']<180
 assert e['gpu_retry_count']==r['gpu_retry_count']==r['normal4682_execution_count']==0 and r['actual_gpu_execution_count']==1
 assert r['passed'] and r['original_head_equal'] and r['original_status_equal'] and r['existing_gpu_service_preserved'] and r['residual_verification_process_count']==0
 pre=r['cpu_preflight'];assert pre['passed'] and pre['source_unchanged'] and pre['cpu_only'] and pre['job_object_descendants_verified'] and pre['cpu_tests']['exit_code']==0 and 'Ran 5 tests' in pre['cpu_tests']['stderr'] and pre['gpu_sentinel_call_count']==0 and pre['gpu_sentinel_calls']==[]
 assert pre['case_counts']==[9,26,35] and pre['total_inputs']==146 and pre['rejections']==27 and pre['prior_inputs']==49 and pre['input_sha256']==s['comparison']['input_sha256']==pre['expected_input_sha256']
 manifest=r['manifest'];assert manifest['source_commit']==SOURCE and manifest['inputs']==146 and not manifest['normal4682_repeated']
 for path,h in manifest['files'].items():assert sha(blob(path))==h
 for path,h in s['comparison']['source_sha256'].items():assert sha(blob(path))==h
 phase=r['phase_rows'];assert len(phase)==e['phase']['events']==50 and all(a['monotonic_ns']<=b['monotonic_ns'] for a,b in zip(phase,phase[1:]))
 last=-1
 for stage in ('nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):
  rows=[(i,x) for i,x in enumerate(phase) if x['stage']==stage];assert len(rows)==2 and rows[0][1]['state']=='entered' and rows[1][1]['state']=='returned' and rows[1][1]['return_code']==0 and rows[0][0]>last;last=rows[1][0]
 assert all(e['phase'][key] for key in ('nvrtc_compile_returned_success','cuda_launch_returned_success','cuda_synchronize_returned_success','cuda_readback_returned_success'))
 result=dict(passed=True,source_commit=SOURCE,inputs=146,native_cases=70,rejected_cases=27,prior_world49_full_output_preserved=True,full_input_output_native_actual_source_generated_fingerprints_equal=True,cuda_elapsed_seconds=e['elapsed_seconds'],actual_cuda_executions=1,normal4682_execution_count=0,gpu_retry_count=0,cpu_preflight_gpu_calls=0,phase_events=50,residual_windows_verification_processes=0,original_windows_work_and_service_preserved=True,files={n:sha((ROOT/'research'/n).read_bytes()) for n in ('windows-portable-world-v81-summary.json','portable-world-v81-execution.json','portable-cross-v81-receipt.json')},audit_gpu_executions=0,full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False)
 (ROOT/'research/portable-world-v81-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA146 sealed:complete fingerprints match Metal;one execution;normal4682 not rerun')
if __name__=='__main__':main()
