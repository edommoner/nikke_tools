"""CPU-only seal: CUDA10 versus frozen Metal10 complete real rosters."""
import hashlib,json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='767f4f4274b5840da44cc48687572580f030d07a'
def main():
 result=audit(version=103,source=SOURCE,expected_file='portable-world-roster-short-expected.json',inputs=10,native_oracles=6,test_counts=[('test_portable_world_roster_input.py',6),('test_portable_windows_observer.py',11)],phase_suite='shared_world_roster_short',old_replays=['normal4682','previous_world1063','previous_reload65'],payload_files=12,payload_bytes=238622,single_suite_replay_names=['previous_world1063','previous_reload65'],single_suite_command='python research/verify-world-roster-short.py --backend cuda',preservation_diagnostic=True,cpu_gpu_calls_format='scalar')
 result.update(full_native_battles=6,raw_rejections=4,output_words=786432,input_words=104400,context_mode=23,abi='0x5045568c',complete_real_roster_input=True,diagnostic_history_omissions_explicit=True)
 r=json.loads((ROOT/'research/portable-cross-v103-receipt.json').read_text());o=r['windows_observer'];gold=json.loads((ROOT/'research/portable-world-roster-short-expected.json').read_text())
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
 cpu=o['base_cpu_report'];assert cpu['passed'] and cpu['input_count']==10 and cpu['native_oracles']==6 and type(cpu['gpu_calls']) is int and cpu['gpu_calls']==0 and cpu['input_sha256']==gold['input_sha256'] and cpu['source_sha256']==gold['source_sha256']
 missing=o['comparison']['missing_existing_processes']
 assert o['comparison']['all_monitored_processes_preserved']==(not missing)
 preservation=bool(o['comparison']['all_monitored_processes_preserved'] and o['comparison']['identified_nikke_service_preservation_verified'])
 assert r['existing_gpu_service_preserved']==result['preservation_verified']==preservation
 assert o['comparison']['termination_cause']==('unknown' if missing else None)
 assert all(p['pid']!=mainjob['child_pid'] and int(p['creation_filetime_ticks'])<int(mainjob['pre_gate']['child_creation_filetime_ticks']) for p in missing)
 result.update(actual_native_windows_cpu_job_verified=True,actual_gpu_job_pid=mainjob['child_pid'],actual_gpu_wrapper_pid=mainjob['wrapper_pid'],actual_gpu_job_members_before=[mainjob['child_pid']],actual_gpu_job_members_after=[],api50_pid_matches_contained_interpreter=True,read_only_observer_assigns_processes=False,command_lines_saved=False,direct_base_python_with_venv_sites_verified=True,base_cpu_oracle_verified_again=True,missing_existing_processes=len(missing),missing_processes_preexist_and_are_outside_validation_job=True,termination_cause=o['comparison']['termination_cause'],nikke_service_identity_preservation='verified' if o['comparison']['identified_nikke_service_preservation_verified'] else 'unverified',strict_environment_audit_passed=preservation,previous_v102_seven_missing_processes_cause='unresolved')
 assert result['passed']==preservation and result['calculation_verified']
 (ROOT/'research/portable-world-v103-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA10 calculation/real-native6/raw4 verified;environment preservation:',result['preservation_verified'],';GPU0')
if __name__=='__main__':main()
