"""Immutable final source/report closure for production v39."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();checkpoint='research/detail-outgoing-healing-checkpoint.json';r=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'));assert r['passed'] and not r['objective_complete'];assert all(sha(p)==h for p,h in r['source_sha256'].items())
closure=set(r['source_sha256'])|{checkpoint,'research/detail-expansion-next.json','research/archive-outgoing-healing-v39.py','research/finalize-outgoing-healing-docs.py','research/promote-outgoing-healing-v39.py','research/detail-outgoing-healing-production-tests.log','research/detail-outgoing-healing-api-verification.log','research/detail-outgoing-healing-coverage.log','research/record-outgoing-healing-browser-proof.py','research/prepare-outgoing-healing-ui-fixture.py','research/verify-outgoing-healing-backend.py'}
stage=r['staging_archive'];m=json.loads((ROOT/stage/'archive-manifest.json').read_text(encoding='utf-8'));assert all(sha(stage+'/'+p)==h for p,h in m['files'].items());closure.update(stage+'/'+p for p in m['files'])
out=ROOT/'research/ports/v39-final';assert not out.exists(),'Archives are immutable.';hashes={p:sha(p) for p in sorted(closure)}
for p in sorted(closure):
    dest=(out/p).resolve();assert dest.is_relative_to(out.resolve());dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dest)
assert all(hashlib.sha256((out/p).read_bytes()).hexdigest()==h for p,h in hashes.items());(out/'archive-manifest.json').write_text(json.dumps(dict(abi=r['abi'],objective_complete=False,passed=True,files=hashes),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(archive='research/ports/v39-final',files=len(hashes),objective_complete=False)))
