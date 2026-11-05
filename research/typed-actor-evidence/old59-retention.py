import hashlib,json
from pathlib import Path
new=Path('/tmp/nikke-typed-actor-metal-v1');old=Path('/tmp/nikke-typed-aim-metal-v3')
a=json.loads(Path('/tmp/nikke-typed-actor-gpu-develop-v1/gpu-package.json').read_text());b=json.loads(Path('/tmp/nikke-typed-aim-final-v1/gpu-package.json').read_text())
for x,y in zip(a['golden']['entries'][:59],b['golden']['entries'],strict=True):assert x=={k:y[k] for k in x}
facts={}
for name,size in [('input.bin',59*115680*4),('readback.bin',59*2032000*4)]:
 with (new/name).open('rb') as x,(old/name).open('rb') as y:
  if name=='input.bin':assert int.from_bytes(x.read(4),'little')==67 and int.from_bytes(y.read(4),'little')==59
  remain=size;h=hashlib.sha256()
  while remain:
   n=min(remain,1024*1024);p=x.read(n);q=y.read(n);assert len(p)==n and p==q,(name,size-remain);h.update(p);remain-=n
  facts[name]=dict(bytes=size,sha256=h.hexdigest(),all_bytes_exact=True)
r=dict(old59_input_native_fingerprints_exact=True,payloads=facts,gpu_calls=0)
Path('/tmp/nikke-typed-actor-retain-old59-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
