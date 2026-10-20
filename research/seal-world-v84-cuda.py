"""CPU-only seal:Windows CUDA72 versus frozen Metal357 projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='8be669df1cac6e349bc676b73792b62386ac795d'
def main():
 result=audit(version=84,source=SOURCE,expected_file='portable-world-actor-fields-short-expected.json',inputs=72,native_oracles=52,test_counts=[('test_portable_phase_audit.py',5),('test_portable_actor_field_input.py',6)],phase_suite='shared_world_actor_fields_short',old_replays=['normal4682','old208','old285'],payload_files=18,payload_bytes=250128,single_suite_replay_names=['old285'],single_suite_command='python research/verify-world-actor-fields-short.py --backend cuda')
 result.update(complete_native_battles=52,raw_rejections=20)
 (ROOT/'research/portable-world-v84-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA72 audited through shared typed proof auditor;GPU calls0')
if __name__=='__main__':main()
