"""Immutable final code/evidence closure for v40, with the full goal unfinished."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();checkpoint='research/detail-healing-storage-checkpoint.json';r=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'));assert r['passed'] and not r['objective_complete'] and all(sha(p)==h for p,h in r['source_sha256'].items())
closure=set(r['source_sha256'])|{checkpoint,'research/detail-expansion-next.json','research/archive-healing-storage-v40.py','research/finalize-healing-storage-docs.py','research/promote-healing-storage-v40.py','research/detail-healing-storage-production-tests.log','research/detail-healing-storage-api-verification.log','research/detail-healing-storage-coverage.log','research/record-healing-storage-browser-proof.py','research/prepare-healing-storage-ui-fixture.py','research/verify-healing-storage-backend.py'}
stage=r['staging_archive'];m=json.loads((ROOT/stage/'archive-manifest.json').read_text(encoding='utf-8'));assert all(sha(stage+'/'+p)==h for p,h in m['files'].items());closure.update(stage+'/'+p for p in m['files'])
out=ROOT/'research/ports/v40-final';assert not out.exists(),'Archives are immutable.';hashes={p:sha(p) for p in sorted(closure)}
for p in sorted(closure):
    dest=(out/p).resolve();assert dest.is_relative_to(out.resolve());dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dest)
assert all(hashlib.sha256((out/p).read_bytes()).hexdigest()==h for p,h in hashes.items());(out/'archive-manifest.json').write_text(json.dumps(dict(abi=r['abi'],objective_complete=False,passed=True,files=hashes),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(archive='research/ports/v40-final',files=len(hashes),objective_complete=False)))
