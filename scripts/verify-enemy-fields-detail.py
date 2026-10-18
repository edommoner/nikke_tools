"""Sparse GPU recipient storage; authored inputs, not CPU buff-state replay."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_recipient_cases import prepare,actions,expected_values,exercise,world_patterns,NAMES
from detail_coverage import a
from detail_boss import compile_world
from impact_specs import ActorHandle,Impact,impact_command
from gpu_selector import Cuda
import detail_gpu as g


def case(device,backend,stat,factor,cpu_only=False):
    reference=exercise(stat,factor)
    bm,boss,enemy,registry=prepare(stat,factor)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in NAMES]
    program=g.compile_effects(chars,bm._effects,enemy_fields=True)
    raw=world_patterns();program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
    script=[];expected=[]
    for t,kind,identity,owner,want in actions():
        generation=1 if t<.3 else 2
        if kind=='frame':script.append([t,15,0,0,0,-1,0,0])
        else:
            actor=ActorHandle(0,0) if identity==-1 else ActorHandle(5,identity,generation)
            if kind=='kill':
                cmd=impact_command(t,Impact(NAMES[owner],actor,0,2,10),NAMES);cmd[1]=14;script.append(cmd)
            else:script.append([t,16,8 if kind=='apply' else 3 if kind=='alias' else 7,owner,int(actor.kind)+8*actor.identity,actor.generation,0,0])
        want=expected_values(t,want,stat,factor)
        if stat!='stun':
            for index,kind in enumerate((0,5,5)):
                identity=0 if index<2 else 1;wire=kind+8*identity
                script.append([t,2,135,0,wire,len(expected),12 if stat=='received_dmg_pct' else 2,1 if index==0 else generation]);expected.append(want[index])
        # This gate probes actual recipient-scoped stun/immunity in the third
        # case. The first two also cover the recipient-scoped named state.
        script.append([t,2,103,0,6,len(expected),0,0]);expected.append(want[3])
    script.append([.9,5,0,0,0,-1,0,0])
    workspace=None
    if not cpu_only:
        result=g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
        for index,want in enumerate(expected):assert math.isclose(result['queries'][0][index][0],want,abs_tol=1e-8),(stat,index,result['queries'][0][index][0],want)
        assert result['totals'][0]==[0]*5
        workspace=result['workspace_bytes']
    return dict(passed=True,stat=stat,independent_observations=len(actions()),queries=len(expected),actual_add_damage=reference['actual_add_damage'],workspace_bytes=workspace,stun_predicate_witness=stat=='stun',normal_summon_admission=False)


def controls(device,backend):
    bm,*_=prepare();chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
    program=g.compile_effects(chars,bm._effects,enemy_fields=True);raw=world_patterns();program['world'],_=compile_world({'patterns':raw},[],{'enemy':{'patterns':raw}},program)
    for wire,generation in ((5,2),(21,1)):
        script=[[0,15,0,0,0,-1,0,0],[.01,16,8,0,wire,generation,0,0],[.02,2,135,0,0,0,12,1],[.1,5,0,0,0,-1,0,0]]
        try:g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
        except RuntimeError as error:assert 'result rejected: [8]' in str(error),str(error)
        else:raise AssertionError('Unknown/stale target notification was accepted')
    script=[[0,15,0,0,0,-1,0,0],[.01,16,8,0,0,1,0,0],[.02,2,135,0,0,0,12,1],[.1,5,0,0,0,-1,0,0]]
    result=g.run(device,[program],script,[[0,0]],[bm.state['base_stats']],module_backend=backend)
    assert result['queries'][0][0][0]==10
    return dict(passed=True,rejected=2,context_reused=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/enemy_recipient_cases.py',ROOT/'scripts/detail_coverage.py',ROOT/'tests/test_target_counter_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=None if args.cpu_preflight else Cuda()
    try:
        rows=[case(device,args.backend,stat,factor,args.cpu_preflight) for stat,factor in [('received_dmg_pct',1),('def_pct',-1),('stun',1)]]
        rejected=None if args.cpu_preflight else controls(device,args.backend)
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cpu_only=args.cpu_preflight,backend=args.backend,cases=rows,controls=rejected,source_sha256=before,character_admission_changed=False)
    path=ROOT/f'research/enemy-fields-{"cpu-preflight" if args.cpu_preflight else args.backend}.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(rows),report=str(path))))


if __name__=='__main__':main()
