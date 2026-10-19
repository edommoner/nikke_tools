"""Synchronize reference-driven maximum HP at outer execution boundaries.
Grants retain native named/stack-child ordering. Crossings observe one actor at
one time; a silent final pass publishes child-mutated rates without edge reentry.
"""
from functools import wraps
HP_STATS=frozenset({'max_hp_pct','max_hp_only_pct','hp_caster_based_pct','hp_only_caster_based_pct'})

def is_reference_health(effect):
    return effect.get('type')=='buff' and effect.get('stat') in HP_STATS and effect.get('scaling')=='stack_count' and bool(effect.get('scaling_ref'))

def enabled(manager):
    result=getattr(manager,'_nikke_reference_health_defined',None)
    if result is None:
        result=any(is_reference_health(e) for e,_ in manager._effects)
        manager._nikke_reference_health_defined=result
    return result

def synchronize(manager,t):
    hp=manager.state.get('hp')
    if not hp or getattr(manager,'_nikke_reference_health_syncing',False):return
    previous_time=manager._cur_t;manager._cur_t=t;manager._nikke_reference_health_syncing=True
    def actor(name):
        if name not in hp:return
        if manager.is_down(name):hp[name]=0;manager.state['hp_pct'][name]=0;return
        maximum=manager.effective_max_hp(name)
        if maximum<=0:return
        hp[name]=max(0.0,min(hp[name],maximum));manager.sync_hp(name)
    try:
        for name in manager.squad_names:actor(name)
        # Native sync_hp suppresses edge recursion while delivering crossings.
        # A callback can mutate another reference; publish the final derived
        # state under the same suppression, after all crossing observers finish.
        guard=manager._in_hp_edge;manager._in_hp_edge=True
        try:
            for name in manager.squad_names:actor(name)
        finally:manager._in_hp_edge=guard
    finally:
        manager._nikke_reference_health_syncing=False;manager._cur_t=previous_time

def execute(manager,t,callback):
    if not enabled(manager):return callback()
    depth=getattr(manager,'_nikke_reference_health_depth',0);previous_time=manager._cur_t
    manager._cur_t=t;manager._nikke_reference_health_depth=depth+1
    try:
        if depth==0:synchronize(manager,t)
        result=callback()
        if depth==0:synchronize(manager,t)
        return result
    finally:
        manager._nikke_reference_health_depth=depth;manager._cur_t=previous_time

def install():
    from calculator.buff_manager import BuffManager
    if getattr(BuffManager,'_nikke_reference_health',False):return
    original_notify=BuffManager.notify;original_activate=BuffManager._activate
    original_dispatch=BuffManager._dispatch_instant;original_tick=BuffManager.tick
    original_damage=BuffManager.register_damage_handler;original_reset=BuffManager.reset
    original_sync=BuffManager.sync_hp
    @wraps(original_notify)
    def notify(self,event,t,caster,*args,**kwargs):
        return execute(self,t,lambda:original_notify(self,event,t,caster,*args,**kwargs))
    @wraps(original_activate)
    def activate(self,effect,caster,t,*args,**kwargs):
        if is_reference_health(effect):self._nikke_reference_health_defined=True
        return execute(self,t,lambda:original_activate(self,effect,caster,t,*args,**kwargs))
    @wraps(original_dispatch)
    def dispatch(self,effect,caster,t,*args,**kwargs):
        return execute(self,t,lambda:original_dispatch(self,effect,caster,t,*args,**kwargs))
    @wraps(original_tick)
    def tick(self,t,*args,**kwargs):
        if enabled(self):synchronize(self,t)
        result=original_tick(self,t,*args,**kwargs)
        if enabled(self):synchronize(self,t)
        return result
    @wraps(original_damage)
    def register_damage(self,handler):
        if handler is None:return original_damage(self,None)
        @wraps(handler)
        def damage(effect,caster,t,*args,**kwargs):
            return execute(self,t,lambda:handler(effect,caster,t,*args,**kwargs))
        return original_damage(self,damage)
    @wraps(original_sync)
    def sync_hp(self,name):
        hp=self.state.get('hp',{}).get(name)
        seen=getattr(self,'_nikke_numeric_hp_seen',None)
        if seen is None:seen={};self._nikke_numeric_hp_seen=seen
        if hp is not None and (name not in seen or seen[name]!=hp):
            seen[name]=hp;self._bump_value_version()
        return original_sync(self,name)
    @wraps(original_reset)
    def reset(self,*args,**kwargs):
        self._nikke_reference_health_defined=None;self._nikke_reference_health_depth=0;self._nikke_numeric_hp_seen={}
        return original_reset(self,*args,**kwargs)
    BuffManager.notify=notify;BuffManager._activate=activate;BuffManager._dispatch_instant=dispatch
    BuffManager.tick=tick;BuffManager.register_damage_handler=register_damage;BuffManager.reset=reset
    BuffManager.sync_hp=sync_hp
    BuffManager._nikke_reference_health=True
