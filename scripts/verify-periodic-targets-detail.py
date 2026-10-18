"""Periodic input/eligibility sampling and registration ownership on both backends."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from periodic_target_cases import prepare,actions,exercise,reentrant_prepare,reentrant_actions,reentrant_exercise,predicate_prepare,predicate_actions,predicate_exercise,sibling_prepare,sibling_actions,sibling_exercise,NAMES,world_patterns
from detail_coverage import a
from detail_boss import compile_world
from impact_specs import ActorHandle,Impact,impact_command
from periodic_target_specs import required_aim_owners
from gpu_selector import Cuda
import detail_gpu as g


def compiled(bm,raw):
    chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES];program=g.compile_effects(chars,bm._effects,enemy_fields=True)
    program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program);g.validate_gpu_fields(program['effects'],bool(raw));return program


def run(device,backend,bm,program,script,expected,cpu_only):
    assert required_aim_owners(program['effects'],bool(program['world'][0]))<={int(r[3]) for r in script if r[0]==0 and r[1]==17}
    script.append([max(r[0] for r in script)+.01,5,0,0,0,-1,0,0])
    if cpu_only:return None
    result=g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
    for i,want in enumerate(expected):assert math.isclose(result['queries'][0][i][0],want,abs_tol=1e-8),(i,result['queries'][0][i][0],want)
    assert result['totals'][0]==[0]*5;return result['workspace_bytes']


def selection(device,backend,policy,cpu_only=False):
    predicate=policy=='predicate';reference=predicate_exercise() if predicate else exercise(policy)
    bm,*_=(predicate_prepare() if predicate else prepare(policy));program=compiled(bm,world_patterns());script=[];expected=[]
    for t,action,value,want in (predicate_actions() if predicate else actions(policy)):
        if action=='frame':script.append([t,15,0,0,0,-1,0,0])
        elif action=='aim':
            kind,identity,generation=value;script.append([t,17,0,0,kind+8*identity,generation,0,0])
        elif action=='start':
            script.append([t,0,0,0,0,-1,0,0])
            if predicate:script += [[t,16,8,0,13,1,0,0],[t,16,3,0,13,1,0,0]]
            else:script.append([t,0,3,0,0,-1,0,0])
        elif action in ('apply','gate','register-clean'):script.append([t,0,{'apply':18,'gate':1,'register-clean':10}[action],0,0,-1,0,0])
        elif action=='mark':script.append([t,16,8,0,value[0]+8*value[1],value[2],0,0])
        elif action=='kill':
            row=impact_command(t,Impact(NAMES[0],ActorHandle(5,value,1),0,2,10),NAMES);row[1]=14;script.append(row)
        for i,wire in enumerate((0,5,13)):
            script.append([t,2,135,0,wire,len(expected),12,1 if i==0 or t<.375 else 2]);expected.append(want[i])
    workspace=run(device,backend,bm,program,script,expected,cpu_only)
    return dict(passed=True,name=policy,observations=len(reference['observations']),queries=len(expected),workspace_bytes=workspace)


def reentrant(device,backend,cpu_only=False,sibling=False):
    reference=sibling_exercise() if sibling else reentrant_exercise();bm=sibling_prepare() if sibling else reentrant_prepare();program=compiled(bm,[]);script=[];expected=[]
    for t,action,want in (sibling_actions() if sibling else reentrant_actions()):
        if action=='start':script += [[t,0,0,0,0,-1,0,0],[t,0,3,0,0,-1,0,0]]
        if action=='apply':script.append([t,0,18,0,0,-1,0,0])
        script.append([t,2,135,0,0,len(expected),12,1]);expected.append(want[0])
        script.append([t,2,103,0,6,len(expected),0,0]);expected.append(want[1])
    workspace=run(device,backend,bm,program,script,expected,cpu_only)
    return dict(passed=True,name='sibling-registration' if sibling else 'reentrant-registration',observations=len(reference['observations']),queries=len(expected),workspace_bytes=workspace)


def controls(device,backend):
    bm,*_=prepare();program=compiled(bm,world_patterns())
    for wire,generation in ((13,2),(21,1)):
        script=[[0,15,0,0,0,-1,0,0],[0,17,0,0,wire,generation,0,0],[.01,2,135,0,0,0,12,1],[.02,5,0,0,0,-1,0,0]]
        try:g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
        except RuntimeError as error:assert 'result rejected: [8]' in str(error),str(error)
        else:raise AssertionError('Stale or unknown aim was accepted')
    script=[[0,15,0,0,0,-1,0,0],[0,17,0,0,0,1,0,0],[0,0,0,0,0,-1,0,0],[0,0,3,0,0,-1,0,0],[.125,2,135,0,0,0,12,1],[.13,5,0,0,0,-1,0,0]]
    result=g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend);assert result['queries'][0][0][0]==20
    return dict(passed=True,rejected=2,context_reused=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/periodic_target_cases.py','scripts/enemy_mutation_cases.py','scripts/enemy_recipient_cases.py','scripts/detail_coverage.py','tests/test_target_counter_runtime.py','app/detail_effects.cu','data/engine-effect-overrides.json')]
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=None if args.cpu_preflight else Cuda()
    try:
        cases=[selection(device,args.backend,p,args.cpu_preflight) for p in ('current','boss','all','predicate')]+[reentrant(device,args.backend,args.cpu_preflight),reentrant(device,args.backend,args.cpu_preflight,True)]
        negative=None if args.cpu_preflight else controls(device,args.backend)
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cpu_only=args.cpu_preflight,backend=args.backend,cases=cases,controls=negative,source_sha256=before,character_admission_changed=False,normal_summon_admission=False)
    (ROOT/f'research/periodic-targets-{"cpu-preflight" if args.cpu_preflight else args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(cases))))


if __name__=='__main__':main()
