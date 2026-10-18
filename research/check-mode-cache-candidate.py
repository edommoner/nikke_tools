import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name,args in [('mode-return',['scripts/debug-boss-buff-rng.py','--duration','30']),('full-end',['scripts/debug-boss-buff-rng.py','--duration','30','--full-end-damage']),('charge-restore',['scripts/debug-mode-charge-restore.py'])]:
 print('Running '+name,flush=True)
 with (ROOT/f'research/detail-cache-candidate-{name}.log').open('w',encoding='utf-8') as out:
  subprocess.run([sys.executable,*args],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True)
 print('Finished '+name,flush=True)
