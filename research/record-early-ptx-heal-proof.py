"""Normalize the completed PTX-only proof; do not rerun or fabricate GPU work."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source='research/detail-staged-survival-ptx-heal-early.json'
r=json.loads((ROOT/source).read_text(encoding='utf-8'))
assert r['passed'] and len(r['cases'])==3
for p,h in r['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
assert all(x['passed'] and x['checks']['actual_gpu'] and x['backend']=='ptx' for x in r['cases'])
r.update(abi='detail_survival_v34',planned_cases=3,not_run_cases=0,derived_from=source,cpu_trace_used_as_gpu_input=False)
r['source_sha256'][source]=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
r['source_sha256']['research/record-early-ptx-heal-proof.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(ROOT/'research/detail-staged-survival-ptx-heal.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded the already completed, unchanged-source PTX healing proof (3 cases).')
