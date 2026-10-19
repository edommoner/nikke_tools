"""Independent pinned native observations, never used as GPU input."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_removal_oracle import observe
cases=json.loads((R/'tests/fixtures/portable-status.json').read_text())['cases'];rows=[]
for case in cases:
 try:
  if case.get('stack_bullet_reference'):
   from portable_bullet_oracle import observe as physical
   cpu=physical(case)
  else:cpu=observe(case)
 except Exception as error:rows.append(dict(name=case['name'],passed=False,error=repr(error)));continue
 rows.append(dict(name=case['name'],passed=True,cpu=cpu))
lookup={r['name']:r for r in rows}
checks={
 'status-charge-cap-0.5':[0,-10,-20,-30],
 'status-charge-cap-1.5':[0,0,-10,-20],
 'status-charge-refresh':[0],
 'status-charge-remove-reapply':[0],
 'status-charge-remove-init':[-10],
 'status-charge-expiry-reapply':[0],
 'status-charge-expiry-init':[-10],
 'status-pools-max-not-sum-True':[-20],
 'status-pools-max-not-sum-False':[-10],
 'status-immune-expired-unretired-False':[0],
 'status-immune-expired-unretired-True':[-10],
 'status-immune-runtime-false-still-presence':[0],
}
for name,values in checks.items():
 row=lookup[name]
 if row['passed']:
  actual=[q['attack_buffs'][0] for q in row['cpu']['queries']]
  if actual!=values:row.update(passed=False,authored_expected=values,actual=actual)
result=dict(passed=all(r['passed'] for r in rows),cases=rows,authored_assertions=len(checks),gpu_execution_performed=False,cpu_results_used_as_gpu_input=False,fixture_sha256=hashlib.sha256((R/'tests/fixtures/portable-status.json').read_bytes()).hexdigest())
(R/'research/portable-status-native-contract.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('Native status cases',len(rows),'failures',[(r['name'],r.get('error',r.get('actual'))) for r in rows if not r['passed']]);raise SystemExit(0 if result['passed'] else 1)
