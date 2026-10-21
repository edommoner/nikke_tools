"""CPU-only seal: CUDA58 versus frozen Metal58 manual charge controls."""
import hashlib,json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='784762d0f9cb809958107c040dcac7c219889c4c'
def main():
 result=audit(version=101,source=SOURCE,expected_file='portable-world-charge-control-short-expected.json',inputs=58,native_oracles=31,test_counts=[('test_portable_phase_audit.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_actor_recipient_input.py',8),('test_portable_world_periodic.py',9),('test_portable_world_enemy_attack.py',10),('test_portable_world_spawn.py',11),('test_portable_world_fraction.py',13),('test_portable_world_team.py',18),('test_portable_charge_control.py',28)],phase_suite='shared_world_charge_control_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833','old841','old878','old923','old958','old1005'],payload_files=22,payload_bytes=341461,single_suite_command='python research/verify-world-charge-control-short.py --backend cuda',preservation_diagnostic=True)
 result.update(full_native_battles=31,raw_rejections=27,output_words=655360,input_words=104136,context_mode=21,abi='0x5045568a',typed_manual_charge_hold=True,latched_full_charge_and_one_notification_per_raw_threshold=True,dynamic_camera_and_hold_preemption=True,physical_mode_restore_after_arbitration=True)
 follow=(ROOT/'research/portable-world-v101-process-followup.json').read_bytes();details=json.loads(follow)
 assert len(follow)==12543 and hashlib.sha256(follow).hexdigest()=='fdc5e84782c4d176a95b40f3fd72c253726ffe30a0316b79e5a26b3959142669' and details['source_commit']==SOURCE and details['gpu_execution_in_this_followup']==0
 for path,h in details['original_three_json_sha256_unchanged'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
 assert hashlib.sha256((ROOT/details['containment_review']['source_file']).read_bytes()).hexdigest()==details['containment_review']['source_sha256']
 receipt=json.loads((ROOT/'research/portable-cross-v101-receipt.json').read_text());assert details['containment_review']['wrapper_sha256']==receipt['bounded_driver']['sha256'] and len(details['missing_processes'])==7
 assert details['conclusions']['missing_seven_exit_cause']=='unknown' and details['nikke_gpu_service']['after_same_process_confirmed'] is None
 result.update(readonly_followup_bytes=12543,missing_existing_processes=7,termination_cause='unknown',nikke_service_identity_preservation='unverified',verification_job_external_assignment_evidence=False,strict_environment_audit_passed=False)
 assert result['calculation_verified'] and result['passed'] is False and result['preservation_verified'] is False
 (ROOT/'research/portable-world-v101-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA58 calculation/native31/raw27 verified;environment preservation:',result['preservation_verified'],';GPU0')
if __name__=='__main__':main()
