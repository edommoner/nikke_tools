"""One authored receiver-mutation lifecycle; no per-character test matrix."""
from enemy_recipient_cases import manager,NAMES,field,world_patterns
from calculator.boss_pattern import BossScript,validate
from world_actor_runtime import registry_for
from impact_specs import ActorHandle
from impact_runtime import land_add
from calculator.sim_result import HitEvent
from effect_runtime import state


def instant(name,stat,event,*,target='target',reference=None,value=1,**extra):
    effect=dict(name=name,source='스킬1',type='instant',stat=stat,fixed_value=value,target=target,trigger=dict(timing=[event],condition=[]),**extra)
    if reference is not None:effect['target_effect']=reference
    return effect


def prepare():
    a=field('field','received_dmg_pct',10,'burst_cast',duration=1,target='all_enemies');a['polarity']='harmful'
    b=field('field child','received_dmg_pct',2,'burst_cast',duration=1,target='all_enemies');b['polarity']='harmful'
    immune=field('immune','stack_change_immune',0,'hit_count:1',stack=1,duration=1)
    ended=field('ended','crit_dmg',1,'event:state_end:field',stack=100,duration=2,target='self');ended['trigger']['timing'].append('event:state_end:field child')
    effects=[a,b,immune,ended,
        instant('up','debuff_stack_add','on_attack',target='all_enemies',reference='field'),
        instant('down','debuff_stack_remove','full_charge',target='all_enemies',reference='field'),
        instant('clear','remove_named_buff','last_bullet',reference='field',remove_scope='target'),
        instant('clear-child','remove_named_buff','crit_hit',reference='field child',remove_scope='target'),
        instant('extend','named_buff_duration_extend','full_charge_fire',reference='field',value=.5),
        instant('extend-all','named_buff_duration_extend','event:cover_hit',target='all_enemies',reference='field',value=.5),
        instant('clean','debuff_cleanse','pellet_hit'),
        instant('clean-all','debuff_cleanse','core_hit',target='all_enemies'),
        instant('global','remove_named_buff','full_charge_hit',target='self',reference='field'),
        instant('global-child','remove_named_buff','event:cover_healed',target='self',reference='field child'),
        instant('generic','debuff_stack_remove','event:shield_applied',target='all_enemies')]
    bm=manager(effects,[0,0,1]+[0]*(len(effects)-3));enemy={'def':0,'core_px':0}
    boss=BossScript(validate(world_patterns()),enemy,lambda *_:True);registry_for(bm,boss)
    bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,bm.enemy_has_state,caster)
    return bm,boss,enemy


def actions():
    return [(0,'frame',None,(0,0,0,0)),(.01,'apply',None,(12,12,12,0)),(.02,'apply',None,(24,24,24,0)),
        (.025,'immune',0,(24,24,24,0)),(.03,'up',None,(34,24,34,0)),(.04,'down',1,(24,24,24,0)),
        (.05,'clear',-1,(4,24,24,1)),(.06,'extend',1,(4,24,24,1)),(.07,'clean',-1,(0,24,24,1)),
        (.08,'kill',0,(0,0,24,1)),(.3,'frame',None,(0,0,0,1)),(.31,'apply',None,(12,12,12,1)),
        (.32,'up',0,(22,22,22,1)),(.33,'down',None,(12,12,12,1)),(.332,'down',None,(2,2,2,1)),(.335,'generic',None,(12,12,12,1)),
        (.34,'extend-all',None,(12,12,12,1)),(.35,'clean-all',None,(2,2,2,1)),(.36,'clear-child',1,(2,2,0,2)),
        (.37,'global',None,(2,2,0,4)),(.38,'global-child',None,(0,0,0,8)),(.6,'frame',None,(0,0,0,8))]


EVENTS={'apply':('burst_cast',0),'immune':('hit_count',1),'up':('on_attack',0),'down':('full_charge',0),'clear':('last_bullet',0),'clear-child':('crit_hit',0),
    'extend':('full_charge_fire',0),'extend-all':('event:cover_hit',0),'clean':('pellet_hit',0),'clean-all':('core_hit',0),'global':('full_charge_hit',0),'global-child':('event:cover_healed',0),'generic':('event:shield_applied',0)}


def exercise():
    bm,boss,enemy=prepare();observations=[]
    for t,action,identity,want in actions():
        if action=='frame':boss.begin_frame(t,enemy);bm.state['enemy_count']=boss.enemy_count
        bm.tick(t)
        if action=='kill':land_add(bm,boss,HitEvent(t,NAMES[0],10,False,'normal'),boss._runs[0].adds[identity].id,t)
        elif action in EVENTS:
            event,owner=EVENTS[action];context=None if identity is None else ActorHandle(0,0) if identity==-1 else ActorHandle(5,identity,1 if t<.3 else 2)
            bm.notify(event,t,NAMES[owner],target_context=context)
        labels=['__enemy__']+[a.id for a in boss._runs[0].adds]
        got=tuple(bm.get_buffs(NAMES[0],label,t).get('received_dmg',0) for label in labels)+(bm.get_buffs(NAMES[0],'__enemy__',t).get('crit_dmg',0),)
        assert got==want,(t,action,got,want)
        assert not state(bm).event_stack
        observations.append(dict(time=t,action=action,values=got))
    return dict(passed=True,observations=observations)
