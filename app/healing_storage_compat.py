"""Declared overheal-buffer CPU extension; pinned upstream has no storage model.

The buffer does not change current/max HP or HP-percent predicates. Its capacity
is caster final maximum HP at activation times the parsed percentage. Only excess
body healing fills it; body-bound damage and current-HP drain spend it first.
Expiry loses it. Reapplication keeps quantity, capped to the new capacity.
Distinct carriers fill/spend newest activation first, stable resident tie order.
Snapshot, reapplication and overlap rules are explicit model choices, not proof
of all in-game interactions. ATK-based storage/discharge and heal_split remain
separate unsupported families. Repair, revival and max-HP grants do not fill it.
"""
import ast
from reference_rewrite import rewrite_reference
from effect_runtime import ActivationPreparation
from functools import wraps
from effect_runtime import CATALOG,Handler,pool,active_carrier

STAT='heal_overcharge_store'

def storage_before_burst_heal(effects):
    """Normalize the S3-storage/S2-self-burst-heal pair (currently Marciana).

    Her storage must already exist when the same-cast passive heal lands.
    Keep unrelated clauses, mixed timings and effect object identities intact.
    CPU and GPU both consume these authored definitions; no CPU state replay.
    """
    heals=[i for i,e in enumerate(effects) if e.get('source')=='스킬2' and e.get('type')=='instant' and e.get('stat')=='heal_hp_pct' and e.get('trigger',{}).get('timing')==['burst_cast']]
    if not heals:return effects
    first=heals[0];move=[i for i,e in enumerate(effects) if i>first and e.get('source')=='스킬3' and e.get('type')=='buff' and e.get('stat')==STAT and e.get('trigger',{}).get('timing')==['burst_cast']]
    if not move:return effects
    return effects[:first]+[effects[i] for i in move]+[e for i,e in enumerate(effects[first:],first) if i not in move]

def snapshot(self,eff,caster,t,carrier=None):
    if eff.get('type')!='buff' or eff.get('stat')!=STAT:return
    ab=active_carrier(self,eff,caster,carrier) if carrier is not None else active_carrier(self,eff,caster)
    if ab is None or ab.target_chars is None:return
    capacity=max(0.0,self.effective_max_hp(caster)*(self._get_value(eff,ab,caster) or 0.0)/100.0)
    previous=getattr(ab,'heal_store_current',{}) if t<getattr(ab,'heal_store_expiry',float('-inf')) else {}
    ab.heal_store_capacity={n:capacity for n in ab.target_chars if n in self.squad_names}
    ab.heal_store_current={n:min(max(0.0,previous.get(n,0.0)),cap) for n,cap in ab.heal_store_capacity.items()}
    ab.heal_store_expiry=ab.expires_at
    pool(self,'overheal_storage')[ab.uid]=ab

def slots(self,name,t):
    if self.is_down(name):return []
    result=[]
    for ab in self._by_stat(STAT):
        if not self._live(ab,name,t):continue
        if not hasattr(ab,'heal_store_current'):snapshot(self,ab.effect,ab.caster,t,ab)
        if name in getattr(ab,'heal_store_current',{}):result.append(ab)
    return sorted(result,key=lambda ab:ab.activated_at,reverse=True)

def store_amount(self,name,t):return sum(ab.heal_store_current[name] for ab in slots(self,name,t))
def store_capacity(self,name,t):return sum(ab.heal_store_capacity[name] for ab in slots(self,name,t))

def fill(self,name,amount,t):
    remaining=max(0.0,amount)
    for ab in slots(self,name,t):
        put=min(remaining,max(0.0,ab.heal_store_capacity[name]-ab.heal_store_current[name]))
        ab.heal_store_current[name]+=put;remaining-=put
    return max(0.0,amount)-remaining

def absorb(self,name,amount,t):
    remaining=max(0.0,amount)
    for ab in slots(self,name,t):
        take=min(remaining,ab.heal_store_current[name]);ab.heal_store_current[name]-=take;remaining-=take
    return remaining

def body_heal(self,name,amount,t):
    maximum=self.effective_max_hp(name);base=self.state['base_stats'].get(name,{}).get('hp',0.0);old=self.state['hp'].get(name,base)
    if amount>0:self.fill_heal_storage(name,max(0.0,old+amount-maximum),t)
    return min(old+amount,maximum)

def body_reduce(self,name,old,value,t):
    after=max(old*(1.0-value/100.0),0.0)
    if after>=old:return after
    amount=old-after;remaining=self.absorb_heal_storage(name,amount,t)
    return after+(amount-remaining)

