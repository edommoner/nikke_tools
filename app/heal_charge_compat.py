"""Declared received-healing accumulator and discharge CPU reference.

This is distinct from the v40 excess-healing damage buffer. Each carrier has a
scalar pool, source final-ATK snapshot and fresh quantity on each activation.
Positive allocated body healing enters before the HP clamp, including full HP.
Live named maximum-accumulation bonuses increase deposit capacity; a decrease
does not destroy already collected healing. A discharge consumes matching owner
and name pools before delivering a new heal to each ordered target. Each new
heal receives current source/recipient multipliers and the v41 sharing model.
Repair, revival and max-HP grants do not enter the pool. Explicit state-end
notifications retain a removed pool for a subsequent named discharge, whereas
cleanse/down without such a callback discards it. These interactions, snapshot
placement and capacity-change rules are declared models, not all game-verified.
"""
from effect_runtime import CATALOG,Handler,pool,state,active_carrier

STAT='heal_overcharge_store_atk_pct'
BOOST='accumulate_max_scale_pct'

def records(self):
    result=pool(self,'healing_charge')
    self._heal_charge_records=result  # Compatibility view for read-only observers.
    return result

def snapshot(self,eff,caster,t):
    if eff.get('type')!='buff' or eff.get('stat')!=STAT:return
    ab=active_carrier(self,eff,caster)
    if ab is None:return
    ab.heal_charge_base_cap=max(0.0,self.final_atk(caster,t)*(self._get_value(eff,ab,caster) or 0.0)/100.0)
    ab.heal_charge_current=0.0;ab.heal_charge_done=False;ab.heal_charge_ended=False
    records(self)[ab.uid]=ab

def capacity(self,ab,t):
    bonus=0.0;name=ab.effect.get('name','')
    for other in self._by_stat(BOOST):
        ref=other.effect.get('target_effect')
        if ref is not None and ref!=name:continue
        if self._live(other,ab.caster,t):bonus+=self._get_value(other.effect,other,ab.caster) or 0.0
    return max(0.0,ab.heal_charge_base_cap*(1.0+bonus/100.0))

def collect(self,name,amount,t):
    if amount<=0 or self.is_down(name):return
    for ab in self._by_stat(STAT):
        if not hasattr(ab,'heal_charge_current') or ab.heal_charge_done or not self._live(ab,name,t):continue
        room=max(0.0,self.heal_charge_capacity(ab,t)-ab.heal_charge_current)
        ab.heal_charge_current+=min(amount,room)

def latch_end(self,name,caster):
    active={ab.uid for ab in self._active}
    for ab in records(self).values():
        if ab.uid in active or ab.caster!=caster or ab.effect.get('name','')!=name or ab.heal_charge_done:continue
        if self.is_down(caster):ab.heal_charge_done=True;ab.heal_charge_current=0.0
        else:ab.heal_charge_ended=True

def discard_removed(self,before):
    state(self).retire(self,'healing_charge',before,lambda record:record.heal_charge_ended)

def take(self,name,caster,t):
    if self.is_down(caster):return 0.0
    active={ab.uid for ab in self._active};amount=0.0
    for ab in records(self).values():
        if ab.caster!=caster or ab.effect.get('name','')!=name or ab.heal_charge_done:continue
        if ab.uid not in active and not ab.heal_charge_ended:continue
        amount+=ab.heal_charge_current;ab.heal_charge_current=0.0;ab.heal_charge_done=True;ab.heal_charge_ended=False
    return amount

def discharge(self,eff,caster,t,val):
    # Resolve all original targets before delivery, then consume once. Never
    # query/take a fresh amount per recipient or recursively refill this pool.
    targets=[n for n in (self._resolve_target(eff.get('target','self'),caster) or []) if n in self.squad_names and not self.is_down(n)]
    amount=self.take_heal_charge(eff.get('target_effect',''),caster,t)
    for name in targets:
        heal=amount*self.heal_received_mult(name,t,heal_source=caster)
        self.apply_shared_body_heal(name,heal,t)
        self.notify('event:heal_received',t,name,heal_source=caster)

def before_notify(self,event,t,caster):
    if event.startswith('event:state_end:'):
        self.latch_heal_charge_end(event[len('event:state_end:'):],caster)

def install():
    from calculator import buff_manager as module
    bm=module.BuffManager
    if getattr(bm,'_nikke_heal_charge',False):return
    assert getattr(bm,'_nikke_heal_sharing',False)
    for name,fn in [('snapshot_heal_charge',snapshot),('heal_charge_capacity',capacity),('collect_heal_charge',collect),('latch_heal_charge_end',latch_end),('take_heal_charge',take),('discard_removed_heal_charge',discard_removed)]:setattr(bm,name,fn)
    CATALOG.register('healing_charge',Handler(activate=snapshot,before_body_heal=collect,
        before_notify=before_notify,instant_stat='heal_overcharge_discharge',instant=discharge,
        resource_kind='healing_charge',retain_removed=lambda record:record.heal_charge_ended,
        collect_removed=lambda record:record.heal_charge_done,
        discard_owner_on_down=True))
    module._DIRECT_READ_STATS=module._DIRECT_READ_STATS|{STAT,BOOST}
    bm._nikke_heal_charge=True
