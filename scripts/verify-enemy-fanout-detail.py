"""GPU fanout with common authored selector, nesting and spawn-order witnesses."""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_fanout_cases import selector_prepare,selector_actions,selector_exercise,order_prepare,order_exercise,NAMES,world_patterns
from detail_coverage import a
from detail_boss import compile_world
from detail_world import packed_enemy,patterns_for
from impact_specs import ActorHandle,Impact,impact_command
from gpu_selector import Cuda
import detail_gpu as g


def compiled(bm,raw,parts=None):
    chars=[dict(name=n,skill_level=10,_weapon=a.META[n]) for n in NAMES]
    program=g.compile_effects(chars,bm._effects,enemy_fields=True)
    program['world'],_=compile_world({'patterns':patterns_for(parts or [])+raw},parts or [],{'enemy':{'patterns':raw}},program)
    return program


def check(device,backend,bm,program,script,expected,parts=None):
    script.append([max(r[0] for r in script)+.01,5,0,0,0,-1,0,0])
    result=g.run(device,[program],script,[packed_enemy({'def':0,'core_px':0},parts) if parts else [0,0]],[bm.state['base_stats']],module_backend=backend)
    for i,want in enumerate(expected):assert math.isclose(result['queries'][0][i][0],want,abs_tol=1e-8),(i,result['queries'][0][i][0],want)
    assert result['totals'][0]==[0]*5
    return result['workspace_bytes']


def selectors(device,backend,nested):
    reference=selector_exercise(nested);bm,*_=selector_prepare(nested);program=compiled(bm,world_patterns());script=[];expected=[]
    for t,kind,identity,want in selector_actions(nested):
        generation=1 if t<.3 else 2
        if kind=='frame':script.append([t,15,0,0,0,-1,0,0])
        if kind=='all':script.append([t,0,3,0,0,-1,0,0])
        if kind=='one':script.append([t,16,8,0,5+8*identity,generation,0,0])
        if kind=='kill':
            row=impact_command(t,Impact(NAMES[0],ActorHandle(5,identity,generation),0,2,10),NAMES);row[1]=14;script.append(row)
        for i,wire in enumerate((0,5,13)):
            script.append([t,2,135,0,wire,len(expected),12,1 if i==0 else generation]);expected.append(want[i])
        script.append([t,2,103,0,6,len(expected),0,0]);expected.append(want[3])
    workspace=check(device,backend,bm,program,script,expected)
    return dict(passed=True,name='nested-fanout' if nested else 'overlapping-all-and-current',observations=len(reference['observations']),queries=len(expected),workspace_bytes=workspace)


def ordering(device,backend):
    reference=order_exercise();bm,boss,enemy,raw=order_prepare();program=compiled(bm,raw)
    script=[[0,15,0,0,0,-1,0,0],[0,0,0,0,0,-1,0,0],[.1,15,0,0,0,-1,0,0],[.11,0,3,0,0,-1,0,0]];expected=[1,3,2,4]
    for i,wire in enumerate((0,5,13)):script.append([.11,2,135,0,wire,i,12,1])
    script.append([.11,2,103,0,6,3,0,0]);workspace=check(device,backend,bm,program,script,expected)
    return dict(passed=True,name='spawn-order-captured-scaling',values=reference['values'],queries=4,workspace_bytes=workspace)


def capacity(device,backend):
    bm,*_=selector_prepare();bm._effects[0][0]['max_trigger']=1
    raw=[dict(id='wave',kind='summon',spec=dict(count=95,hp=10))];parts=[dict(name=f'fixed{i}',hp=0,reach=1) for i in range(32)]
    program=compiled(bm,raw,parts);script=[[0,15,0,0,0,-1,0,0],[.01,0,3,0,0,-1,0,0]];expected=[]
    for wire in [0]+[5+8*i for i in range(95)]:
        script.append([.01,2,135,0,wire,len(expected),12,1]);expected.append(10)
    script.append([.01,2,103,0,6,len(expected),0,0]);expected.append(96)
    workspace=check(device,backend,bm,program,script,expected,parts)
    return dict(passed=True,name='body-32-parts-95-adds',logical_receivers=96,physical_parts=32,queries=len(expected),workspace_bytes=workspace)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/enemy_fanout_cases.py','scripts/enemy_recipient_cases.py','scripts/detail_coverage.py','tests/test_target_counter_runtime.py','app/detail_effects.cu','data/engine-effect-overrides.json')]
    files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=Cuda()
    try:rows=[selectors(device,args.backend,False),selectors(device,args.backend,True),ordering(device,args.backend),capacity(device,args.backend)]
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,backend=args.backend,cases=rows,source_sha256=before,normal_summon_admission=False,character_admission_changed=False)
    (ROOT/f'research/enemy-fanout-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
