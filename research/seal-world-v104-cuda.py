"""CPU-only seal: CUDA63 versus saved Metal63 physical projectile proofs."""
import hashlib,json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='def167197c840d63457ce139f5f6131ce78dc491'
def main():
 result=audit(version=104,source=SOURCE,expected_file='portable-world-projectile-short-expected.json',inputs=63,native_oracles=52,test_counts=[('test_portable_projectiles.py',13),('test_portable_real_binding_proof.py',3),('test_portable_windows_observer.py',11)],phase_suite='shared_world_projectile_short',old_replays=['normal4682','old1063','old_reload65','old_real22'],payload_files=26,payload_bytes=390810,single_suite_replay_names=['old1063','old_real22','old_reload65'],single_suite_command='python research/verify-world-projectile-short.py --backend cuda',preservation_diagnostic=True)
 result.update(full_native_battles=52,raw_rejections=11,output_words=786432,input_words=104400,context_mode=24,abi='0x5045568d',typed_projectile_modifiers=True,shared_resource_and_named_removal_admission=True)
 r=json.loads((ROOT/'research/portable-cross-v104-receipt.json').read_text());o=r['windows_observer'];gold=json.loads((ROOT/'research/portable-world-projectile-short-expected.json').read_text())
 def blob(path):return __import__('subprocess').check_output(['git','show',SOURCE+':'+path],cwd=ROOT)
 assert o['module_path']=='research/windows_validation_observer.py' and hashlib.sha256(blob(o['module_path'])).hexdigest()==o['module_sha256'] and o['command_lines_saved'] is False
 from windows_validation_observer import compare_snapshots
 assert hashlib.sha256((ROOT/o['module_path']).read_bytes()).hexdigest()==o['module_sha256']
 assert compare_snapshots(o['before'],o['after'])==o['comparison']
 for snap in (o['before'],o['after']):
  assert snap['command_lines_saved'] is False
  for process in snap['processes']:assert 'CommandLine' not in process and 'command_line' not in process
 def job_checked(records):
  assert records['schema']==1 and records['observer_assigns_processes'] is False and len(records['records'])==1
  record=records['records'][0];a=record['pre_gate'];b=record['post_wait'];pid=record['child_pid'];parent=record['wrapper_pid']
  assert record['pre_gate_verified'] and record['inspection_error'] is None and a['child_pid']==b['child_pid']==pid and a['child_ppid']==b['child_ppid']==parent and a['wrapper_pid']==b['wrapper_pid']==parent
  assert a['parent_observation']=='os_process_snapshot' and b['parent_observation'] in ('os_process_snapshot','pre_gate_snapshot_same_process_handle_after_exit')
  assert a['job_members']==[pid] and b['job_members']==[] and a['child_creation_filetime_ticks']==b['child_creation_filetime_ticks'] and a['observed_unix_ns']<=b['observed_unix_ns']
  assert int(a['child_creation_filetime_ticks'])>116444736000000000
  return record
 smoke=o['cpu_job_smoke'];f=smoke['facts'];assert f['passed'] and not f['timed_out'] and f['error'] is None and f['cleanup_error'] is None and f['child_exit_code']==f['final_child_exit_code']==0 and f['elapsed_seconds']<f['timeout_seconds']<=20 and f['phase']['events']==0
 sj=job_checked(smoke['job_records']);assert smoke['marker']==dict(pid=sj['child_pid'],ppid=sj['wrapper_pid'])
 mainjob=job_checked(o['production_job_records']);assert o['production_job_verified'] and {p['pid'] for p in r['phase_rows']}=={mainjob['child_pid']}
 assert mainjob['pre_gate']['observed_unix_ns']<=r['phase_rows'][0]['wall_time_ns']<=r['phase_rows'][-1]['wall_time_ns']<=mainjob['post_wait']['observed_unix_ns']
 launch=o['direct_base_launch'];assert launch['child_launcher_variable_removed'] and launch['venv_site_packages'] in launch['pythonpath'] and launch['base_executable'].lower().endswith('python.exe')
 assert o['base_import']['exit_code']==o['base_cpu_short']['exit_code']==0 and o['base_import']['stdout'].strip()==launch['base_executable']
 cpu=o['base_cpu_report'];assert cpu['passed'] and cpu['input_count']==63 and cpu['native_oracles']==52 and cpu['gpu_calls']==dict(build=0,execute=0) and cpu['input_sha256']==gold['input_sha256'] and cpu['source_sha256']==gold['source_sha256']
 gpu_before=o['gpu_before']
 assert compare_snapshots(o['before'],gpu_before)==o['cpu_window_comparison']
 assert compare_snapshots(gpu_before,o['after'])==o['gpu_window_comparison']
 assert o['before']['observed_unix_ns']<=gpu_before['observed_unix_ns']<=mainjob['pre_gate']['observed_unix_ns']
 result.update(cpu_window_missing=len(o['cpu_window_comparison']['missing_existing_processes']),gpu_window_missing=len(o['gpu_window_comparison']['missing_existing_processes']),three_process_snapshots_verified=True)
 assert o['after']['observed_unix_ns']>=mainjob['post_wait']['observed_unix_ns']
 lag=(o['after']['observed_unix_ns']-mainjob['post_wait']['observed_unix_ns'])/1e9
 window=(o['after']['observed_unix_ns']-gpu_before['observed_unix_ns'])/1e9
 result.update(post_snapshot_delay_after_job_seconds=lag,pre_gpu_to_after_snapshot_window_seconds=window,process_exit_during_gpu_execution_proven=False,post_snapshot_is_immediate=False)
 import base64
 control=r['cpu_only_control_original'];raw=base64.b64decode(control['data_base64'],validate=True)
 assert len(raw)==control['bytes'] and hashlib.sha256(raw).hexdigest()==control['sha256']
 c=json.loads(raw);assert c['gpu_calls']==c['job_calls']==c['service_operations']==0 and c['observer_sha256']==o['module_sha256'] and c['original_head_status_preserved']
 assert c['original_head_before']==c['original_head_after']=='61a43e91301841c272badce519e4d8984bb5efae' and c['original_status_before']==c['original_status_after']==[]
 assert compare_snapshots(c['before'],c['after'])==c['comparison']
 control_path=ROOT/'research/windows-portable-world-v104-cpu-control.json'
 if control_path.exists():assert control_path.read_bytes()==raw
 else:control_path.write_bytes(raw)
 result.update(cpu_only_control_original_sha256=control['sha256'],cpu_only_control_original_bytes=len(raw),cpu_only_control_missing=len(c['comparison']['missing_existing_processes']),cpu_only_control_gpu_calls=0,cpu_only_control_job_calls=0)

 missing=o['comparison']['missing_existing_processes']
 assert o['comparison']['all_monitored_processes_preserved']==(not missing)
 preservation=bool(o['comparison']['all_monitored_processes_preserved'] and o['comparison']['identified_nikke_service_preservation_verified'])
 assert r['existing_gpu_service_preserved']==result['preservation_verified']==preservation
 assert o['comparison']['termination_cause']==('unknown' if missing else None)
 assert all(p['pid']!=mainjob['child_pid'] and int(p['creation_filetime_ticks'])<int(mainjob['pre_gate']['child_creation_filetime_ticks']) for p in missing)
 result.update(actual_native_windows_cpu_job_verified=True,actual_gpu_job_pid=mainjob['child_pid'],actual_gpu_wrapper_pid=mainjob['wrapper_pid'],actual_gpu_job_members_before=[mainjob['child_pid']],actual_gpu_job_members_after=[],api50_pid_matches_contained_interpreter=True,read_only_observer_assigns_processes=False,command_lines_saved=False,direct_base_python_with_venv_sites_verified=True,base_cpu_oracle_verified_again=True,missing_existing_processes=len(missing),missing_processes_preexist_and_are_outside_validation_job=True,termination_cause=o['comparison']['termination_cause'],nikke_service_identity_preservation='verified' if o['comparison']['identified_nikke_service_preservation_verified'] else 'unverified',strict_environment_audit_passed=preservation,previous_v102_seven_missing_processes_cause='unresolved')
 assert result['passed']==preservation and result['calculation_verified']
 (ROOT/'research/portable-world-v104-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA63 calculation/native52/raw11 verified;environment preservation:',result['preservation_verified'],';GPU0')
if __name__=='__main__':main()
