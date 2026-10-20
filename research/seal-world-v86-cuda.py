"""CPU-only seal:Windows CUDA37 versus Metal461 named-removal projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='4271202f6b39e7c27b6de250141b506178ecd1b0'
def main():
 result=audit(version=86,source=SOURCE,expected_file='portable-world-actor-mutation-short-expected.json',inputs=37,native_oracles=30,test_counts=[('test_portable_phase_audit.py',5),('test_portable_actor_mutation_input.py',8)],phase_suite='shared_world_actor_mutation_short',old_replays=['normal4682','old208','old285','old357','old424'],payload_files=17,payload_bytes=279509,single_suite_replay_names=['old285','old357','old424'],single_suite_command='python research/verify-world-actor-mutation-short.py --backend cuda')
 result.update(complete_native_battles=30,raw_rejections=7)
 (ROOT/'research/portable-world-v86-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA37 audited through shared typed proof auditor;GPU calls0')
if __name__=='__main__':main()
