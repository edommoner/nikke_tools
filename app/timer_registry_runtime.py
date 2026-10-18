"""One snapshot/ownership executor for damage and instant periodic registrations.

The mapping owns a clock identity. A deadline is consumed before callbacks;
children may cancel or reschedule without being overwritten. A phase-preserving
refresh keeps its clock, while a new clock waits for the next pass. Timing
boundaries and callback context remain family policies.
"""
from effect_runtime import state
from impact_specs import EventFrame
from world_actor_runtime import sample_control_aim


class Registration(tuple):
    def __new__(cls,values,clock):
        result=super().__new__(cls,values);result.clock=clock;return result


class TimerRegistry(dict):
    """DOT refreshes with the same next deadline continue the same clock.

    Removing a registration ends that clock even if a subsequent registration
    has equal tuple values. Other timer families always replace their clock.
    """
    def __init__(self,values=(),*,preserve_phase=False):
        super().__init__();self.preserve_phase=preserve_phase;self.update(values)
    def __setitem__(self,key,value):
        previous=self.get(key)
        preserve=self.preserve_phase(key) if callable(self.preserve_phase) else self.preserve_phase
        same=preserve and previous is not None and previous[:2]==tuple(value)[:2]
        super().__setitem__(key,Registration(value,previous.clock if same else object()))
    def update(self,values=(),**kw):
        for key,value in dict(values,**kw).items():self[key]=value


def owns(current,snapshot):
    return current is snapshot or isinstance(current,Registration) and isinstance(snapshot,Registration) and current.clock is snapshot.clock


def execute(manager,t,*,damage=False):
    timers=manager._dot_timers if damage else manager._instant_timers
    if not timers or damage and not manager._damage_handler:return
    for eid,registration in list(timers.items()):
        current=timers.get(eid)
        if not owns(current,registration):continue
        registration=current
        caster,next_t,expires_at=registration
        effect=manager._eff_by_id.get(eid)
        if effect is None:
            del timers[eid];continue
        if damage:
            limit=expires_at+(-1e-6 if effect.get('tick_start')=='immediate' else 1e-6)
            expired=next_t>limit
        else:expired=t>=expires_at
        if expired:
            del timers[eid];continue
        if t<next_t:continue
        # Publish the consumed deadline before children. A phase-preserving DOT
        # refresh must see the next deadline, rather than refire the current one.
        timers[eid]=(caster,next_t+effect.get('tick_interval',1.0),expires_at)
        committed=timers[eid]
        try:
            if damage:
                manager._damage_handler(effect,caster,expires_at-1e-4 if t>=expires_at else t)
            else:
                runtime=state(manager)
                runtime.event_stack.append(EventFrame('periodic_instant',caster,t,target=sample_control_aim(manager,caster)))
                try:
                    conds=effect['trigger'].get('condition',[])
                    if effect.get('duration')!=-1 or not conds or manager._runtime_condition_ok(conds,caster,caster,caster,t):
                        manager._dispatch_instant(effect,caster,t,from_tick=True)
                finally:runtime.event_stack.pop()
        except BaseException:
            if timers.get(eid) is committed:dict.__setitem__(timers,eid,registration)
            raise


def tick_damage(manager,t):execute(manager,t,damage=True)
def tick_instant(manager,t):execute(manager,t)
