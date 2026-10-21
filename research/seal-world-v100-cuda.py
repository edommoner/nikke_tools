"""CPU-only seal: CUDA47 versus frozen Metal47 team hit bridge."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='a61136f1db638b7cd16f5174b08fa13dffbe0bb1'
def main():
 result=audit(version=100,source=SOURCE,expected_file='portable-world-team-short-expected.json',inputs=47,native_oracles=29,test_counts=[('test_portable_phase_audit.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_actor_recipient_input.py',8),('test_portable_world_periodic.py',9),('test_portable_world_enemy_attack.py',10),('test_portable_world_spawn.py',11),('test_portable_world_fraction.py',13),('test_portable_world_team.py',18)],phase_suite='shared_world_team_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833','old841','old878','old923','old958'],payload_files=23,payload_bytes=387656,single_suite_command='python research/verify-world-team-short.py --backend cuda')
 result.update(full_native_battles=29,raw_rejections=18,output_words=655360,input_words=98000,context_mode=19,abi='0x50455689',team_part_body_notifications_common=True,source_owner_predicates_and_actual_attacker_activation=True,shared_team_counter_budget_and_probability=True,exact_static_post_fire_delay_preserved=True)
 (ROOT/'research/portable-world-v100-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA47 team inputs/native29/ownership/shared counters audited against Metal;GPU0')
if __name__=='__main__':main()
