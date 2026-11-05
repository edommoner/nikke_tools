"""Verify old bytes through the real new-stride dispatch (ABI word only changes)."""
import hashlib, importlib.util, json, struct, subprocess, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
import portable_runtime
s=importlib.util.spec_from_file_location('foundation_verifier',R/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
old=json.loads(subprocess.check_output(['git','show','97e47b2:research/portable-combat-metal.json'],cwd=R))
assert [c['name'] for c in v.fixtures()]==[c['name'] for c in old['cases']]
original=portable_runtime.execute
calls=0
def execute(source,entry,packed,input_words,output_words,backend):
 global calls
 calls+=1;assert calls==1 and source=='gpu/event_runtime.slang'
 count,=struct.unpack_from('<I',packed);assert count==1355 and input_words==77824 and output_words==94208
 h=hashlib.sha256(packed[:4])
 for i in range(count):
  b=4+i*input_words*4;assert struct.unpack_from('<I',packed,b)[0]==0x50455661
  h.update(struct.pack('<I',0x50455660));h.update(memoryview(packed)[b+4:b+input_words*4])
 assert h.hexdigest()==old['input_sha256']
 raw,evidence=original(source,entry,packed,input_words,output_words,backend)
 o=hashlib.sha256();view=memoryview(raw)
 for i in range(count):
  b=i*output_words*4;o.update(view[b:b+90112*4]);assert not any(view[b+90112*4:b+output_words*4])
 assert o.hexdigest()==old['output_sha256']
 result=dict(passed=True,previous_proof_commit='97e47b2',inputs=count,positives=1149,rejections=206,
  input_normalization='ABI word 0x50455661 to 0x50455660 only',all_prior_output_bytes_equal=True,
  added_output_tail_zero=True,no_output_normalization=True,prior_input_sha256=h.hexdigest(),prior_output_sha256=o.hexdigest(),
  cpu_trace_used_as_gpu_input=False,backend=backend,source_sha256=evidence['source_sha256'],input_sha256=evidence['input_sha256'],output_sha256=evidence['output_sha256'])
 (R/f'research/portable-stack-foundation-existing-{backend}-parity.json').write_text(json.dumps(result,indent=2)+'\n')
 return raw,evidence
portable_runtime.execute=execute
v.main();assert calls==1
