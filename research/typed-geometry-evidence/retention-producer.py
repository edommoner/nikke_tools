import hashlib,json
from pathlib import Path
old=Path('/tmp/nikke-coordinate-typed-final-v1')
new=Path('/tmp/nikke-typed-geometry-develop-v1')
before=json.loads((old/'gpu-package.json').read_text())
after=json.loads((new/'gpu-package.json').read_text())
for a,b in zip(before['golden']['entries'],after['golden']['entries'][:10],strict=True):
    assert {k:v for k,v in a.items() if k!='output_sha256'}==b,(a.get('name'),b.get('name'))
size=10*2032000*4
paths=[Path('/tmp/nikke-coordinate-typed-metal-v3/readback.bin'),Path('/tmp/nikke-typed-geometry-metal-v1/readback.bin')]
digests=[]
for p in paths:
    h=hashlib.sha256();left=size
    with p.open('rb') as f:
        while left:
            b=f.read(min(left,1024*1024));assert b;h.update(b);left-=len(b)
    digests.append(h.hexdigest())
assert digests[0]==digests[1]
r=dict(schema=1,scope='Old ten exact input/native fingerprints and every output byte retained inside new 28-input batch',old_package_id=before['package_id'],new_package_id=after['package_id'],old_cases=10,output_prefix_bytes=size,sha256=digests[0],all_input_native_fingerprints_exact=True,all_output_bytes_exact=True,gpu_calls=0)
Path('/tmp/nikke-typed-geometry-retention-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
