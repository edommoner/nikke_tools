"""CPU-only seal: CUDA37 versus frozen Metal878 pending projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='ea1eccc0e23d22f7cfede3437fd76dedf6dec0fe'
def main():
 result=audit(version=95,source=SOURCE,expected_file='portable-world-pending-short-expected.json',inputs=37,native_oracles=26,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8),('test_portable_counter_landings.py',5),('test_portable_counter_context.py',5),('test_portable_counter_fields.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_world_skills.py',7),('test_portable_world_skill_formulas.py',3),('test_portable_world_pending.py',6)],phase_suite='shared_world_pending_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833','old841'],payload_files=15,payload_bytes=297084,single_suite_command='python research/verify-world-pending-short.py --backend cuda')
 result.update(full_native_battles=26,raw_rejections=11,output_words=524288,input_words=97464,typed_target_child_conditions=True,typed_enemy_field_children=True,typed_direct_damage_children=True,context_mode=9,private_dispatch_work_limit=16384)
 (ROOT/'research/portable-world-v95-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA37 pending Actor batches audited against Metal;GPU0')
if __name__=='__main__':main()