class Rewrite(ActivationPreparation):
    def __init__(self):self.stack=[];self.protection_rewrites=0;self.counts=dict(heal_source=0,body_heal=0,body_reduce=0,incoming_absorb=0,snapshot=0,prepare_new=0,prepare_refresh=0,carrier_lookup=0,hp_recipients=0)
    def visit_FunctionDef(self,node):
        self.stack.append(node.name);self.generic_visit(node);self.stack.pop();return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and node.func.attr=='heal_received_mult':
            assert len(node.args)==2 and not node.keywords
            source='caster' if 'handle_heal_hp_pct' in self.stack else 'ev.caster'
            node.keywords.append(ast.keyword(arg='heal_source',value=ast.parse(source,mode='eval').body));self.counts['heal_source']+=1
        return node
    def visit_Assign(self,node):
        self.generic_visit(node)
        if self.stack[-1]=='_activate' and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('_ab','ab_new') and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='next':
            node.value=ast.parse('self.effect_runtime_carrier(eff,caster,_runtime_carrier)',mode='eval').body;self.counts['carrier_lookup']+=1
        if len(node.targets)==1 and isinstance(node.targets[0],ast.Subscript) and isinstance(node.targets[0].value,ast.Name) and node.targets[0].value.id=='hp':
            if self.stack[-1] in ('handle_heal_hp_pct','_apply_lifesteal'):
                who='name' if self.stack[-1]=='handle_heal_hp_pct' else 'ev.caster'
                node.value=ast.parse('bm.apply_storage_body_heal('+who+',heal,t)',mode='eval').body;self.counts['body_heal']+=1
            elif self.stack[-1]=='handle_current_hp_reduce':
                node.value=ast.parse('bm.reduce_storage_body_hp(name,cur,val,t)',mode='eval').body;self.counts['body_reduce']+=1
        if self.stack[-1]=='_activate' and any(isinstance(n,ast.Name) and n.id=='_STAT_APPLIED_EVENTS' for n in node.targets):
            stmt=ast.copy_location(ast.parse('self.effect_runtime_activate(eff,caster,t,_runtime_carrier)').body[0],node);self.counts['snapshot']+=1;return [stmt,node]
        return node
    def visit_If(self,node):
        self.generic_visit(node)
        if self.stack[-1]=='_activate':
            if ast.dump(node.test)==ast.dump(ast.parse('stat == "max_hp_from_max_hp_pct" and "hp" in self.state',mode='eval').body):
                lookup=node.body[0]
                assert isinstance(lookup,ast.Assign) and ast.dump(lookup.targets[0])==ast.dump(ast.Name(id='ab_ref',ctx=ast.Store())) and isinstance(lookup.value,ast.Call) and isinstance(lookup.value.func,ast.Name) and lookup.value.func.id=='next'
                lookup.value=ast.parse('self.effect_runtime_carrier(eff,caster,_runtime_carrier)',mode='eval').body;self.counts['carrier_lookup']+=1
                loops=[part for part in ast.walk(node) if isinstance(part,ast.For) and isinstance(part.iter,ast.Name) and part.iter.id=='targets']
                assert len(loops)==1
                loops[0].iter=ast.parse('ab_ref.target_chars or []',mode='eval').body;self.counts['hp_recipients']+=1
            for kind in ('DECOY','SHIELD'):
                expected=ast.parse('stat in _'+kind+'_STATS and targets',mode='eval').body
                if ast.dump(node.test)==ast.dump(expected):
                    self.protection_rewrites+=1
                    if kind=='SHIELD':return None
                    return ast.copy_location(ast.parse('self.effect_runtime_protection(eff,caster,t,targets,_runtime_carrier)').body[0],node)
        if self.stack[-1]=='_land_squad' and isinstance(node.test,ast.BoolOp):
            calls=[n for n in ast.walk(node.test) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='has_live_stat' and any(isinstance(a,ast.Constant) and a.value=='undying' for a in n.args)]
            if calls:
                stmt=ast.copy_location(ast.parse('to_hp=bm.absorb_heal_storage(name,to_hp,t)').body[0],node);self.counts['incoming_absorb']+=1;return [stmt,node]
        return node

def clone(fn,expected):
    return rewrite_reference(fn,Rewrite(),expected,{'protection_rewrites':2 if fn.__name__=='_activate' else 0})

def install():
    from calculator import timeline,buff_manager as module
    from runner import sim
    bm=module.BuffManager
    if getattr(bm,'_nikke_healing_storage',False):return
    assert getattr(bm.heal_received_mult,'_nikke_outgoing_healing',False)
    assert timeline.simulate is sim.simulate
    zero=dict(heal_source=0,body_heal=0,body_reduce=0,incoming_absorb=0,snapshot=0,prepare_new=0,prepare_refresh=0,carrier_lookup=0,hp_recipients=0)
    activate=clone(bm._activate,{**zero,'snapshot':1,'prepare_new':1,'prepare_refresh':2,'carrier_lookup':3,'hp_recipients':1})
    register=clone(timeline._register_instant_handlers,{**zero,'heal_source':1,'body_heal':1,'body_reduce':1})
    simulate=clone(timeline.simulate,{**zero,'heal_source':1,'body_heal':1,'incoming_absorb':1})
    original_effects=bm.char_effects
    @wraps(original_effects)
    def char_effects(self,name):return storage_before_burst_heal(original_effects(self,name))
    for name,fn in [('snapshot_heal_storage',snapshot),('heal_storage_amount',store_amount),('heal_storage_capacity',store_capacity),('fill_heal_storage',fill),('absorb_heal_storage',absorb),('apply_storage_body_heal',body_heal),('reduce_storage_body_hp',body_reduce)]:setattr(bm,name,fn)
    CATALOG.register('overheal_storage',Handler(activate=snapshot,body_clamp=body_heal,resource_kind='overheal_storage'))
    module._DIRECT_READ_STATS=module._DIRECT_READ_STATS|{STAT}
    bm._activate=activate;bm.char_effects=char_effects;timeline._register_instant_handlers=register;timeline.simulate=sim.simulate=simulate;bm._nikke_healing_storage=True
