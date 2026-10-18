"""Finish staged extra/legacy acceptance after a verified new-case process."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);args=ap.parse_args()
def current(path):
    if not path.exists():return False
    r=json.loads(path.read_text(encoding='utf-8'))
    return r['passed'] and all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in r['source_sha256'].items())
assert current(ROOT/f'research/detail-heal-charge-new-{args.backend}.json'),'Require a finished, passed, source-bound new-case suite.'
for group,script,flags in [('extra','research/verify-heal-charge-extra.py',[]),('legacy','research/verify-heal-charge.py',['--group','legacy'])]:
    output=f'research/detail-heal-charge-{group}-{args.backend}.json'
    if current(ROOT/output):print('Retained current accepted '+group,flush=True);continue
    subprocess.run([sys.executable,script,'--backend',args.backend,*flags,'--output',output],cwd=ROOT,check=True)
    assert current(ROOT/output)
print(json.dumps(dict(passed=True,backend=args.backend,cases=208,objective_complete=False)),flush=True)
