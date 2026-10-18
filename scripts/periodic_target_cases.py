"""Authored firing-time selection and registration ownership, not CPU replays."""
from enemy_recipient_cases import manager,NAMES,field
from enemy_mutation_cases import instant
from calculator.boss_pattern import BossScript,validate
from calculator.sim_result import HitEvent
from impact_runtime import land_add
from impact_specs import ActorHandle
from world_actor_runtime import registry_for
from effect_runtime import state


def world_patterns():
    return [dict(id='wave',kind='summon',spec=dict(count=2,hp=10),until=dict(time=.375),after=['start','wave'],repeat=2)]


def prepare(policy='current'):
    modifier=field('payload','received_dmg_pct',10,'battle_start',stack=5,duration=2,target='all_enemies');modifier['trigger']['timing'].append('event:shield_applied');modifier['polarity']='harmful'
    up=instant('periodic-up','debuff_stack_add','burst_cast',target={'current':'target','boss':'boss','all':'all_enemies'}[policy],reference='payload',value=1,tick_interval=.125,duration=-1 if policy=='current' else .5)
    effects=[modifier,up]
    if policy=='current':
        up['trigger']['condition']=['self_state:gate']
        gate=field('gate','',0,'battle_start',stack=1,duration=.5,target='self');gate['trigger']['timing'].append('full_burst_start')
        clean=instant('periodic-clean','debuff_cleanse','full_charge',target='target',value=1,tick_interval=.25,duration=.75)
        effects += [gate,clean]
    bm=manager(effects,[0]*len(effects));enemy={'def':0,'core_px':0};boss=BossScript(validate(world_patterns()),enemy,lambda *_:True)
    registry_for(bm,boss);bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,bm.enemy_has_state,caster)
    return bm,boss,enemy


def actions(policy='current'):
    if policy!='current':
        yield from [(0,'frame',None,(0,0,0)),(0,'start',None,(10,10,10)),(.125,'tick',None,(20,20 if policy=='all' else 10,20 if policy=='all' else 10)),
            (.25,'tick',None,(30,30 if policy=='all' else 10,30 if policy=='all' else 10)),(.375,'frame',None,(40,0,0)),(.4,'apply',None,(50,10,10)),
            (.5,'tick',None,(50,10,10)),(.75,'frame',None,(50,0,0))]
        return
    yield from [(0,'frame',None,(0,0,0)),(0,'aim',(5,1,1),(0,0,0)),(0,'start',None,(10,10,10)),(.125,'tick',None,(10,10,20)),
        (.1875,'aim',(0,0,1),(10,10,20)),(.25,'tick',None,(20,10,20)),(.28125,'kill',1,(20,10,0)),(.3125,'register-clean',None,(20,10,0)),
        (.34375,'aim',(5,0,1),(20,10,0)),(.375,'frame',None,(30,0,0)),(.4,'apply',None,(40,10,10)),(.4375,'aim',(5,0,2),(40,10,10)),
        (.5,'tick',None,(40,10,10)),(.5625,'tick',None,(40,0,10)),(.59375,'gate',None,(40,0,10)),(.6,'aim',(5,1,2),(40,0,10)),
        (.625,'tick',None,(40,0,20)),(.75,'frame',None,(50,0,0)),(.8125,'tick',None,(0,0,0)),(.875,'tick',None,(0,0,0)),(1.0,'apply',None,(10,0,0)),
        (1.0625,'tick',None,(10,0,0)),(1.125,'tick',None,(10,0,0))]


def exercise(policy='current'):
    bm,boss,enemy=prepare(policy);observations=[]
    for t,action,value,want in actions(policy):
        if action=='frame':boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count
        bm.tick(t)
        if action=='aim':bm.set_control_aim(NAMES[0],ActorHandle(*value))
        elif action=='start':bm.notify('battle_start',t,NAMES[0]);bm.notify('burst_cast',t,NAMES[0])
        elif action in ('apply','gate','register-clean'):bm.notify({'apply':'event:shield_applied','gate':'full_burst_start','register-clean':'full_charge'}[action],t,NAMES[0])
        elif action=='kill':land_add(bm,boss,HitEvent(t,NAMES[0],10,False,'normal'),boss._runs[0].adds[value].id,t)
        labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
        got=tuple(bm.get_buffs(NAMES[0],label,t).get('received_dmg',0) for label in labels)
        assert got==want,(policy,t,action,got,want)
        assert not state(bm).event_stack
        observations.append(dict(time=t,action=action,values=got))
    return dict(passed=True,policy=policy,observations=observations)


def reentrant_prepare():
    payload=field('payload','received_dmg_pct',10,'battle_start',stack=1,duration=2,target='boss');payload['trigger']['timing'].append('event:shield_applied')
    ended=field('ended','crit_dmg',1,'event:state_end:payload',stack=100,duration=2,target='self')
    timer=instant('clear-timer','remove_named_buff','burst_cast',target='boss',reference='payload',remove_scope='target',tick_interval=.125,duration=.375);timer['trigger']['timing'].append('event:state_end:payload')
    return manager([payload,ended,timer],[0,0,0])


