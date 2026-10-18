"""Immutable closure of the final v36 production and staged evidence."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
checkpoint='research/detail-survival-scaling-checkpoint.json';r=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'));assert r['passed'] and not r['objective_complete']
assert all(sha(p)==h for p,h in r['source_sha256'].items())
closure=set(r['source_sha256'])|{checkpoint,'research/detail-expansion-next.json','research/archive-survival-scaling-v36.py','research/finalize-survival-scaling-docs.py','research/detail-survival-scaling-normal-tests.log','research/detail-survival-scaling-normal-tail-tests.log','research/detail-survival-scaling-normal-tail-verification.json','research/promote-survival-scaling-v36.py','research/detail-survival-scaling-api-verification.log','research/detail-survival-scaling-coverage.log','research/record-survival-scaling-browser-proof.py'}
stage=r['staging_archive'];manifest=json.loads((ROOT/stage/'archive-manifest.json').read_text(encoding='utf-8'))
assert all(sha(stage+'/'+p)==h for p,h in manifest['files'].items())
closure.update(stage+'/'+p for p in manifest['files'])
prefix='research/ports/v36-production-before-test-wrapper-fix';old=json.loads((ROOT/prefix/'archive-manifest.json').read_text(encoding='utf-8'))
assert all(sha(prefix+'/'+p)==h for p,h in old['files'].items())
closure.update(prefix+'/'+p for p in old['files'])
target=ROOT/'research/ports/v36-final';assert not target.exists(),'Archives are immutable.'
hashes={p:sha(p) for p in sorted(closure)}
for p in sorted(closure):
    out=(target/p).resolve();assert out.is_relative_to(target.resolve());out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
assert all(hashlib.sha256((target/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(target/'archive-manifest.json').write_text(json.dumps(dict(abi=r['abi'],objective_complete=False,passed=True,files=hashes),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(archive='research/ports/v36-final',files=len(hashes),objective_complete=False)))
