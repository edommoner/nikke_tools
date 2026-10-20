"""CPU-only seal: CUDA58 versus frozen Metal721 completion-context projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='a9bb64216cce80e813a4a18e524f8b178ba6cc2c'
def main():
 result=audit(version=91,source=SOURCE,expected_file='portable-world-counter-context-short-expected.json',inputs=58,native_oracles=49,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8),('test_portable_counter_landings.py',5),('test_portable_counter_context.py',5)],phase_suite='shared_world_counter_context_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590','old622','old663'],payload_files=16,payload_bytes=250508,single_suite_command='python research/verify-world-counter-context-short.py --backend cuda')
 result.update(full_native_battles=49,raw_rejections=9,output_words=524288,input_words=97464,typed_target_child_conditions=True,typed_damage_children=False,context_mode=3,generic_named_child_clears_context=True,finite_latch_and_permanent_recheck=True)
 (ROOT/'research/portable-world-v91-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA58 typed completion contexts audited against Metal;GPU0')
if __name__=='__main__':main()
