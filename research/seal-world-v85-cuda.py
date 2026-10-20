"""CPU-only seal:Windows CUDA67 versus composed Metal424 state projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='c9ecd4d28b67c4638d63cff4e5067ee8384472b8'
def main():
 result=audit(version=85,source=SOURCE,expected_file='portable-world-actor-state-short-expected.json',inputs=67,native_oracles=49,test_counts=[('test_portable_phase_audit.py',5),('test_portable_actor_state_input.py',9)],phase_suite='shared_world_actor_state_short',old_replays=['normal4682','old208','old285','old357'],payload_files=26,payload_bytes=314913,single_suite_replay_names=['old285','old357'],single_suite_command='python research/verify-world-actor-state-short.py --backend cuda')
 result.update(complete_native_battles=49,raw_rejections=18)
 (ROOT/'research/portable-world-v85-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA67 audited through shared typed proof auditor;GPU calls0')
if __name__=='__main__':main()
