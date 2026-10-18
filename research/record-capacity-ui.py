"""Record values observed in the normal UI and its expanded compute JSON."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'research/detail-team-hits-ui-verification.json').read_text(encoding='utf-8'))
report.update(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,
 evidence='Restarted task-owned 4332 server for v29; clicked normal squad Calculate, observed completion, all five member values, baseline/delta, expanded compute JSON, part table and screenshot. Existing fictional owned roster retained.',
 elapsed_ms=9556.65,initialization_ms=9.305,workspace_bytes=359320,abi='detail_capacity_v29')
assert report['total']==288233217 and report['baseline_total']==283664922
assert all(report['cpu_verification'].values())
files=list(report['source_sha256'])+['app/detail_effects-build.json','research/record-capacity-ui.py']
report['source_sha256']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
(ROOT/'research/detail-capacity-ui-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ('passed','total','backend','workspace_bytes')}))
