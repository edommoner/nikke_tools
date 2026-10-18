"""Actual world count + effect lifetimes; no character-specific result matrix."""
import argparse,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from test_target_counter_runtime import NAMES
from detail_world import packed_enemy
from impact_specs import ActorHandle,Impact,impact_command
from impact_runtime import land_add
from calculator.sim_result import HitEvent
from gpu_selector import Cuda
import detail_gpu as g
spec=importlib.util.spec_from_file_location('world_source_verifier',ROOT/'scripts/verify-summon-sources-detail.py');sources=importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)


def effect(name,stat,value,condition,timing='passive',duration=-1,max_stack=1):
    return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target='self',duration=duration,max_stack=max_stack,trigger=dict(timing=[timing],condition=condition))


def exercise(device,backend,parts,cpu_only):
    effects=[effect('crowded','atk_pct',17,['enemy_count_above:3']),
        effect('sparse','crit_rate',11,['enemy_count_below:2']),
        effect('window','charge_dmg_pct',7,['enemy_count_above:2','enemy_count_below:3','self_state:gate']),
        effect('gate','',0,[],'on_attack',.15),
        effect('latched','atk_pct',23,['enemy_count_above:3'],'on_attack',.25),
        effect('tail','crit_dmg',101,['enemy_count_above:3'],duration=.1),
        effect('event-progress','',0,['enemy_count_above:3'],'on_attack',max_stack=100)]
    raw=[dict(id='wave',kind='summon',spec=dict(count=2,hp=1),delay=1,until=dict(time=1,targets_cleared=True),after=['start','wave'],repeat=2)]
    bm,boss,enemy,program=sources.prepare(raw,parts,effects)
    # Expected count, ATK%, crit%, charge%, crit damage%, qualified event count.
    actions=[(0,'frame',(1,0,11,0,0,0)),(0,'start',(1,0,11,0,0,0)),
        (.1,'attack',(1,0,11,0,0,0)),(1,'frame',(3,17,0,0,101,0)),
        (1.05,'attack',(3,40,0,7,101,1)),(1.1,'hit0',(3,40,0,7,101,1)),
        (1.11,'attack',(3,40,0,7,101,2)),(1.2,'frame',(2,23,11,7,101,2)),
        (1.22,'attack',(2,23,11,7,0,2)),(1.25,'hit1',(2,23,11,7,0,2)),
        (1.3,'frame',(1,23,11,0,0,2)),(1.4,'frame',(1,0,11,0,0,2)),
        (2.3,'frame',(3,17,0,0,101,2)),(2.31,'attack',(3,40,0,7,101,3)),
        (3.3,'frame',(1,0,11,0,0,3)),(3.6,'frame',(1,0,11,0,0,3))]
    script=[];expected=[];observations=[]
    def query(t,event,arg,field,want):
        script.append([t,2,event,0,arg,len(expected),0,0]);expected.append((field,want))
    # Source-only schedules require an actual initial frame at zero.
    for t,action,want in actions:
        if action=='frame':
            events=boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count;bm.tick(t)
            for event in events:
                for name in NAMES:bm.notify(event,t,name)
            script.append([t,15,0,0,0,-1,0,0])
        elif action in ('start','attack'):
            bm.tick(t);ev='battle_start' if action=='start' else 'on_attack'
            for i,name in enumerate(NAMES):
                bm.notify(ev,t,name);script.append([t,0,g.EVENT[ev],i,0,-1,0,0])
        else:
            identity=int(action[-1]);bm.tick(t)
            land_add(bm,boss,HitEvent(t,NAMES[0],1,False,'normal'),boss._runs[-1].adds[identity].id,t)
            cmd=impact_command(t,Impact(NAMES[0],ActorHandle(5,identity,boss._runs[-1].opens),0,2,1),NAMES);cmd[1]=14;script.append(cmd)
        buffs=dict(bm.get_buffs(NAMES[0],'__enemy__',t))
        buffs['crit_rate']=(buffs['crit_rate']-.15)*100
        got=(boss.enemy_count,*(buffs.get(key,0) for key in ('atk_pct','crit_rate','charge_dmg_pct','crit_dmg')),bm.ref_count(NAMES[0],'event-progress') or 0)
        # Passive carriers are registered at battle_start, so the pre-start
        # initial frame only observes the world, not an initialized effect set.
        if action=='frame' and t==0:want=(1,0,0,0,0,0)
        assert all(math.isclose(x,y,abs_tol=1e-8) for x,y in zip(got,want)),(t,action,got,want)
        observations.append(dict(t=t,action=action,values=got))
        query(t,134,0,11,want[0])
        for key,value in zip(('atk_pct','crit_rate','charge_dmg_pct','crit_dmg'),want[1:5]):query(t,103,g.STAT[key],0,.15+value/100 if key=='crit_rate' else value)
        query(t,0,program['states']['event-progress'],37,want[5])
    script.append([3.7,5,0,0,0,-1,0,0])
    workspace=None
    if not cpu_only:
        result=g.run(device,[program],script,[packed_enemy({'def':0,'core_px':0},parts)],[bm.state['base_stats']],module_backend=backend)
        for i,(field,want) in enumerate(expected):assert math.isclose(result['queries'][0][i][field],want,abs_tol=1e-8),(i,field,result['queries'][0][i][field],want)
        workspace=result['workspace_bytes']
    return dict(passed=True,fixed_parts=len(parts),observations=observations,queries=len(expected),workspace_bytes=workspace)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/verify-summon-sources-detail.py',ROOT/'scripts/detail_coverage.py',ROOT/'tests/test_target_counter_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=None if args.cpu_preflight else Cuda();start=time.perf_counter()
    try:rows=[exercise(device,args.backend,parts,args.cpu_preflight) for parts in ([],[dict(name='physical',hp=0,reach=1),dict(name='physical2',hp=0,reach=1)])]
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cpu_only=args.cpu_preflight,backend=args.backend,cases=rows,source_sha256=before,elapsed_s=time.perf_counter()-start,normal_summon_admission=False,character_admission_changed=False)
    path=ROOT/f'research/world-conditions-{"cpu-preflight" if args.cpu_preflight else args.backend}.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(rows),report=str(path))))


if __name__=='__main__':main()
