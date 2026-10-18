"""Persist the observed normal UI result after the v30 preview restart."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'research/detail-capacity-ui-verification.json').read_text(encoding='utf-8'))
r.update(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,abi='detail_named_capacity_v30',
 evidence='Restarted task-owned 4332 preview for v30, clicked normal Calculate, observed both jobs complete; inspected five-member damage, baseline/delta, compute JSON, parts table and screenshot. Existing fictional profile retained.',
 elapsed_ms=20766.922,initialization_ms=9.113,workspace_bytes=359320,
 timing_scope='Another GPU regression was running concurrently; this is functional verification, not a performance benchmark.')
assert r['total']==288233217 and r['baseline_total']==283664922 and all(r['cpu_verification'].values())
files=[p for p in r['source_sha256'] if p!='research/record-capacity-ui.py']+['research/record-named-capacity-ui.py']
r['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(ROOT/'research/detail-named-capacity-ui-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:r[k] for k in ('passed','total','backend','abi')}))
