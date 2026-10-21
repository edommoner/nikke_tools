"""CPU-only seal: CUDA8 versus frozen Metal8 world formula projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='05a763db1d988ad9c82e5b14fcf4a49aa16430a0'
def main():
 result=audit(version=94,source=SOURCE,expected_file='portable-world-skill-formula-short-expected.json',inputs=8,native_oracles=8,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8),('test_portable_counter_landings.py',5),('test_portable_counter_context.py',5),('test_portable_counter_fields.py',5),('test_portable_enemy_query_scope.py',4),('test_portable_world_skills.py',7),('test_portable_world_skill_formulas.py',3)],phase_suite='shared_world_skill_formula_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663','old721','old783','old833'],payload_files=6,payload_bytes=89510,single_suite_command='python research/verify-world-skill-formula-short.py --backend cuda')
 result.update(full_native_battles=8,raw_rejections=0,output_words=524288,input_words=97464,typed_target_child_conditions=True,typed_enemy_field_children=True,typed_direct_damage_children=True,context_mode=7,private_dispatch_work_limit=16384)
 (ROOT/'research/portable-world-v94-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA8 world formula audited against Metal;GPU0')
if __name__=='__main__':main()
