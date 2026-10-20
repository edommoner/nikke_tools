"""CPU-only seal:CUDA68 versus frozen Metal529/484 new status projections."""
import json
from portable_typed_cuda_proof_audit import ROOT,audit
SOURCE='f988d15ceb36f8715981afc69cbe77e92612138c'
def main():
 result=audit(version=87,source=SOURCE,expected_file='portable-world-actor-status-short-expected.json',inputs=68,native_oracles=56,test_counts=[('test_portable_phase_audit.py',5),('test_portable_actor_recipient_input.py',8),('test_portable_actor_status_input.py',8)],phase_suite='shared_world_actor_status_short',old_replays=['normal4682','old208','old285','old357','old424','old461','old484'],payload_files=29,payload_bytes=299952,single_suite_replay_names=['old285','old357','old424','old461','old484'],single_suite_command='python research/verify-world-actor-status-short.py --backend cuda',summary_omission_counts={'old484':484})
 result.update(complete_native_battles=56,raw_rejections=12,persistent_recipient_inputs=23,status_inputs=45,output_words=524288)
 (ROOT/'research/portable-world-v87-cuda-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('CUDA68 audited through shared typed proof auditor;GPU calls0')
if __name__=='__main__':main()
