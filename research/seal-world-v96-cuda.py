"""CPU-only seal: CUDA45 versus frozen Metal923 periodic projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='4554b0b61ce98375deee8aedeb262729915e3e0f'
def main():
 result=audit(version=96,source=SOURCE,expected_file='portable-world-periodic-short-expected.json',inputs=45,native_oracles=32,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8),('test_portable_counter_landings.py',5),('test_portable_counter_context.py',5),('test_portable_counter_fields.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_world_skills.py',7),('test_portable_world_skill_formulas.py',3),('test_portable_world_pending.py',6),('test_portable_actor_recipient_input.py',8),('test_portable_world_periodic.py',9)],phase_suite='shared_world_periodic_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833','old841','old878'],payload_files=21,payload_bytes=346136,single_suite_command='python research/verify-world-periodic-short.py --backend cuda')
 result.update(full_native_battles=32,raw_rejections=13,output_words=655360,input_words=97464,typed_target_child_conditions=True,typed_enemy_field_children=True,typed_direct_damage_children=True,context_mode=11,private_dispatch_work_limit=16384)
 (ROOT/'research/portable-world-v96-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA45 immutable periodic snapshots audited against Metal;GPU0')
if __name__=='__main__':main()
