"""CPU-only seal: CUDA27 versus frozen Metal27 initial/add notifications."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='a7f4b777845dee039f9d873df7eea272d4debf07'
def main():
 result=audit(version=98,source=SOURCE,expected_file='portable-world-spawn-short-expected.json',inputs=27,native_oracles=22,test_counts=[('test_portable_phase_audit.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_actor_recipient_input.py',8),('test_portable_world_periodic.py',9),('test_portable_world_enemy_attack.py',10),('test_portable_world_spawn.py',11)],phase_suite='shared_world_spawn_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833','old841','old878','old923'],payload_files=17,payload_bytes=280180,single_suite_command='python research/verify-world-spawn-short.py --backend cuda')
 result.update(full_native_battles=22,raw_rejections=5,output_words=655360,input_words=97464,context_mode=15,abi='0x50455686',initial_and_add_spawn_common=True,all640_notification_owners_and_times_exact=True,initial_magazine_and_wide_skill_dot_native_equal=True)
 (ROOT/'research/portable-world-v98-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA27 startup/add inputs/native22 audited against Metal;GPU0')
if __name__=='__main__':main()
