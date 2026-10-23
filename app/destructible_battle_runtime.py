"""Scoped typed-world extension around the actual native battle scheduler.

The normal damage handler owns scalar math, named hits and gauge. Its produced
packet lands on live typed targets; the later body landing is explicitly skipped.
This is an opt-in declared model, not public full-catalog admission.
"""
import ast
from contextlib import contextmanager
from functools import wraps
from unittest.mock import patch
from destructible_world_runtime import DestructibleWorld
from destructible_attack_runtime import projectiles
from destructible_skill_specs import FIELDS
from impact_specs import ActorKind
from reference_rewrite import rewrite_reference

class TypedLandings(ast.NodeTransformer):
    def __init__(self):self.counts=dict(land=0)
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='_land':
            guard=ast.parse('if _nikke_skip_typed_body_landing(ev):\n return').body[0]
            index=1 if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str) else 0
            node.body.insert(index,ast.copy_location(guard,node.body[index]));self.counts['land']+=1
        return node

@contextmanager
def typed_battle(bindings,*,max_attacks=128):
    from calculator import timeline,buff_manager
    from runner import sim
    if type(max_attacks) is not int or not 1<=max_attacks<=128:raise ValueError('Invalid typed battle observation capacity')
    old_simulate=timeline.simulate;old_alias=sim.simulate
    if old_simulate is not old_alias:raise ValueError('Native battle aliases differ before typed extension')
    old_boss=timeline.BossScript;old_register=buff_manager.BuffManager.register_damage_handler;old_hit=timeline.HitEvent
    data=dict(worlds=[],activations=[],attacks=[],finished=[]);active=[];marked={};restores=[]
    class Boss(old_boss):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self._nikke_typed_world=DestructibleWorld.from_clock(self,bindings);data['worlds'].append(self._nikke_typed_world)
        def begin_frame(self,t,enemy):
            result=super().begin_frame(t,enemy);self._nikke_typed_world.synchronize(t);return result
        def finish(self,t):
            result=super().finish(t);self._nikke_typed_world.synchronize(t,finished=True);data['finished'].append(float(t));return result
    def register(manager,handler):
        old_register(manager,handler);previous=manager._damage_handler
        if not data['worlds']:raise ValueError('Typed battle requires the scheduler before damage registration')
        world=data['worlds'][-1];resolver=manager._resolve_target;missing=object();old_instance=manager.__dict__.get('_resolve_target',missing)
        def resolve_target(target,caster,*args,**kwargs):
            if target=='all_projectiles':return [world.bindings[i].label for i in world.targets.select([ActorKind.PROJECTILE])]
            return resolver(target,caster,*args,**kwargs)
        @wraps(previous)
        def damage(effect,caster,t,*args,**kwargs):
            context=None
            if effect.get('target')=='all_projectiles':
                if set(effect)-FIELDS or effect.get('type')!='damage' or effect.get('stat')!='damage':raise ValueError('Typed battle currently requires a plain projectile skill')
                if world.last!=t or world.finished:raise ValueError('Projectile skill is outside the owning battle frame')
                data['activations'].append(dict(name=effect.get('name'),caster=caster,time=t))
                if not world.targets.select([ActorKind.PROJECTILE]):return
                context=dict(manager=manager,world=world,effect=effect,caster=caster,time=t)
            active.append(context)
            try:return previous(dict(effect,target='boss') if context is not None else effect,caster,t,*args,**kwargs)
            finally:assert active.pop() is context
        manager._damage_handler=damage;manager._resolve_target=resolve_target
        restores.append((manager,damage,previous,old_instance,missing))
    def packet(*args,**kwargs):
        event=old_hit(*args,**kwargs);context=active[-1] if active else None
        if context is None:return event
        if event.caster!=context['caster'] or event.t!=context['time']:raise ValueError('Typed packet owner/time mismatch')
        if len(data['attacks'])>=max_attacks:raise ValueError('Typed battle attack observation capacity exceeded')
        identity=len(data['attacks'])+1;marked[id(event)]=event
        # Reserve before synchronous landing children can produce another packet.
        # A failed delivery remains visible as incomplete, never as success.
        record=dict(attack_id=identity,name=context['effect'].get('name'),caster=event.caster,time=event.t,damage=float(event.damage),receipts=(),completed=False)
        data['attacks'].append(record)
        record['receipts']=projectiles(context['world'],context['manager'],event.caster,1,2,float(event.damage),1.,identity)
        record['completed']=True
        return event
    def skip(event):return marked.get(id(event)) is event
    rewritten=rewrite_reference(old_simulate,TypedLandings(),dict(land=1),compose=True)
    try:
        with patch.object(timeline,'BossScript',Boss),patch.object(buff_manager.BuffManager,'register_damage_handler',register),patch.object(timeline,'HitEvent',packet),patch.dict(old_simulate.__globals__,{'_nikke_skip_typed_body_landing':skip}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):yield data
    finally:
        for manager,wrapper,previous,old_instance,missing in reversed(restores):
            if manager._damage_handler is wrapper:manager._damage_handler=previous
            if old_instance is missing:manager.__dict__.pop('_resolve_target',None)
            else:manager._resolve_target=old_instance
        if active:raise ValueError('Typed handler context leaked after battle')
