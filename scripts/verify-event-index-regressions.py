"""Shared ordering controls for indexed dispatch; reuse existing independent oracles."""
import argparse,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('native','ptx'),default='native');args=parser.parse_args()
    events=load('indexed_event_controls','verify-events-detail.py')
    named=load('indexed_named_controls','verify-named-hits.py')
    hp=load('indexed_hp_controls','verify-hp-edge.py')
    files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    files += [ROOT/'app'/name for name in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    started=time.perf_counter();device=Cuda();rows=[]
    try:
        rows+=events.verify(device,args.backend,include_real=False)
        rows+=named.independent(device,args.backend)
        for name,body,extra in named.fixtures():
            if name=='named-hits-down-revive-fractions':rows.append(named.compare(device,name,body,extra,args.backend))
        for name,body,extra in hp.fixtures():
            if name in ('reentrant-heal','registration-high-first','received-heal-after-edge','revival-suppresses-edge'):
                rows.append(hp.compare(device,name,body,extra,args.backend))
    finally:device.close()
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    assert len(rows)==25,len(rows)
    report=dict(passed=all(row['passed'] for row in rows),backend=args.backend,cases=rows,source_stable=True,source_sha256=hashes,
        seconds=time.perf_counter()-started,cpu_trace_used_as_gpu_input=False,
        scope='Existing independent ordering, duplicate descriptor, private continuation, nested HP/heal and revival controls; no per-character matrix expansion.')
    (ROOT/f'research/event-index-regressions-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(rows),seconds=report['seconds'])),flush=True)
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
