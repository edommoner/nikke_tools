"""180-second survival battles with repeated lethal attacks and real skills."""
import hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('long_survival_oracle',ROOT/'scripts/verify-staged-survival.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
selected={'raw-mode-모더니아-True','raw-new-라푼젤-death','raw-new-앤 : 미라클 페어리-death','raw-new-마나-death'}
planned=[]
for name,b,extra in m.fixtures():
    if name not in selected:continue
    b['duration']=180
    for p in b['enemy']['patterns']:
        p['until']={'time':180};p['spec'].update(hits=3,interval=55)
    planned.append((name+'-180-repeated',b,extra))
assert len(planned)==4
files=list(json.loads((ROOT/'research/detail-staged-survival-initial-quick.json').read_text(encoding='utf-8'))['source_sha256'])+['scripts/verify-staged-survival-long.py']
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files}
rows=[];device=m.v.v.v.Cuda()
try:
    for name,b,extra in planned:
        try:
            row=m.compare(device,name,b,extra,'native')
            row['positive_control']=row['incoming_hits']>=2 and bool(row['cpu_revives'])
            row['passed']=row['passed'] and row['positive_control']
        except Exception as error:row=dict(name=name,passed=False,error=repr(error));print(json.dumps(row),flush=True)
        rows.append(row)
        if not row['passed']:break
finally:device.close()
assert hashes=={p:sha(p) for p in files}
passed=len(rows)==len(planned) and all(x['passed'] for x in rows)
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=passed,abi=m.g.DETAIL_ABI,stage_only=True,objective_complete=False,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
(ROOT/'research/detail-staged-survival-repeated-long.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if passed else 1)
