"""Shared authored receiver mutation sequence, CPU/GPU independent execution."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_mutation_cases import prepare,actions,exercise,EVENTS,NAMES,world_patterns
from detail_coverage import a
from detail_boss import compile_world
from impact_specs import ActorHandle,Impact,impact_command
from gpu_selector import Cuda
import detail_gpu as g


def verify(device,backend,cpu_only=False):
    reference=exercise();bm,*_=prepare();chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
    program=g.compile_effects(chars,bm._effects,enemy_fields=True);raw=world_patterns();program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
    g.validate_gpu_fields(program['effects'],True)
    script=[];expected=[]
    for t,action,identity,want in actions():
        generation=1 if t<.3 else 2
        if action=='frame':script.append([t,15,0,0,0,-1,0,0])
        elif action=='kill':
            row=impact_command(t,Impact(NAMES[0],ActorHandle(5,identity,generation),0,2,10),NAMES);row[1]=14;script.append(row)
        elif action in EVENTS:
            event,owner=EVENTS[action]
            if identity is None:script.append([t,0,g.EVENT[event],owner,0,-1,0,0])
            else:script.append([t,16,g.EVENT[event],owner,0 if identity==-1 else 5+8*identity,1 if identity==-1 else generation,0,0])
        for i,wire in enumerate((0,5,13)):
            script.append([t,2,135,0,wire,len(expected),12,1 if i==0 else generation]);expected.append(want[i])
        script.append([t,2,103,0,6,len(expected),0,0]);expected.append(want[3])
    script.append([.61,5,0,0,0,-1,0,0]);workspace=None
    if not cpu_only:
        result=g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
        for i,want in enumerate(expected):assert math.isclose(result['queries'][0][i][0],want,abs_tol=1e-8),(i,result['queries'][0][i][0],want)
        assert result['totals'][0]==[0]*5;workspace=result['workspace_bytes']
    return dict(passed=True,observations=len(reference['observations']),queries=len(expected),workspace_bytes=workspace,independent_expected=True,normal_summon_admission=False)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/enemy_mutation_cases.py','scripts/enemy_recipient_cases.py','scripts/detail_coverage.py','tests/test_target_counter_runtime.py','app/detail_effects.cu','data/engine-effect-overrides.json')]
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=None if args.cpu_preflight else Cuda()
    try:cases=[verify(device,args.backend,args.cpu_preflight)]
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cpu_only=args.cpu_preflight,backend=args.backend,cases=cases,source_sha256=before,character_admission_changed=False)
    (ROOT/f'research/enemy-mutations-{"cpu-preflight" if args.cpu_preflight else args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(cases),observations=cases[0]['observations'])))


if __name__=='__main__':main()