def reentrant_actions():
    return [(0,'start',(10,0)),(.140625,'tick',(0,1)),(.25,'apply',(10,1)),(.265625,'tick',(0,2)),
        (.375,'apply',(10,2)),(.390625,'tick',(0,3)),(.765625,'tick',(0,3)),(.78125,'apply',(10,3)),(.9,'tick',(10,3))]


def reentrant_exercise():
    bm=reentrant_prepare();observations=[]
    for t,action,want in reentrant_actions():
        bm.tick(t)
        if action=='start':bm.notify('battle_start',t,NAMES[0]);bm.notify('burst_cast',t,NAMES[0])
        if action=='apply':bm.notify('event:shield_applied',t,NAMES[0])
        buffs=bm.get_buffs(NAMES[0],'__enemy__',t);got=(buffs.get('received_dmg',0),buffs.get('crit_dmg',0));assert got==want,(t,action,got,want)
        assert not state(bm).event_stack
        observations.append(dict(time=t,action=action,values=got))
    return dict(passed=True,observations=observations)


def predicate_prepare():
    bm,boss,enemy=prepare('all');effects=[e for e,n in bm._effects]
    effects[1]['duration']=-1;effects[1]['trigger']['condition']=['target_state:proof']
    effects.append(field('proof','',0,'hit_count:1',stack=1,duration=2,target='target'))
    bm=manager(effects,[0]*len(effects));registry_for(bm,boss);bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,bm.enemy_has_state,caster)
    return bm,boss,enemy


def predicate_actions():
    return [(0,'frame',None,(0,0,0)),(0,'aim',(5,1,1),(0,0,0)),(0,'start',None,(10,10,10)),(.125,'tick',None,(20,20,20)),
        (.1875,'aim',(0,0,1),(20,20,20)),(.25,'tick',None,(20,20,20)),(.3125,'aim',(5,1,1),(20,20,20)),(.375,'frame',None,(20,0,0)),
        (.4,'apply',None,(30,10,10)),(.4375,'aim',(5,1,2),(30,10,10)),(.5,'tick',None,(30,10,10)),(.5625,'mark',(5,1,2),(30,10,10)),
        (.625,'tick',None,(40,20,20)),(.75,'frame',None,(40,0,0))]


def predicate_exercise():
    bm,boss,enemy=predicate_prepare();observations=[]
    for t,action,value,want in predicate_actions():
        if action=='frame':boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count
        bm.tick(t)
        if action=='aim':bm.set_control_aim(NAMES[0],ActorHandle(*value))
        elif action=='start':
            actor=ActorHandle(5,1,1);bm.notify('battle_start',t,NAMES[0]);bm.notify('hit_count',t,NAMES[0],target_context=actor);bm.notify('burst_cast',t,NAMES[0],target_context=actor)
        elif action=='mark':bm.notify('hit_count',t,NAMES[0],target_context=ActorHandle(*value))
        elif action=='apply':bm.notify('event:shield_applied',t,NAMES[0])
        labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
        got=tuple(bm.get_buffs(NAMES[0],label,t).get('received_dmg',0) for label in labels);assert got==want,(t,action,got,want)
        assert not state(bm).event_stack
        observations.append(dict(time=t,action=action,values=got))
    return dict(passed=True,observations=observations)


def sibling_prepare():
    switch=field('switch','',0,'battle_start',stack=1,duration=2,target='boss');switch['trigger']['timing'].append('event:shield_applied')
    payload=field('payload','received_dmg_pct',10,'battle_start',stack=100,duration=2,target='boss')
    first=instant('first-clock','remove_named_buff','burst_cast',target='boss',reference='switch',remove_scope='target',tick_interval=.125,duration=.5)
    second=instant('second-clock','debuff_stack_add','burst_cast',target='boss',reference='payload',tick_interval=.125,duration=.5);second['trigger']['timing'].append('event:state_end:switch')
    return manager([switch,payload,first,second],[0,0,0,0])


def sibling_actions():
    return [(0,'start',(10,0)),(.140625,'tick',(10,0)),(.25,'apply',(10,0)),(.265625,'tick',(20,0)),
        (.375,'tick',(20,0)),(.390625,'tick',(20,0)),(.5,'tick',(30,0)),(.875,'tick',(30,0))]


def sibling_exercise():
    bm=sibling_prepare();observations=[]
    for t,action,want in sibling_actions():
        bm.tick(t)
        if action=='start':bm.notify('battle_start',t,NAMES[0]);bm.notify('burst_cast',t,NAMES[0])
        if action=='apply':bm.notify('event:shield_applied',t,NAMES[0])
        buffs=bm.get_buffs(NAMES[0],'__enemy__',t);got=(buffs.get('received_dmg',0),buffs.get('crit_dmg',0));assert got==want,(t,action,got,want)
        assert not state(bm).event_stack
        observations.append(dict(time=t,action=action,values=got))
    return dict(passed=True,observations=observations)
