"""Read actual down/revive calls; never resolve targets or query stats in snapshots."""
import copy,random
from contextlib import contextmanager,nullcontext
from unittest.mock import patch
from calculator.buff_manager import BuffManager
from calculator.timeline import CharState
from world_projectile_native import observe as projectile_native
from world_frame_native import roster_names


@contextmanager
def capture(case):
    names=roster_names(case);events=[];identities={}
    down=BuffManager.knock_down;revive=BuffManager.revive;notify=BuffManager.notify
    on_down=CharState.on_down;on_revive=CharState.on_revive;resolve=BuffManager._resolve_target
    def owner(name):return names.index(name)
    def state(bm):
        active=[]
        for ab in bm._active:
            identity=identities.setdefault(id(ab),(ab,len(identities)+1))[1]
            active.append(dict(identity=identity,name=ab.effect.get('name',''),caster=owner(ab.caster),stat=ab.effect.get('stat'),recipients=None if ab.target_chars is None else [owner(n) if n in names else n for n in ab.target_chars],stack=ab.stack,activated=ab.activated_at,end=ab.expires_at))
        return dict(down=[i for i,n in enumerate(names) if n in bm.state.get('down',())],hp=[bm.state['hp'][n] for n in names],hp_pct=[bm.state['hp_pct'][n] for n in names],active=active,lost={str(owner(n)):[dict(name=e.get('name',''),caster=owner(caster)) for e,caster in lost] for n,lost in bm._down_lost.items()},gauges=copy.deepcopy(bm.state.get('gauges',{})),stacks=copy.deepcopy(bm.state.get('stacks',{})),event_counts=copy.deepcopy(bm._event_counts))
    def transition(original,label):
        def call(bm,name,t,*args):
            events.append(dict(kind='before-'+label,owner=owner(name),time=t,state=state(bm)))
            result=original(bm,name,t,*args)
            events.append(dict(kind='after-'+label,owner=owner(name),time=t,state=state(bm)))
            return result
        return call
    def resolved(bm,target,caster):
        observed=isinstance(target,str) and target.startswith('allies_down_')
        before=list(random.getstate()[1]) if observed and target.startswith('allies_down_class_random:') else None
        result=resolve(bm,target,caster)
        if observed:
            events.append(dict(kind='target',owner=owner(caster),selector=target,result=[owner(n) for n in result],random_before=before,random_after=list(random.getstate()[1]) if before is not None else None))
        return result
    def notified(bm,event,t,caster,**kw):
        if event in ('received_hit','event:lethal_hit','event:self_down','event:ally_down') or event.startswith('hp_below:'):
            events.append(dict(kind='notify',event=event,owner=owner(caster),time=t))
        return notify(bm,event,t,caster,**kw)
    def action(original,label):
        def call(actor,t,bm):
            result=original(actor,t,bm)
            events.append(dict(kind=label,owner=owner(actor.name),time=t,ammo=actor.ammo,next_fire=actor.next_fire_time,reload_until=actor.reloading_until,post_reload=actor._post_reload_end_t,charge_phase=actor._charge_phase,charge_full=actor._charge_full_t,hold_release=actor._hold_release_t,cover_until=actor._cover_until,cover_until_reload=actor._cover_until_reload,charging=bm.state.get('charging',{}).get(actor.name)))
            return result
        return call
    dispatch=BuffManager._dispatch_instant
    def source_identity(effect,caster):
        index=effect.get('_portable_observer_row')
        if type(index) is not int or not 0<=index<len(case['effects']) or case['effects'][index]['name']!=effect['name'] or case['names'][case['owners'][index]]!=caster:raise ValueError('Original revival attempt identity mismatch')
        return index
    def clocks(bm):
        return [dict(row=e['_portable_observer_row'],due=bm._next_fire[id(e)][0],interval=bm._next_fire[id(e)][1]) for e,_ in bm._effects if id(e) in bm._next_fire]
    def attempted(bm,effect,caster,t,*args,**kwargs):
        if effect.get('stat')=='revive':events.append(dict(kind='revive-attempt',row=source_identity(effect,caster),owner=owner(caster),time=t))
        reduction=None
        if effect.get('stat')=='skill_cooldown_reduce_pct' and case.get('observe_skill_clocks'):
            reduction=dict(kind='skill-clock-reduction',row=source_identity(effect,caster),owner=owner(caster),time=t,before=clocks(bm))
        result=dispatch(bm,effect,caster,t,*args,**kwargs)
        if reduction is not None:
            reduction['after']=clocks(bm);events.append(reduction)
        return result
    attempts=patch.object(BuffManager,'_dispatch_instant',attempted) if case.get('observe_revival_attempts') else nullcontext()
    with attempts,patch.object(BuffManager,'_resolve_target',resolved),patch.object(BuffManager,'knock_down',transition(down,'down')),patch.object(BuffManager,'revive',transition(revive,'revive')),patch.object(BuffManager,'notify',notified),patch.object(CharState,'on_down',action(on_down,'action-down')),patch.object(CharState,'on_revive',action(on_revive,'action-revive')):
        yield events

def observe(case):
    with capture(case) as events:
        native,trace=projectile_native(case)
    native['revival_events']=events
    return native,trace
