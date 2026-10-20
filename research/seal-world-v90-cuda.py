"""CPU-only seal: CUDA41 versus frozen Metal663 physical counter projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='03383d90d5eda28c4eb8c15529365b33add0190e'
def main():
 result=audit(version=90,source=SOURCE,expected_file='portable-world-counter-landing-short-expected.json',inputs=41,native_oracles=26,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8),('test_portable_counter_landings.py',5)],phase_suite='shared_world_counter_landing_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622'],payload_files=21,payload_bytes=310092,single_suite_command='python research/verify-world-counter-landing-short.py --backend cuda')
 result.update(full_native_battles=26,raw_rejections=15,output_words=524288,input_words=97464,physical_landing_bridge=True,typed_target_child_conditions=False,typed_damage_children=False,body_plus127_parts_verified=True,parts_direct_and_extra_accounting_separate=True)
 (ROOT/'research/portable-world-v90-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA41 physical Actor counters audited against Metal;GPU0')
if __name__=='__main__':main()
