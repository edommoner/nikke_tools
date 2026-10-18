"""One authored overlapping-recipient lifecycle table, independent of characters."""
from enemy_recipient_cases import manager,NAMES,field,world_patterns
from calculator.boss_pattern import BossScript,validate
from world_actor_runtime import registry_for
from effect_runtime import state
from impact_runtime import land_add
from calculator.sim_result import HitEvent
from impact_specs import ActorHandle


def prepare():
    effect=field('shared','received_dmg_pct',10,'burst_cast',duration=.1,target='all_enemies');effect['max_trigger']=6
    child=field('child','crit_dmg',1,'event:shared',stack=100,duration=1,target='self')
    bm=manager([effect,child],[0,0]);enemy={'def':0,'core_px':0}
    boss=BossScript(validate(world_patterns()),enemy,lambda *_:True);registry_for(bm,boss)
    return bm,boss,enemy,effect


def actions():
    return [(0,'frame',(),(0,0,0,0)),(.01,'apply',(-1,0),(10,10,0,2)),
        (.04,'apply',(0,1),(10,20,10,4)),(.08,'apply',(1,),(10,20,20,5)),
        (.12,'tick',(),(0,20,20,5)),(.15,'apply',(0,),(0,10,20,6)),
        (.19,'tick',(),(0,10,0,6)),(.2,'kill',(0,),(0,0,0,6)),
        (.3,'frame',(),(0,0,0,6)),(.31,'apply',(0,1),(0,10,10,8)),
        (.32,'apply',(0,0),(0,20,10,9)),(.33,'apply',(-1,),(0,20,10,9)),
        (.415,'tick',(),(0,20,0,9)),(.43,'tick',(),(0,0,0,9))]


def exercise():
    bm,boss,enemy,effect=prepare();observations=[]
    for t,action,identities,want in actions():
        if action=='frame':
            boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count
        bm.tick(t)
        labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
        selected=[labels[i+1] for i in identities]
        if action=='apply':bm._activate(effect,NAMES[0],t,targets=selected)
        if action=='kill':land_add(bm,boss,HitEvent(t,NAMES[0],10,False,'normal'),selected[0],t)
        got=tuple(bm.get_buffs(NAMES[0],label,t).get('received_dmg',0) for label in labels)+(bm.get_buffs(NAMES[0],'__enemy__',t).get('crit_dmg',0),)
        assert got==want,(t,action,got,want)
        assert not state(bm).event_stack and not getattr(state(bm),'enemy_activation_stack',())
        observations.append(dict(time=t,action=action,values=got))
    assert bm._trigger_counts[id(effect)]==6
    assert sum(boss.add_dealt.values())==10
    return dict(passed=True,observations=observations,original_activations=6,recipient_applications=9,actual_add_damage=10)


def selector_prepare(nested=False):
    all_field=field('shared','received_dmg_pct',10,'burst_cast',duration=.1,target='all_enemies');all_field['max_trigger']=3
    one_field=field('shared','received_dmg_pct',10,'hit_count:1',duration=.1,target='target');one_field['max_trigger']=3
    child=field('child','crit_dmg',1,'event:shared',stack=100,duration=1,target='self')
    effects=[all_field,one_field,child]
    if nested:
        extra=field('nested','received_dmg_pct',2,'event:shared',stack=1,duration=-1,target='all_enemies');extra['max_trigger']=1;effects.append(extra)
    bm=manager(effects,[0]*len(effects));enemy={'def':0,'core_px':0};boss=BossScript(validate(world_patterns()),enemy,lambda *_:True);registry_for(bm,boss)
    bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,bm.enemy_has_state,caster)
    return bm,boss,enemy


def selector_actions(nested=False):
    rows=[(0,'frame',None,(0,0,0,0)),(.01,'all',None,(10,10,10,3)),(.04,'one',0,(10,20,10,4)),(.08,'one',1,(10,20,20,5)),
        (.12,'tick',None,(0,20,20,5)),(.15,'all',None,(10,10,30,8)),(.2,'kill',0,(10,0,30,8)),(.3,'frame',None,(0,0,0,8)),
        (.31,'all',None,(10,10,10,11)),(.32,'one',0,(10,20,10,12)),(.33,'one',0,(10,20,10,12)),
        (.415,'tick',None,(0,20,0,12)),(.43,'tick',None,(0,0,0,12))]
    for t,kind,identity,want in rows:
        if nested and t>=.01:want=(want[0]+2,want[1]+(2 if t<.2 else 0),want[2]+(2 if t<.3 else 0),want[3])
        yield t,kind,identity,want


def selector_exercise(nested=False):
    bm,boss,enemy=selector_prepare(nested);observations=[]
    for t,kind,identity,want in selector_actions(nested):
        if kind=='frame':boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count
        bm.tick(t)
        if kind=='all':bm.notify('burst_cast',t,NAMES[0])
        if kind=='one':bm.notify('hit_count',t,NAMES[0],target_context=ActorHandle(5,identity,1 if t<.3 else 2))
        if kind=='kill':land_add(bm,boss,HitEvent(t,NAMES[0],10,False,'normal'),boss._runs[0].adds[identity].id,t)
        labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
        got=tuple(bm.get_buffs(NAMES[0],label,t).get('received_dmg',0) for label in labels)+(bm.get_buffs(NAMES[0],'__enemy__',t).get('crit_dmg',0),)
        assert got==want,(nested,t,kind,got,want)
        observations.append(dict(time=t,action=kind,values=got))
    return dict(passed=True,observations=observations,nested=nested)


def order_prepare():
    ordered=field('ordered','received_dmg_pct',1,'burst_cast',stack=1,duration=1,target='all_enemies');ordered.update(scaling='stack_count',scaling_ref='ordinal')
    ordinal=field('ordinal','crit_dmg',1,'battle_start',stack=-1,duration=2,target='self');ordinal['trigger']['timing'].append('event:ordered')
    bm=manager([ordered,ordinal],[0,0]);enemy={'def':0,'core_px':0}
    raw=[dict(id='late',kind='summon',delay=.1,spec=dict(count=1,hp=10)),dict(id='early',kind='summon',spec=dict(count=1,hp=10))]
    boss=BossScript(validate(raw),enemy,lambda *_:True);registry_for(bm,boss);bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,bm.enemy_has_state,caster)
    return bm,boss,enemy,raw


def order_exercise():
    bm,boss,enemy,raw=order_prepare();boss.begin_frame(0,enemy);bm.notify('battle_start',0,NAMES[0]);boss.begin_frame(.1,enemy);bm.tick(.11);bm.notify('burst_cast',.11,NAMES[0])
    labels=['__enemy__']+[r.adds[0].id for r in boss._runs]
    got=[bm.get_buffs(NAMES[0],label,.11).get('received_dmg',0) for label in labels]
    assert got==[1,3,2],got
    assert bm.get_buffs(NAMES[0],'__enemy__',.11).get('crit_dmg',0)==4
    return dict(passed=True,values=got,spawn_order=[-1,1,0])
