import json,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];python=str(root/'.venv/bin/python')
jobs=[('staged-native',['-m','unittest','discover','-s','tests','-p','test_staged_dot_runtime.py']),('source-native',['-m','unittest','discover','-s','tests','-p','test_periodic_source_runtime.py']),('native-mode-spec',['-m','unittest','discover','-s','tests','-p','test_weapon_mode_specs.py']),('native-mode-input',['-m','unittest','discover','-s','tests','-p','test_mode_input_policy.py']),('reference-rewrite',['-m','unittest','discover','-s','tests','-p','test_reference_rewrite.py']),('duration-native',['research/verify-duration-extend.py','--backend','metal']),('definition-input',['research/verify-definition-input.py']),('definition-scalar',['research/verify-definition-input.py','--scalar-accessor-control']),('definition-out',['research/verify-definition-input.py','--out-parameter-control']),('removal-queue',['research/verify-removal-queue.py']),('numeric',['scripts/verify-portable-numeric.py','--backend','metal']),('probe',['scripts/verify-portable-probe.py','--backend','metal']),('events',['scripts/verify-portable-events.py','--backend','metal']),('roster',['scripts/verify-portable-roster-battles.py','--backend','metal']),('catalog-weapons',['scripts/verify-portable-catalog-weapons.py','--backend','metal']),('equipment',['scripts/verify-portable-real-equipment.py','--backend','metal']),('real-battle',['scripts/verify-portable-real-battle.py','--backend','metal']),('api',['scripts/verify-portable-api.py','--backend','metal']),('pipeline-lock',['scripts/verify-portable-metal-lock.py']),('catalog-audit',['scripts/audit-portable-catalog.py']),('unit',['-m','unittest','discover','-s','tests','-p','test_portable*.py'])]
jobs.insert(0,('stack-foundation',['research/verify-stack-foundation.py','--backend','metal']))
jobs.insert(0,('status-native',['research/verify-status-native-contract.py']))
rows=[]
for name,args in jobs:
 start=time.monotonic();log=Path('/tmp/nikke-v53-gate-'+name+'.log')
 with log.open('w') as f:result=subprocess.run([python,*args],cwd=root,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(name=name,exit_code=result.returncode,elapsed_seconds=time.monotonic()-start,log=str(log)))
 (root/'research/portable-status-global-gates.json').write_text(json.dumps(dict(passed=all(r['exit_code']==0 for r in rows),complete=len(rows)==len(jobs),gates=rows),indent=2)+'\n')
 print(name,result.returncode,round(rows[-1]['elapsed_seconds'],3),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
