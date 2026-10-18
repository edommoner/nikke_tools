"""Sequential v40 8+16+5+124 parity, reusing only current passed evidence."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);backend=ap.parse_args().backend
env=dict(os.environ,CUDA_CACHE_PATH=str(ROOT/'research/cuda-cache'),CUDA_CACHE_MAXSIZE='536870912')
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
for kind,script,flags,count in [('authored','scripts/verify-staged-healing-storage.py',['--fail-fast'],8),('extra','research/verify-healing-storage-extra.py',[],16),('real','scripts/verify-staged-healing-storage.py',['--real','--fail-fast'],5),('regression','research/verify-healing-storage-regressions.py',[],124)]:
    output=f'research/detail-healing-storage-{kind}-{backend}.json';current=False
    try:
        r=json.loads((ROOT/output).read_text(encoding='utf-8'));current=r['passed'] and r['abi']=='detail_healing_storage_v40' and r['backend']==backend and len(r['cases'])==count and not r['not_run_cases'] and all(sha(p)==h for p,h in r['source_sha256'].items())
    except (OSError,ValueError,KeyError):pass
    if current:print(json.dumps(dict(backend=backend,kind=kind,cases=count,reused_current_passed_evidence=True)),flush=True);continue
    args=[sys.executable,script,'--backend',backend,'--output',output]+flags
    with (ROOT/f'research/detail-healing-storage-{kind}-{backend}.log').open('w',encoding='utf-8') as stream:result=subprocess.run(args,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:print(json.dumps(dict(backend=backend,kind=kind,passed=False,exit_code=result.returncode)),flush=True);raise SystemExit(result.returncode)
    r=json.loads((ROOT/output).read_text(encoding='utf-8'));assert r['passed'] and len(r['cases'])==count
    print(json.dumps(dict(backend=backend,kind=kind,passed=True,cases=count)),flush=True)
