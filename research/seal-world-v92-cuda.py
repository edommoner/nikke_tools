"""CPU-only seal: CUDA62 versus frozen Metal783 counter-field projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='9152a2a52b89cb8d3b77a94a619101a31d6942e8'
def main():
 result=audit(version=92,source=SOURCE,expected_file='portable-world-counter-field-short-expected.json',inputs=62,native_oracles=52,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8),('test_portable_counter_landings.py',5),('test_portable_counter_context.py',5),('test_portable_counter_fields.py',5)],phase_suite='shared_world_counter_field_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721'],payload_files=15,payload_bytes=234843,single_suite_command='python research/verify-world-counter-field-short.py --backend cuda')
 result.update(full_native_battles=52,raw_rejections=10,output_words=524288,input_words=97464,typed_target_child_conditions=True,typed_enemy_field_children=True,typed_damage_children=False,context_mode=5,private_dispatch_work_limit=16384,field128_maximum_dispatch_work=4106)
 (ROOT/'research/portable-world-v92-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA62 captured counter fields audited against Metal;GPU0')
if __name__=='__main__':main()
