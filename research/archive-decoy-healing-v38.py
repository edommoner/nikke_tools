"""Immutable final current source/report closure for v38."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();checkpoint='research/detail-decoy-healing-checkpoint.json';r=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'));assert r['passed'] and not r['objective_complete'];assert all(sha(p)==h for p,h in r['source_sha256'].items())
closure=set(r['source_sha256'])|{checkpoint,'research/detail-expansion-next.json','research/archive-decoy-healing-v38.py','research/finalize-decoy-healing-docs.py','research/promote-decoy-healing-v38.py','research/detail-decoy-healing-production-tests.log','research/detail-decoy-healing-api-verification.log','research/detail-decoy-healing-coverage.log','research/record-decoy-healing-browser-proof.py'}
stage=r['staging_archive'];m=json.loads((ROOT/stage/'archive-manifest.json').read_text(encoding='utf-8'));assert all(sha(stage+'/'+p)==h for p,h in m['files'].items());closure.update(stage+'/'+p for p in m['files'])
out=ROOT/'research/ports/v38-final';assert not out.exists(),'Archives are immutable.';hashes={p:sha(p) for p in sorted(closure)}
for p in sorted(closure):
    dest=(out/p).resolve();assert dest.is_relative_to(out.resolve());dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dest)
assert all(hashlib.sha256((out/p).read_bytes()).hexdigest()==h for p,h in hashes.items());(out/'archive-manifest.json').write_text(json.dumps(dict(abi=r['abi'],objective_complete=False,passed=True,files=hashes),indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(archive='research/ports/v38-final',files=len(hashes),objective_complete=False)))
