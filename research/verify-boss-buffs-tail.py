"""Run dependent long/boundary/API checks sequentially, at most one GPU worker."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
steps=[
 ([sys.executable,'scripts/verify-boss-buffs-detail.py','--backend','native','--long','--fail-fast','--output','research/detail-boss-buffs-long-verification.json'],'research/detail-boss-buffs-long-verification.log'),
 ([sys.executable,'scripts/verify-boss-buff-boundaries.py'],'research/detail-boss-buff-boundaries-verification.log'),
 (['node','scripts/smoke-detail-boss-buffs.mjs','research/detail-boss-buffs-api-fixture.json'],'research/detail-boss-buffs-api-verification.log')]
for command,log in steps:
 print('Running '+command[1],flush=True)
 with (ROOT/log).open('w',encoding='utf-8') as output:
  result=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(result.returncode)
 print('Passed '+command[1],flush=True)
