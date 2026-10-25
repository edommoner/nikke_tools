"""Observe actual synchronous force/start/finish calls without repeated target resolution."""
from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def capture(case,*,original=False):
    from calculator import timeline
    from calculator.buff_manager import BuffManager
    from world_frame_native import roster_names
    names=roster_names(case);actors={};requests=[];events=[]
    initialize=timeline.CharState.__init__;start=timeline.CharState._start_reload;finish=timeline.CharState._finish_reload;register=BuffManager.register_instant_handler
    def initialized(self,*args,**kwargs):initialize(self,*args,**kwargs);actors[self.name]=self
    def state(actor):
        return dict(owner=names.index(actor.name),until=actor.reloading_until,ammo=actor.ammo,phase=actor._charge_phase,full_time=actor._charge_full_t,release_time=actor._hold_release_t)
    def started(self,t,bm,*args,**kwargs):
        answer=start(self,t,bm,*args,**kwargs);events.append(dict(kind='start',time=t,**state(self)));return answer
    def finished(self,t,bm,*args,**kwargs):
        answer=finish(self,t,bm,*args,**kwargs);events.append(dict(kind='finish',time=t,**state(self)));return answer
    def registered(manager,stat,handler):
        if stat=='force_reload':
            original_handler=handler
            def forced(effect,caster,t,value):
                if original:
                    from world_original_source_native import identity
                    assert set(actors)==set(names),'Original roster must exist before force handler'
                    row=identity(case,effect,caster);event=dict(row=row,owner=names.index(caster),name=effect['name'],time=t,before=[state(actors[n]) for n in names]);begin=len(events)
                events.append(dict(kind='force',owner=names.index(caster),name=effect.get('name',''),time=t))
                answer=original_handler(effect,caster,t,value)
                if original:
                    event.update(after=[state(actors[n]) for n in names],starts=[e.copy() for e in events[begin:] if e['kind']=='start']);requests.append(event)
                return answer
            handler=forced
        return register(manager,stat,handler)
    result=dict(requests=requests,events=events)
    with patch.object(timeline.CharState,'__init__',initialized),patch.object(timeline.CharState,'_start_reload',started),patch.object(timeline.CharState,'_finish_reload',finished),patch.object(BuffManager,'register_instant_handler',registered):yield result
    assert set(actors)==set(names),'Every original actor must be observed'
    result['final']=[state(actors[n]) for n in names]


def observe(case):
    from world_charge_control_native import observe as charge_native
    with capture(case) as observed:native,trace=charge_native(case)
    native['reload_events']=observed['events'];native['reload_until']=[row['until'] for row in observed['final']]
    return native,trace
