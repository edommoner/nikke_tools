import json
from pathlib import Path
load=lambda p:json.loads(Path(p).read_text())
a=load('/tmp/nikke-typed-aim-gpu-develop-v2/gpu-package.json');b=load('/tmp/nikke-typed-aim-gpu-develop-v3/gpu-package.json')
old=a['golden']['entries'];new=b['golden']['entries'];assert len(old)==len(new)==59
assert all(x['name']==y['name'] and x['native_sha256']==y['native_sha256'] for x,y in zip(old,new,strict=True))
inputs=[i for i,(x,y) in enumerate(zip(old,new,strict=True)) if x['input_sha256']!=y['input_sha256']];assert inputs==[52]
with Path('/tmp/nikke-typed-aim-metal-v2/readback.bin').open('rb') as x,Path('/tmp/nikke-typed-aim-metal-v3/readback.bin').open('rb') as y:
 changed=[]
 for i in range(59):
  before=x.read(2032000*4);after=y.read(2032000*4);assert len(before)==len(after)==2032000*4
  if before!=after:changed.append(i)
 assert not x.read(1) and not y.read(1)
assert changed==[50],changed
r=dict(first_package=a['package_id'],fixed_package=b['package_id'],inputs=59,changed_raw_indices=changed,unchanged_raw_cases=58,all59_native_fingerprints_exact=True,changed_input_indices=inputs,gpu_calls=0)
Path('/tmp/nikke-typed-aim-fix-retention-v1.json').write_text(json.dumps(r,indent=2)+'\n')
