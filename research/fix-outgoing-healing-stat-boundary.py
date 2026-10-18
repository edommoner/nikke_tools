"""Freeze the initial arithmetic proofs, then reject fractional stat IDs."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
reports=['research/detail-outgoing-healing-authored-native.json','research/detail-outgoing-healing-authored-ptx.json','research/detail-outgoing-healing-real-native.json','research/detail-outgoing-healing-regression-native.json','research/detail-outgoing-healing-boundary-verification.json']
files=set(reports)|{'research/fix-outgoing-healing-stat-boundary.py','research/detail-outgoing-healing-boundary-tests.log'}
for path in reports:
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert all(sha(p)==h for p,h in r['source_sha256'].items())
    assert r['passed']==('boundary' not in path)
    files.update(r['source_sha256'])
out=ROOT/'research/ports/v39-before-stat-boundary-fix';assert not out.exists()
for path in sorted(files):
    dest=(out/path).resolve();assert dest.is_relative_to(out.resolve());dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,dest)
(out/'archive-manifest.json').write_text(json.dumps(dict(objective_complete=False,gpu_arithmetic_mismatch=False,issue='Malformed fractional stat73.5 reached module boundary instead of rejection; no GPU executed for this negative test.',files={p:sha(p) for p in sorted(files)}),indent=2)+'\n',encoding='utf-8')
p=ROOT/'research/staging/v39/app/detail_gpu.py';s=p.read_text(encoding='utf-8');needle='or not 0<=r[2]<74:';assert s.count(needle)==1;s=s.replace(needle,'or int(r[2])!=r[2] or not 0<=r[2]<74:');p.write_text(s,encoding='utf-8')
print('Preserved initial arithmetic proofs; fractional stat IDs now rejected before CUDA.')
