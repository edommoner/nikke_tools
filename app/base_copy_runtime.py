"""Base ATK/HP copy policy shared by compiler and registered CPU lifecycle.

Independent guide observations select by base values, unlike a local parsed
note suggesting final-ATK ranking. This is an explicit model correction;
the pinned calculator previously omitted these stats entirely.
"""
import ast
from dataclasses import dataclass
from functools import wraps
from effect_runtime import CATALOG,Handler,pool,state
from reference_rewrite import rewrite_reference

@dataclass(frozen=True)
class CopyPolicy:
    code:int
    axis:str
    selector:str

POLICIES={
    'atk_copy':CopyPolicy(85,'atk','allies_top_atk:1'),
    'hp_copy':CopyPolicy(86,'hp','allies_top_hp:1'),
}

def prepare(manager,effect,caster,t,carrier,initialized=False):
    policy=POLICIES.get(effect.get('stat'))
    if effect.get('type')!='buff' or policy is None:return
    if effect.get('copy_from')!=policy.selector:raise ValueError('Unsupported base-stat copy selector')
    if carrier is None or carrier.effect is not effect or carrier.caster!=caster or not any(ab is carrier for ab in manager._active):raise RuntimeError('Copy preparation requires the exact live carrier')
    stats=manager.state.get('base_stats',{})
    candidates=[name for name in manager.squad_names if not manager.is_down(name)]
    source=max(candidates,key=lambda name:stats.get(name,{}).get(policy.axis,0)) if candidates else None
    carrier.copy_source=source;carrier.copy_basis=stats.get(source,{}).get(policy.axis,0)
    carrier.copy_pending_sync=bool(initialized and policy.axis=='hp')
    pool(manager,'base_stat_copy')[carrier.uid]=carrier
    manager._invalidate_buffs_cache()

def hp_bonus(manager,carrier,recipient):
    value=manager._get_value(carrier.effect,carrier,recipient)
    return carrier.copy_basis*value/100 if value is not None else 0

def activate(manager,effect,caster,t):
    if effect.get('stat')!='hp_copy':return
    carrier=state(manager).activation_stack[-1]
    if carrier is None or carrier.effect is not effect or carrier.caster!=caster:raise RuntimeError('Copy activation requires the exact carrier')
    if not any(ab is carrier for ab in manager._active):return
    carrier.copy_pending_sync=False
    amount=hp_bonus(manager,carrier,caster);previous=getattr(carrier,'copy_last_gift',0)
    carrier.copy_last_gift=amount;delta=amount-previous
    for recipient in carrier.target_chars or []:
        if recipient in manager.state.get('hp',{}):
            if delta>0:manager.state['hp'][recipient]=min(manager.state['hp'][recipient]+delta,manager.effective_max_hp(recipient))
            manager.sync_hp(recipient)

def after_dispatch(manager,before):
    # Stack initialization changes max HP without an activation HP grant.
    # Synchronize its derived ratio before the caller resumes; use the same
    # nested-event delivery as other HP writes, without emitting healing.
    for carrier in list(pool(manager,'base_stat_copy').values()):
        if not getattr(carrier,'copy_pending_sync',False) or not any(ab is carrier for ab in manager._active):continue
        carrier.copy_pending_sync=False
        for recipient in carrier.target_chars or []:
            if recipient in manager.state.get('hp',{}):manager.sync_hp(recipient)

class Rewrite(ast.NodeTransformer):
    def __init__(self):self.counts={'hp_contribution':0,'hp_expiry':0}
    def visit_If(self,node):
        self.generic_visit(node)
        if ast.dump(node.test)==ast.dump(ast.parse('stat == "max_hp_from_max_hp_pct"',mode='eval').body):
            assert not node.orelse
            node.orelse=ast.parse('if stat == "hp_copy":\n bonus_flat += self.copy_hp_bonus(ab,name)').body
            self.counts['hp_contribution']+=1
        return node
    def visit_Tuple(self,node):
        self.generic_visit(node)
        if all(isinstance(item,ast.Constant) for item in node.elts) and tuple(item.value for item in node.elts)==('hp_caster_based_pct','hp_only_caster_based_pct','max_hp_from_max_hp_pct'):
            node.elts.append(ast.Constant('hp_copy'));self.counts['hp_expiry']+=1
        return node

def install():
    if 'base_stat_copy' in CATALOG.handlers:return
    from calculator import buff_manager as module
    manager=module.BuffManager;original_value=manager._get_value
    @wraps(original_value)
    def get_value(self,effect,carrier,*args,**kwargs):
        value=original_value(self,effect,carrier,*args,**kwargs)
        if effect.get('stat')=='atk_copy' and value is not None:return carrier.copy_basis*value/100
        return value
    manager._get_value=get_value;manager.copy_hp_bonus=hp_bonus
    module._STAT_TO_BUFF['atk_copy']='atk_flat'
    module._DIRECT_READ_STATS=module._DIRECT_READ_STATS|{'hp_copy'}
    manager.effective_max_hp=rewrite_reference(manager.effective_max_hp,Rewrite(),{'hp_contribution':1,'hp_expiry':0})
    manager.tick=rewrite_reference(manager.tick,Rewrite(),{'hp_contribution':0,'hp_expiry':1})
    CATALOG.register('base_stat_copy',Handler(prepare_activation=prepare,activate=activate,after_dispatch=after_dispatch,resource_kind='base_stat_copy'))
