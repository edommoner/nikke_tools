"""CPU-only seal:CUDA61 versus frozen Metal590 typed stack projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='a106e1e69de91888abe3c175029f13028a616e1c'
def main():
 result=audit(version=88,source=SOURCE,expected_file='portable-world-actor-stack-short-expected.json',inputs=61,native_oracles=53,test_counts=[('test_portable_phase_audit.py',5),('test_portable_actor_stack_input.py',8)],phase_suite='shared_world_actor_stack_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484','old529'],payload_files=16,payload_bytes=226799,single_suite_replay_names=['old285','old357','old424','old461','old484','old529'],single_suite_command='python research/verify-world-actor-stack-short.py --backend cuda')
 result.update(complete_native_battles=53,raw_rejections=8,numeric_storage_overflow_rejection_status=2,output_words=524288)
 (ROOT/'research/portable-world-v88-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA61 audited through shared typed proof auditor;GPU calls0')
if __name__=='__main__':main()
