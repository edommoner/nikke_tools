"""CPU-only seal: CUDA50 versus frozen Metal833 direct-skill projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='9c34a5f1a4542811385ac3f6160087c3ef39b29e'
def main():
 result=audit(version=93,source=SOURCE,expected_file='portable-world-skill-short-expected.json',inputs=50,native_oracles=40,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8),('test_portable_counter_landings.py',5),('test_portable_counter_context.py',5),('test_portable_counter_fields.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_world_skills.py',7)],phase_suite='shared_world_skill_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783'],payload_files=23,payload_bytes=356917,single_suite_command='python research/verify-world-skill-short.py --backend cuda')
 result.update(full_native_battles=40,raw_rejections=10,output_words=524288,input_words=97464,typed_target_child_conditions=True,typed_enemy_field_children=True,typed_direct_damage_children=True,context_mode=7,private_dispatch_work_limit=16384)
 (ROOT/'research/portable-world-v93-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA50 direct skill receipts audited against Metal;GPU0')
if __name__=='__main__':main()
