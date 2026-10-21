"""CPU-only seal: CUDA37 versus frozen Metal37 enemy attack fields."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='970aed0d7921de429c3808ec73a7115b0dcd2386'
def main():
 result=audit(version=97,source=SOURCE,expected_file='portable-world-enemy-attack-short-expected.json',inputs=37,native_oracles=28,test_counts=[('test_portable_phase_audit.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_actor_recipient_input.py',8),('test_portable_world_periodic.py',9),('test_portable_world_enemy_attack.py',10)],phase_suite='shared_world_enemy_attack_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833','old841','old878','old923'],payload_files=16,payload_bytes=252144,single_suite_command='python research/verify-world-enemy-attack-short.py --backend cuda')
 result.update(full_native_battles=28,raw_rejections=9,output_words=655360,input_words=97464,context_mode=13,abi='0x50455685',enemy_attack_flat_and_percent_common=True,incoming_attack_frozen_before_victims=True)
 (ROOT/'research/portable-world-v97-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA37 enemy attack inputs/native28 audited against Metal;GPU0')
if __name__=='__main__':main()
