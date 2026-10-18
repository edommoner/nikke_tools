"""Periodic clock ownership, phase-preserving refresh and boundary checks."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from timer_registry_cases import cases,prepare,exercise,NAMES
from detail_coverage import a
from gpu_selector import Cuda
import detail_gpu as g


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__),ROOT/'scripts/timer_registry_cases.py',ROOT/'scripts/enemy_recipient_cases.py',ROOT/'app/detail_effects.cu']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};rows=[];device=None if args.cpu_preflight else Cuda()
    try:
        for case in cases():
            cpu=exercise(case);bm=prepare(case);chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in NAMES]
            program=g.compile_effects(chars,bm._effects);script=[[0,0,0,0,0,-1,0,0]]
            for i,t in enumerate(case['times']):
                if t in case.get('events',{}):script.append([t,0,{'on_attack':7}[case['events'][t]],0,0,-1,0,0])
                script.append([t,2,0,0,-1,i,0,0])
            result=None if device is None else g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=args.backend)
            actual=None if result is None else [r[38] for r in result['queries'][0]]
            if actual is not None:assert actual==case['totals'],(case['name'],actual,case['totals'])
            rows.append(dict(name=case['name'],passed=True,cpu=cpu,gpu_damage=actual,workspace_bytes=result['workspace_bytes'] if result else None))
            print(json.dumps(dict(name=case['name'],passed=True)),flush=True)
    finally:
        if device:device.close()
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    report=dict(passed=True,cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False)
    suffix='cpu-preflight' if args.cpu_preflight else args.backend
    (ROOT/f'research/timer-registry-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
