"""Declared HP-recovery-share model, isolated from production.

Each distinct live carrier contributes one link per distinct live recipient.
Overlapping carriers form a connected component; healing is divided in link
proportions, including full-HP members. This models Rem's 2/8 versus 1/8 shares.
The original heal's received/outgoing multipliers are evaluated once before
division. Distributed portions update HP/storage and synchronous HP edges but
do not recursively share or emit additional heal_received notifications. The
original recipient still receives its one original notification.

General multi-caster connectivity, potency placement, conditional links and
delivery order are explicit model choices pending in-game verification.
Repair, revival, max-HP grants and negative amounts are not shared.
"""
import ast
from reference_rewrite import rewrite_reference
from healing_storage_compat import Rewrite as StorageRewrite
from effect_runtime import CATALOG,Handler,shared_body_heal

STAT='heal_split'

def plan(self,name,t):
    if self.is_down(name):return [(name,1)]
    carriers=[]
    for ab in self._by_stat(STAT):
        # Evaluate live/lazy membership in resident then squad order, before
        # changing any HP. Repeated authored target names create no extra links.
        members={n for n in self.squad_names if not self.is_down(n) and self._live(ab,n,t)}
        if members:carriers.append(members)
    connected={name}
    while True:
        expanded=connected.union(*(members for members in carriers if members & connected))
        if expanded==connected:break
        connected=expanded
    weights=[(n,sum(n in members for members in carriers if members & connected)) for n in self.squad_names if n in connected]
    return [(n,w) for n,w in weights if w] or [(name,1)]

def body_heal(self,name,amount,t):
    return shared_body_heal(self,name,amount,t)

class Rewrite(StorageRewrite):
    def __init__(self):
        super().__init__();self.shared_heals=0;self.removed_syncs=0
    def visit_Assign(self,node):
        result=super().visit_Assign(node)
        if isinstance(result,ast.Assign) and isinstance(result.value,ast.Call) and isinstance(result.value.func,ast.Attribute) and result.value.func.attr=='apply_storage_body_heal':
            result.value.func.attr='apply_shared_body_heal';self.shared_heals+=1
            return ast.copy_location(ast.Expr(value=result.value),result)
        return result
    def visit_Expr(self,node):
        if self.stack[-1] in ('handle_heal_hp_pct','_apply_lifesteal') and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='sync_hp':
            self.removed_syncs+=1;return None
        return self.generic_visit(node)

def clone(fn,expected):
    return rewrite_reference(fn,Rewrite(),expected,{'shared_heals':1,'removed_syncs':1})

def install():
    from calculator import timeline,buff_manager as module
    from runner import sim
    bm=module.BuffManager
    if getattr(bm,'_nikke_heal_sharing',False):return
    assert getattr(bm,'_nikke_healing_storage',False)
    assert timeline.simulate is sim.simulate
    zero=dict(heal_source=0,body_heal=0,body_reduce=0,incoming_absorb=0,snapshot=0,prepare_new=0,prepare_refresh=0,carrier_lookup=0,hp_recipients=0)
    register=clone(timeline._register_instant_handlers,{**zero,'heal_source':1,'body_heal':1,'body_reduce':1})
    simulate=clone(timeline.simulate,{**zero,'heal_source':1,'body_heal':1,'incoming_absorb':1})
    bm.heal_share_plan=plan
    CATALOG.register('healing_share',Handler(heal_plan=plan))
    module._DIRECT_READ_STATS=module._DIRECT_READ_STATS|{STAT}
    timeline._register_instant_handlers=register;timeline.simulate=sim.simulate=simulate;bm._nikke_heal_sharing=True
