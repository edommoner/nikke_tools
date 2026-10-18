"""Sequential authored19/raw4/prior101 acceptance on one chosen GPU backend."""
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);backend=ap.parse_args().backend
env=dict(os.environ,CUDA_CACHE_PATH=str(ROOT/'research/cuda-cache'),CUDA_CACHE_MAXSIZE='536870912')
for kind in ('authored','real','regression'):
    script='research/verify-outgoing-healing-regressions.py' if kind=='regression' else 'scripts/verify-staged-outgoing-healing.py'
    output=f'research/detail-outgoing-healing-{kind}-{backend}.json';log=ROOT/f'research/detail-outgoing-healing-{kind}-{backend}.log'
    args=[sys.executable,script,'--backend',backend,'--output',output]+(['--real','--fail-fast'] if kind=='real' else ['--fail-fast'] if kind=='authored' else [])
    with log.open('w',encoding='utf-8') as stream:result=subprocess.run(args,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:print(json.dumps(dict(backend=backend,kind=kind,passed=False,exit_code=result.returncode)),flush=True);raise SystemExit(result.returncode)
    r=json.loads((ROOT/output).read_text(encoding='utf-8'));assert r['passed']
    print(json.dumps(dict(backend=backend,kind=kind,passed=True,cases=len(r['cases']))),flush=True)
