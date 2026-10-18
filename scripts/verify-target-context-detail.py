"""Actual add-pool completions and nested target predicates, one shared fixture."""
import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from test_target_counter_runtime import NAMES
from target_counter_cases import marker
from effect_runtime import state,publish_impact
from impact_runtime import land_add
from impact_specs import ActorHandle,Impact,impact_command
from calculator.sim_result import HitEvent
from detail_world import packed_enemy
from gpu_selector import Cuda
import detail_gpu as g
spec=importlib.util.spec_from_file_location('context_source_setup',ROOT/'scripts/verify-summon-sources-detail.py');source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)


def buff(name,stat,value,event,conditions=()):
    return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target='self',duration=10,max_stack=1,trigger=dict(timing=[event],condition=list(conditions)))


def exercise(device,backend,cpu_only,with_hp=False):
    effects=[]
    for name,kind,generation,threshold in [('body','body',1,1),('part','part',1,1),('first','add',1,1),('death','add',2,100)]:
        carrier=marker(name,threshold=threshold,actor=dict(kind=kind,identity=0,generation=generation));carrier['trigger']['timing']=['battle_start'];effects.append(carrier)
        event='event:target_counter_complete:'+name;condition='target_is_add' if kind=='add' else 'target_is_boss';opposite='target_is_boss' if kind=='add' else 'target_is_add'
        effects += [buff('first-'+name,'atk_pct',1,event,[condition]),buff('wrong-'+name,'atk_pct',1000,event,[opposite]),
            buff('gate-'+name,'',0,event,[condition]),
            buff('nested-'+name,'crit_dmg',10,'stack_reach:gate-'+name+':1',['target_is_boss']),
            buff('nested-leak-'+name,'crit_dmg',1000,'stack_reach:gate-'+name+':1',['target_is_add']),
            buff('last-'+name,'atk_pct',2,event,[condition]),
            buff('retired-'+name,'crit_rate',2,'event:state_end:'+name,['target_is_boss'])]
    effects.append(buff('outside','atk_pct',7,'on_attack',['target_is_boss']))
    if with_hp:
        def instant(name,stat,value,event):
            row=buff(name,stat,value,event);row['type']='instant';row.pop('duration');row.pop('max_stack');return row
        effects += [instant('nested HP drain','current_hp_reduce',50,'stack_reach:gate-first:1'),
            buff('HP edge body','crit_dmg',3,'hp_below:60',['target_is_boss']),
            buff('HP edge must not inherit add','crit_dmg',1000,'hp_below:60',['target_is_add']),
            instant('recover inside HP edge','heal_hp_pct',100,'hp_below:60'),
            buff('after HP continuation','crit_dmg',4,'stack_reach:gate-first:1',['target_is_boss'])]
    parts=[dict(name='physical',hp=0,reach=1)]
    raw=[dict(id='wave',kind='summon',spec=dict(name='npc',count=1,hp=5),until=dict(targets_cleared=True),after=['start','wave'],repeat=2)]
    bm,boss,enemy,program=source.prepare(raw,parts,effects);expected=[];observed=[];script=[]
    if with_hp:
        from calculator.timeline import CharState,_register_instant_handlers
        bm.state['hp']={n:bm.state['base_stats'][n]['hp'] for n in NAMES};bm.state['hp_pct']={n:100 for n in NAMES}
        _register_instant_handlers(bm,{c['name']:CharState(c,bm.state['base_stats'][c['name']]['atk'],None) for c in program['chars']},None)
    actions=[(0,'frame',(0,0,0,0)),(0,'start',(0,0,0,0)),(.05,'body',(3,10,2,1)),(.06,'part',(6,20,4,2)),
        (.1,'add1',(9,30,6,3)),(.11,'outside',(16,30,6,3)),(.2,'frame',(16,30,6,3)),
        (.21,'add2',(19,40,8,4)),(.22,'outside',(19,40,8,4)),(.3,'finish',(19,40,8,4))]
    for t,action,want in actions:
        if with_hp and t>=.1:want=(want[0],want[1]+7,*want[2:])
        if action=='frame':
            events=boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count;bm.tick(t)
            for event in events:
                for name in NAMES:bm.notify(event,t,name)
            script.append([t,15,0,0,0,-1,0,0])
        elif action=='finish':boss.finish(t);script.append([t,5,0,0,0,-1,0,0])
        elif action in ('start','outside'):
            bm.tick(t);event='battle_start' if action=='start' else 'on_attack'
            for who,name in enumerate(NAMES):bm.notify(event,t,name);script.append([t,0,g.EVENT[event],who,0,-1,0,0])
        elif action in ('body','part'):
            bm.tick(t);packet=Impact(NAMES[0],ActorHandle(0 if action=='body' else 1,0),0,2,1)
            publish_impact(bm,packet,t);script.append(impact_command(t,packet,NAMES))
        else:
            bm.tick(t);run=boss._runs[-1];assert run.opens==int(action[-1])
            land_add(bm,boss,HitEvent(t,NAMES[0],5,False,'normal'),run.adds[0].id,t)
            cmd=impact_command(t,Impact(NAMES[0],ActorHandle(5,0,run.opens),0,2,5),NAMES);cmd[1]=14;script.append(cmd)
        buffs=bm.get_buffs(NAMES[0],'__enemy__',t)
        got=(buffs.get('atk_pct',0),buffs.get('crit_dmg',0),(buffs['crit_rate']-.15)*100,state(bm).counter_completed)
        assert all(math.isclose(x,y,abs_tol=1e-8) for x,y in zip(got,want)),(action,got,want)
        assert not state(bm).event_stack
        observed.append(dict(time=t,action=action,values=got))
        for key,value in zip(('atk_pct','crit_dmg','crit_rate'),want[:3]):
            script.append([t,2,103,0,g.STAT[key],len(expected),0,0]);expected.append((0,.15+value/100 if key=='crit_rate' else value))
        script.append([t,2,127,0,-1,len(expected),0,0]);expected.append((2,want[3]))
        if with_hp:
            assert bm.state.get('hp_pct',{}).get(NAMES[0],100)==100
            script.append([t,2,101,0,0,len(expected),0,0]);expected.append((1,100))
    last=state(bm).counter_last[1]
    assert last.actor==ActorHandle(5,0,2) and last.reason=='death' and last.impact is None
    assert sum(boss.add_dealt.values())==10
    workspace=None
    if not cpu_only:
        result=g.run(device,[program],script,[packed_enemy({'def':0,'core_px':0},parts)],[bm.state['base_stats']],module_backend=backend)
        for i,(field,want) in enumerate(expected):assert math.isclose(result['queries'][0][i][field],want,abs_tol=1e-8),(i,result['queries'][0][i][field],want)
        assert result['totals'][0]==[0]*5
        workspace=result['workspace_bytes']
    return dict(passed=True,name='actual_add_receipts_and_nested_contexts'+('_with_HP_reentry' if with_hp else ''),observations=observed,queries=len(expected),workspace_bytes=workspace,actual_add_damage=10,completion_without_impact=True,normal_summon_admission=False)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/verify-summon-sources-detail.py',ROOT/'scripts/target_counter_cases.py',ROOT/'scripts/detail_coverage.py',ROOT/'tests/test_target_counter_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    if not args.cpu_preflight:files += [ROOT/'app'/n for n in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};device=None if args.cpu_preflight else Cuda()
    try:rows=[exercise(device,args.backend,args.cpu_preflight,with_hp) for with_hp in (False,True)]
    finally:
        if device:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cpu_only=args.cpu_preflight,backend=args.backend,cases=rows,source_sha256=before,character_admission_changed=False)
    path=ROOT/f'research/target-context-{"cpu-preflight" if args.cpu_preflight else args.backend}.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(rows),report=str(path))))


if __name__=='__main__':main()
