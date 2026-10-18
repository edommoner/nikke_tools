"""Bind body/part/add landings to typed actor identities without duplicating math.

Add receipts use the actual reference pool quantity after HP/hit-HP clipping.
This CPU bridge does not enable GPU summon-world admission. Unsupported actor
kinds require an explicit adapter instead of aliasing them to the body.
"""
import ast
from functools import wraps
from effect_runtime import observes_impacts,publish_impact
from impact_specs import ActorHandle,ActorKind,HitOutcome,Impact,classify_hit
from reference_rewrite import rewrite_reference
from world_actor_runtime import registry_for


def landing(manager,event,t,boss):
    if not observes_impacts(manager):return
    name=event.target or event.part
    if name:
        actor=registry_for(manager,boss).view(ActorKind.PART,name)
    else:actor=registry_for(manager,boss).view(ActorKind.BODY,'__enemy__')
    publish_impact(manager,Impact(event.caster,actor.handle,classify_hit(event.hit_tag),HitOutcome.DAMAGING,event.damage),t)
    if not actor.alive:
        from target_counter_runtime import target_death
        target_death(manager,actor.handle,t)

def land_add(manager,boss,event,name,t):
    if not observes_impacts(manager):return boss.hit_add(event,name,t)
    registry=registry_for(manager,boss);previous=getattr(boss,'_typed_add_callback',None)
    def receipt(ev,label,generation,amount,killed,at):
        target=ActorHandle(ActorKind.ADD,registry.identity(ActorKind.ADD,label),generation)
        publish_impact(manager,Impact(ev.caster,target,classify_hit(ev.hit_tag),HitOutcome.DAMAGING,amount),at)
        if killed:
            from target_counter_runtime import target_death
            target_death(manager,target,at)
    boss._typed_add_callback=receipt
    try:return boss.hit_add(event,name,t)
    finally:boss._typed_add_callback=previous

def add_receipt(boss,event,label,generation,amount,killed,t):
    callback=getattr(boss,'_typed_add_callback',None)
    if callback is not None:callback(event,label,generation,amount,killed,t)

class AddReceipt(ast.NodeTransformer):
    def __init__(self):self.counts=dict(receipt=0)
    def visit_Return(self,node):
        if isinstance(node.value,ast.Constant) and node.value.value is True:
            self.counts['receipt']+=1
            statement=ast.parse('self.publish_add_receipt(ev,add.id,run.opens,took,killed,t)').body[0]
            return [ast.copy_location(statement,node),node]
        return node


class Landings(ast.NodeTransformer):
    def __init__(self):self.stack=[];self.counts=dict(body=0,part=0,target=0,add=0)
    def visit_FunctionDef(self,node):
        self.stack.append(node.name);self.generic_visit(node);self.stack.pop();return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if self.stack[-1]=='_land' and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='boss' and node.func.attr=='hit_add':
            self.counts['add']+=1
            return ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id='bm',ctx=ast.Load()),attr='land_add_with_impact',ctx=ast.Load()),args=[ast.Name(id='boss',ctx=ast.Load())]+node.args,keywords=node.keywords),node)
        return node
    def visit_Expr(self,node):
        self.generic_visit(node)
        call=node.value
        if self.stack[-1] not in ('_land_boss','_land_target') or not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!='_apply_lifesteal':return node
        if not isinstance(call.args[0],ast.Name):return node # Interception damage is outside the supported actor world.
        name=call.args[0].id
        key='target' if self.stack[-1]=='_land_target' else 'part' if name=='pev' else 'body'
        self.counts[key]+=1
        statement=ast.parse(f'bm.publish_landing({name},t,boss)').body[0]
        return [ast.copy_location(statement,node),node]


def install():
    from calculator import timeline,buff_manager,boss_pattern
    from runner import sim
    manager=buff_manager.BuffManager
    if getattr(manager,'_nikke_typed_impacts',False):return
    assert timeline.simulate is sim.simulate and getattr(manager,'_nikke_damage_queries',False)
    simulate=rewrite_reference(timeline.simulate,Landings(),dict(body=1,part=1,target=1,add=1),compose=True)
    manager.publish_landing=landing
    boss_pattern.BossScript.hit_add=rewrite_reference(boss_pattern.BossScript.hit_add,AddReceipt(),dict(receipt=1))
    boss_pattern.BossScript.publish_add_receipt=add_receipt
    manager.land_add_with_impact=land_add
    original_reset=manager.reset
    @wraps(original_reset)
    def reset(self,*args,**kwargs):
        result=original_reset(self,*args,**kwargs)
        from effect_runtime import state
        state(self).world_actor_registry=None
        state(self).control_aims={}
        return result
    manager.reset=reset
    timeline.simulate=sim.simulate=simulate;manager._nikke_typed_impacts=True
