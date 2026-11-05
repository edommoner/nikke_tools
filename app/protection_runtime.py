"""Shared shield/decoy snapshot and applied-event delivery for existing effects."""
from dataclasses import dataclass
from effect_runtime import CATALOG,Handler,pool,active_carrier

@dataclass(frozen=True)
class ProtectionPolicy:
    key: str
    stats: frozenset
    current: str
    capacity: str
    amplify: bool = False
    event: str | None = None

def activate(manager,effect,caster,t,targets,policy):
    if effect.get('stat') not in policy.stats or not targets:return
    from calculator.buff_manager import _is_enemy
    carrier=active_carrier(manager,effect,caster)
    if carrier is None:return
    value=manager._get_value(effect,carrier,caster)
    amount=manager.effective_max_hp(caster)*value/100.0 if value is not None else 0.0
    values={target:amount*(1.0+manager.take_next_shield_amp(target,t)/100.0)
            for target in (carrier.target_chars or []) if not _is_enemy(target)} if policy.amplify else {
            target:amount for target in (carrier.target_chars or []) if not _is_enemy(target)}
    setattr(carrier,policy.current,values);setattr(carrier,policy.capacity,dict(values))
    pool(manager,policy.key)[carrier.uid]=carrier
    if policy.event:
        for target in values:manager.notify(policy.event,t,target)

def install():
    from calculator import buff_manager as module
    for policy in (
        ProtectionPolicy('decoy',frozenset(module._DECOY_STATS),'decoy_per_target','decoy_max_per_target'),
        ProtectionPolicy('shield',frozenset(module._SHIELD_STATS),'shield_per_target','shield_max_per_target',True,'event:shield_applied'),
    ):
        def initialize(manager,effect,caster,t,targets,selected=policy):
            return activate(manager,effect,caster,t,targets,selected)
        CATALOG.register(policy.key,Handler(protection_activate=initialize,resource_kind=policy.key))


def install_health_gate():
    """Gate newly ported during_shield HP modifiers without recursive get_buffs."""
    import ast
    from reference_rewrite import rewrite_reference
    from calculator.buff_manager import BuffManager
    if getattr(BuffManager,'_nikke_protection_health_gate',False):return
    class Gate(ast.NodeTransformer):
        def __init__(self):self.counts=dict(gate=0)
        def visit_For(self,node):
            self.generic_visit(node)
            if isinstance(node.iter,ast.Attribute) and node.iter.attr=='_active':
                assert isinstance(node.target,ast.Name) and node.target.id=='ab'
                statement=ast.parse('if ab.effect.get("stat") in {"max_hp_pct","max_hp_only_pct","hp_caster_based_pct","hp_only_caster_based_pct","max_hp_from_max_hp_pct","hp_copy"} and name in (ab.target_chars or []) and (query_scope is None or not query_scope.excludes(ab)) and ab.has_runtime_conditions and "during_shield" in ab.effect.get("trigger",{}).get("condition",[]) and not self._runtime_condition_ok(ab.effect["trigger"]["condition"],ab.caster,name,name,self._cur_t):\n continue').body[0]
                node.body.insert(0,ast.copy_location(statement,node.body[0]));self.counts['gate']+=1
            return node
    BuffManager.effective_max_hp=rewrite_reference(BuffManager.effective_max_hp,Gate(),dict(gate=1),compose=True)
    BuffManager._nikke_protection_health_gate=True
