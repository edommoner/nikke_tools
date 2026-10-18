"""Authored recipient lifecycle table, reusable by CPU and GPU witnesses."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES
from calculator.boss_pattern import BossScript,validate
from calculator.sim_result import HitEvent
from effect_runtime import state
from impact_specs import ActorHandle,Impact
from impact_runtime import land_add
from world_actor_runtime import registry_for


def field(name,stat,value,event,*,stack=3,duration=.5,conditions=(),target='target'):
    return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target=target,max_stack=stack,duration=duration,trigger=dict(timing=[event],condition=list(conditions)))


def world_patterns():
    return [dict(id='wave',kind='summon',spec=dict(count=2,hp=10),until=dict(time=.3),after=['start','wave'],repeat=2)]


def prepare(field_stat='received_dmg_pct',factor=1):
    effects=[field('vulnerability',field_stat,10*factor,'hit_count:1'),field('vulnerability',field_stat,10*factor,'burst_cast'),
        field('proof','',0,'hit_count:1',stack=1),
        field('qualified','crit_dmg',7,'on_attack',stack=100,duration=1,conditions=['target_stunned' if field_stat=='stun' else 'target_state:proof'],target='self'),
        field('vulnerability','stun_immune' if field_stat=='stun' else field_stat,4*factor,'hit_count:1')]
    bm=manager(effects,[0,0,0,0,1]);enemy={'def':0,'core_px':0}
    boss=BossScript(validate(world_patterns()),enemy,lambda *_:True)
    registry=registry_for(bm,boss)
    return bm,boss,enemy,registry


def actions():
    # body/add0/add1 received damage modifiers, qualified ally modifier.
    return [(0,'frame',None,0,(0,0,0,0)),(.01,'apply',-1,0,(10,0,0,0)),(.02,'apply',0,0,(10,10,0,0)),
        (.03,'apply',0,0,(10,20,0,0)),(.04,'alias',0,0,(10,30,0,0)),(.05,'apply',0,1,(10,34,0,0)),
        (.06,'probe',1,0,(10,34,0,0)),(.07,'probe',0,0,(10,34,0,7)),(.08,'kill',0,0,(10,0,0,7)),
        (.09,'probe',0,0,(10,0,0,7)),(.3,'frame',None,0,(10,0,0,7)),(.31,'apply',0,0,(10,10,0,7)),
        (.32,'alias',0,0,(10,20,0,7)),(.33,'probe',1,0,(10,20,0,7)),(.34,'probe',0,0,(10,20,0,14)),
        (.52,'frame',None,0,(0,20,0,14)),(.53,'apply',1,0,(0,20,10,14)),(.54,'probe',1,0,(0,20,10,21)),
        (.6,'frame',None,0,(0,0,0,21)),(.83,'frame',None,0,(0,0,0,21))]


def expected_values(t,want,field_stat='received_dmg_pct',factor=1):
    if field_stat!='stun':return tuple(x*factor for x in want[:3])+(want[3],)
    status=[int(x!=0) for x in want[:3]]
    if .05<=t<.3:status[1]=0 # A separate owner's immunity, scoped to generation1.
    return tuple(status)+(14 if t>=.54 else 7 if t>=.34 else 0,)


def exercise(field_stat='received_dmg_pct',factor=1):
    bm,boss,enemy,registry=prepare(field_stat,factor);observations=[]
    for t,kind,identity,owner,want in actions():
        if kind=='frame':
            events=boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count;bm.tick(t)
            for event in events:
                for name in NAMES:bm.notify(event,t,name)
            # Deliberately retain old canonical names in carrier lists. The
            # generation key must protect refresh/query before drop_enemies.
        else:
            bm.tick(t)
            actor=ActorHandle(0,0) if identity==-1 else ActorHandle(5,identity,boss._runs[0].opens)
            if kind=='kill':land_add(bm,boss,HitEvent(t,NAMES[owner],10,False,'normal'),boss._runs[0].adds[identity].id,t)
            elif kind=='apply':bm.notify('hit_count',t,NAMES[owner],impact=Impact(NAMES[owner],actor,0,2,1))
            else:bm.notify('burst_cast' if kind=='alias' else 'on_attack',t,NAMES[owner],target_context=actor)
        labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
        want=expected_values(t,want,field_stat,factor)
        got=tuple(int(bm.is_stunned(label)) if field_stat=='stun' else bm.get_buffs(NAMES[0],label,t).get('enemy_def_down_pct' if field_stat=='def_pct' else 'received_dmg',0) for label in labels)
        got+= (bm.get_buffs(NAMES[0],'__enemy__',t).get('crit_dmg',0),)
        assert got==want,(t,kind,got,want)
        assert not state(bm).event_stack and not getattr(state(bm),'enemy_query_stack',())
        observations.append(dict(time=t,action=kind,values=got))
        if t==.32:
            stacks={(ab.caster,b.actor.generation):ab.stack for ab in bm._active if ab.effect.get('name')=='vulnerability' for b in getattr(getattr(ab,'enemy_recipient_key',None),'bindings',()) if b.actor.kind==5 and b.actor.identity==0}
            assert stacks[NAMES[0],1]==3 and stacks[NAMES[0],2]==2 and stacks[NAMES[1],1]==1,stacks
    assert sum(boss.add_dealt.values())==10
    return dict(passed=True,observations=observations,actual_add_damage=10,generations=2,named_and_direct_refresh=True,old_names_retained=True)
