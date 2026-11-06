"""Run requested S21 acceptance commands with exact environment and receipts."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from search_s21 import DEFAULT,save
ROOT=Path(__file__).resolve().parents[2]
def main(out):
    env=os.environ.copy();env.update(PYTHONPATH=str(out.parent.parent/'pin-update-v1/validation-deps'),NIKKE_SLANG_ROOT=str(ROOT.parents[1]/'.tools/slang-2026.20-Darwin-arm64'),PYTHONDONTWRITEBYTECODE='1')
    results=[]
    commands=[('focused',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_team_search_enumerator.py']),('python',[sys.executable,'-m','unittest','discover','-s','tests']),('node',['node','--test',*map(str,sorted((ROOT/'tests').glob('*.test.mjs')))])]
    for label,command in commands:
        start=time.perf_counter()
        with (out/f'validation-{label}.log').open('w') as log:r=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        results.append(dict(label=label,command=command,exit=r.returncode,seconds=time.perf_counter()-start,env={k:env[k] for k in ('PYTHONPATH','NIKKE_SLANG_ROOT','PYTHONDONTWRITEBYTECODE')}));save(out/'validation.json',results);print(results[-1],flush=True)
    if any(r['exit'] for r in results):raise SystemExit(1)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=DEFAULT/'s21');main(p.parse_args().out)
