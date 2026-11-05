import argparse,json,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];python=str(root/'.venv/bin/python')
jobs=[('staged-native',['-m','unittest','discover','-s','tests','-p','test_staged_dot_runtime.py']),('source-native',['-m','unittest','discover','-s','tests','-p','test_periodic_source_runtime.py']),('native-mode-spec',['-m','unittest','discover','-s','tests','-p','test_weapon_mode_specs.py']),('native-mode-input',['-m','unittest','discover','-s','tests','-p','test_mode_input_policy.py']),('reference-rewrite',['-m','unittest','discover','-s','tests','-p','test_reference_rewrite.py']),('duration-native',['research/verify-duration-extend.py','--backend','metal']),('definition-input',['research/verify-definition-input.py']),('definition-scalar',['research/verify-definition-input.py','--scalar-accessor-control']),('definition-out',['research/verify-definition-input.py','--out-parameter-control']),('removal-queue',['research/verify-removal-queue.py']),('numeric',['scripts/verify-portable-numeric.py','--backend','metal']),('probe',['scripts/verify-portable-probe.py','--backend','metal']),('events',['scripts/verify-portable-events.py','--backend','metal']),('roster',['scripts/verify-portable-roster-battles.py','--backend','metal']),('catalog-weapons',['scripts/verify-portable-catalog-weapons.py','--backend','metal']),('equipment',['scripts/verify-portable-real-equipment.py','--backend','metal']),('real-battle',['scripts/verify-portable-real-battle.py','--backend','metal']),('api',['scripts/verify-portable-api.py','--backend','metal']),('pipeline-lock',['scripts/verify-portable-metal-lock.py']),('catalog-audit',['scripts/audit-portable-catalog.py']),('unit',['-m','unittest','discover','-s','tests','-p','test_portable*.py'])]
jobs.insert(0,('stack-foundation',['research/verify-stack-foundation.py','--backend','metal']))
jobs.insert(0,('status-native',['research/verify-status-native-contract.py']))
jobs.insert(0,('protection-native',['research/verify-protection.py','--native-only']))
jobs.insert(0,('split-native',['research/verify-protection.py','--split','--native-only']))
jobs.insert(0,('instant-list-native',['research/verify-instant-lists.py','--native-only']))
jobs.insert(0,('named-state-native',['research/verify-named-states.py','--native-only']))
jobs.insert(0,('enemy-code-native',['research/verify-codes.py','--native-only']))
jobs.insert(0,('enemy-code-real',['research/verify-code-real.py']))
jobs.insert(0,('core',['research/verify-element-optimized.py','--backend','metal']))
jobs.insert(0,('element-native',['research/verify-elements.py','--native-only']))
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();total=len(jobs);rows=[]
for name,args in jobs:
 subprocess.run(['git','diff','--exit-code',source,'--','app','scripts','gpu','tests'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 start=time.monotonic();log=Path('/tmp/nikke-element-optimized-gate-'+name+'.log')
 with log.open('w') as f:result=subprocess.run([python,*args],cwd=root,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(name=name,source_commit=source,exit_code=result.returncode,elapsed_seconds=time.monotonic()-start,log=str(log)))
 (root/'research/portable-element-optimized-global-gates.json').write_text(json.dumps(dict(passed=all(r['exit_code']==0 for r in rows),complete=len(rows)==total,gates=rows,source_commit=source),indent=2)+'\n')
 print(name,result.returncode,round(rows[-1]['elapsed_seconds'],3),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
