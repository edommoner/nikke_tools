"""Sequential source-bound stage checks; one runner per GPU backend maximum."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);args=ap.parse_args()
for script,label,extra in [
    ('verify-staged-heal-query.py','heal',[]),
    ('verify-staged-survival.py','full',['--fail-fast']),
    ('verify-staged-survival-regression.py','regression',[]),
    ('verify-staged-survival-regression.py','long',['--long'])]:
    report=f'research/detail-staged-survival-{args.backend}-{label}.json'
    command=[sys.executable,'scripts/'+script,'--backend',args.backend,'--output',report,*extra]
    print('Running '+args.backend+' '+label,flush=True)
    with (ROOT/report.replace('.json','.log')).open('w',encoding='utf-8') as out:
        result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
    if result.returncode:raise SystemExit(result.returncode)
    r=json.loads((ROOT/report).read_text(encoding='utf-8'));assert r['passed'] and not r['not_run_cases'] and r['abi']=='detail_survival_v34'
    print('Passed '+args.backend+' '+label+' '+str(len(r['cases'])),flush=True)
