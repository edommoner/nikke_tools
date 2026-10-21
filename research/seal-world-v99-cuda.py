"""CPU-only seal: CUDA35 versus frozen Metal35 fractions and exact delays."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='158e8b7a81e0af470af7cfe06e5d8809b48690ba'
def main():
 result=audit(version=99,source=SOURCE,expected_file='portable-world-fraction-short-expected.json',inputs=35,native_oracles=24,test_counts=[('test_portable_phase_audit.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_actor_recipient_input.py',8),('test_portable_world_periodic.py',9),('test_portable_world_enemy_attack.py',10),('test_portable_world_spawn.py',11),('test_portable_world_fraction.py',13)],phase_suite='shared_world_fraction_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833','old841','old878','old923'],payload_files=19,payload_bytes=293289,single_suite_command='python research/verify-world-fraction-short.py --backend cuda')
 result.update(full_native_battles=24,raw_rejections=11,output_words=655360,input_words=97480,context_mode=17,abi='0x50455688',critical_core_fractional_notifications_common=True,exact_static_post_fire_delay_preserved=True)
 (ROOT/'research/portable-world-v99-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA35 fractional inputs/native24/exact clocks audited against Metal;GPU0')
if __name__=='__main__':main()
