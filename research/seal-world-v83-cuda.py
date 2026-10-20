"""CPU-only seal:Windows CUDA77 versus frozen Metal285 projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='ea1f8ddee06cc7c995307d5e110a60b6c696893c'
def main():
 result=audit(version=83,source=SOURCE,expected_file='portable-world-actor-pools-short-expected.json',inputs=77,native_oracles=36,test_counts=[('test_portable_phase_audit.py',5),('test_portable_actor_registry_input.py',4),('test_portable_actor_pool_input.py',6)],phase_suite='shared_world_actor_pools_short',old_replays=['normal4682','old208'],payload_files=24,payload_bytes=301900)
 result.update(complete_native_battles=14,typed_pool_set_cases=10,registry_native_cases=12,raw_rejections=41)
 (ROOT/'research/portable-world-v83-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA77 audited through shared typed proof auditor;GPU calls0')
if __name__=='__main__':main()
