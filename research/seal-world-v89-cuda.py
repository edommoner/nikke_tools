"""CPU-only seal:CUDA32 versus frozen Metal622 counter projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='61c7a884c3d687c486017d71e84e560d6b0a46e9'
def main():
 result=audit(version=89,source=SOURCE,expected_file='portable-world-target-counter-short-expected.json',inputs=32,native_oracles=10,test_counts=[('test_portable_phase_audit.py',5),('test_portable_target_counters.py',8)],phase_suite='shared_world_target_counter_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529','old590'],payload_files=13,payload_bytes=233071,single_suite_command='python research/verify-world-target-counter-short.py --backend cuda')
 result.update(native_literal_resource_cases=10,native_action_steps=48,raw_rejections=22,output_words=524288,input_words=97464,physical_landing_bridge=False,typed_target_child_conditions=False)
 (ROOT/'research/portable-world-v89-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA32 audited through shared typed proof auditor;GPU0')
if __name__=='__main__':main()
