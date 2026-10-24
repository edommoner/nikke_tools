"""Opt-in normal-shot producer using native or declared whole-scene routing.

Uses actual native fire returns, routing, landings and owned group dispatch.
It supplies no damage formula or CPU replay. BODY/ADD are enemies; parts are
not separately counted. Default native execution never installs this scope.
"""
import ast
from contextlib import contextmanager
from dataclasses import dataclass,replace
from functools import wraps
from unittest.mock import patch
from attack_group_runtime import plan,cancel
from effect_runtime import state,pool
from impact_specs import ActorKind,HitFamily,inherits_target
from enemy_recipient_specs import CURRENT_TARGETS
from reference_rewrite import rewrite_reference
from world_actor_runtime import registry_for

@dataclass(eq=False)
class Shot:
    manager:object
    owner:str
    identity:int
    time:float
    packets:dict
    frame:object=None

class LandScope(ast.NodeTransformer):
    def __init__(self):self.counts=dict(land=0)
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='_land':
            item=ast.parse('with _nikke_shot_land_scope(bm,boss,ev,t):\n pass').body[0]
            item.body=node.body;node.body=[ast.copy_location(item,node.body[0])];self.counts['land']+=1
        return node

class Producer:
    def __init__(self,*,coordinate_packets=False):
        self.coordinate_packets=coordinate_packets
        self.next_id=0;self.pending={};self.shots={};self.active=[];self.deliveries=[];self.contexts=[];self.damage_contexts=[];self.child_targets={};self.visibility=[];self.restores=[]
        self.data=dict(shots=[],groups=[],notifications=[],children=[],child_landings=[],managers=[])
        if coordinate_packets:self.data['physical_receipts']=[]
    def wrap_fire(self,original):
        @wraps(original)
        def fire(actor,t,manager,*args,**kwargs):
            answer=original(actor,t,manager,*args,**kwargs)
            if not answer or not plan(manager,actor.name) or actor._wc_is_skill_damage():return answer
            from calculator.sim_result import _is_normal
            if self.coordinate_packets:
                # _coord_pellet already authored the real BODY/PART/INTERRUPT
                # packets. Retain their identities and let canonical landing
                # publish typed receipts; never synthesize enemy targets here.
                if any(not _is_normal(ev) or ev.to is not None or ev.rule or ev.split or ev.part_damage or ev.interrupt_damage for ev in answer):
                    raise ValueError('Coordinate shot groups require expanded normal packets')
            elif any(not _is_normal(ev) or ev.to is not None or ev.rule or ev.target or ev.extra or ev.split or ev.part_damage or ev.interrupt_damage for ev in answer):
                raise ValueError('Shot groups require plain logical normal packets')
            packet_limit=131072 if self.coordinate_packets else 1024
            if len(self.shots)>=32 or len(answer)>packet_limit or len({id(ev) for ev in answer})!=len(answer):raise ValueError('Pending shot group capacity or packet identity')
            self.next_id+=1
            if self.next_id>=2**24:raise ValueError('Shot identity capacity exceeded')
            shot=Shot(manager,actor.name,self.next_id,t,{id(ev):ev for ev in answer})
            self.shots[shot.identity]=shot
            for key,ev in shot.packets.items():
                if key in self.pending:raise ValueError('Packet already belongs to a shot')
                self.pending[key]=(shot,ev)
            self.data['shots'].append(dict(owner=actor.name,identity=shot.identity,time=t,packets=len(answer)))
            return answer
        return fire
    def abort(self,shot):
        if shot.frame is not None:cancel(shot.manager,shot.frame)
        for key in shot.packets:self.pending.pop(key,None)
        self.shots.pop(shot.identity,None)
    @contextmanager
    def packet_scope(self,manager,boss,event,t):
        item=self.pending.pop(id(event),None);shot=item[0] if item is not None else None
        if item is None and any(frame[1] is not None and frame[2] is event for frame in self.active):raise ValueError('Shot packet reentered its landing')
        if item is not None and (item[1] is not event or shot.manager is not manager or event.caster!=shot.owner or t<shot.time):raise ValueError('Shot landing owner/time mismatch')
        if shot is not None and shot.frame is None:
            shot.frame=manager.begin_attack_targets(shot.owner,shot.identity,t,kinds=(ActorKind.BODY,ActorKind.ADD))
        self.active.append((manager,shot,event))
        try:
            try:yield
            finally:self.active.pop();self.child_targets.pop(id(event),None)
        except BaseException:
            if shot is not None:self.abort(shot)
            raise
        else:
            if shot is not None:
                del shot.packets[id(event)]
                if not shot.packets:
                    self.shots.pop(shot.identity)
                    targets=tuple(shot.frame.targets)
                    row=dict(owner=shot.owner,identity=shot.identity,epoch=shot.frame.key.epoch,time=t,targets=targets,finished=False)
                    self.data['groups'].append(row)
                    try:result=manager.finish_attack_targets(shot.frame,t)
                    except BaseException:cancel(manager,shot.frame);raise
                    if result.targets!=targets:raise ValueError('Sealed group changed during children')
                    row['finished']=True
    @contextmanager
    def delivery(self,manager,event):
        current=self.active[-1] if self.active else None
        identity=current[1].identity if current and current[0] is manager and current[1] is not None and current[2] is event else 0
        frame=[manager,event.caster,identity,False];self.deliveries.append(frame)
        try:yield
        finally:assert self.deliveries.pop() is frame
    def labels(self,manager,handles,*,live=True):
        registry=state(manager).world_actor_registry[1];out=[]
        for handle in handles:
            try:actor=registry.exact(handle)
            except ValueError:continue
            if not live or actor.alive:out.append(actor.label)
        return out

@contextmanager
def battle_attack_groups(*,routing,coordinate_packets=False):
    if routing not in ('native','all-logical-enemies'):raise ValueError('Explicit native or all-logical-enemies shot routing required')
    from calculator import timeline,buff_manager
    from runner import sim
    import impact_runtime
    if timeline.simulate is not sim.simulate:raise ValueError('Native simulation aliases differ')
    if getattr(timeline.BossScript,'_nikke_attack_group_scope',False):raise ValueError('Nested shot producer scopes are unsupported')
    if type(coordinate_packets) is not bool:raise ValueError('Explicit boolean coordinate packet policy required')
    if coordinate_packets and routing!='native':raise ValueError('Coordinate packets require native routing')
    runtime=Producer(coordinate_packets=coordinate_packets);old_sim=timeline.simulate;old_boss=timeline.BossScript;old_hit=timeline.HitEvent
    manager_type=buff_manager.BuffManager;old_register=manager_type.register_damage_handler;old_notify=manager_type.notify;old_resolve=manager_type._resolve_target
    old_landing=manager_type.publish_landing;old_add=manager_type.land_add_with_impact;old_publish=impact_runtime.publish_impact
    class Boss(old_boss):
        _nikke_attack_group_scope=True
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            if not coordinate_packets and (self.geom is not None or self.target_kinds or self._base_parts or any(run.p.kind not in ('idle','summon') or run.p.summon is not None and (run.p.summon.attack is not None or run.p.summon.self_destruct) for run in self._runs)):raise ValueError('Shot group model requires plain body/add world')
        def _alive_adds(self):
            actors=super()._alive_adds()
            if not runtime.visibility or runtime.visibility[-1][0] is not self:return actors
            manager,bindings=runtime.visibility[-1][1:];registry=registry_for(manager,self);out=[]
            for actor in actors:
                expected=bindings.get(actor.id)
                if expected is not None and registry.view(ActorKind.ADD,actor.id).handle!=expected:continue
                out.append(actor)
            return out
        def route(self,event,has_state=None):
            child=runtime.child_targets.get(id(event));current=runtime.active[-1] if runtime.active else None
            if child is not None and child[0] is event:
                manager,handles,key=child[1:];registry=registry_for(manager,self)
                bindings={registry.identities[h.kind,h.identity]:h for h in handles if h.kind==ActorKind.ADD}
                runtime.visibility.append((self,manager,bindings))
                try:return super().route(event,has_state)
                finally:runtime.visibility.pop()
            if routing=='all-logical-enemies' and current and current[1] is not None and current[2] is event:
                return super().route(replace(event,rule='all_enemies'),has_state)
            return super().route(event,has_state)
        def publish_add_receipt(self,event,label,generation,amount,killed,t):
            child=runtime.child_targets.get(id(event))
            if child is not None and child[0] is event:
                from impact_specs import ActorHandle
                registry=registry_for(child[1],self)
                runtime.data['child_landings'].append(dict(owner=event.caster,time=t,name=event.skill_name,group_identity=child[3].identity,target=ActorHandle(ActorKind.ADD,registry.identity(ActorKind.ADD,label),generation),damage=amount))
            return super().publish_add_receipt(event,label,generation,amount,killed,t)
    def publish(manager,packet,t):
        frame=runtime.deliveries[-1] if runtime.deliveries else None
        if frame is not None and frame[0] is manager and not frame[3]:
            frame[3]=True
            if frame[2]:
                if packet.attacker!=frame[1] or packet.family!=HitFamily.WEAPON:raise ValueError('Nonphysical shot receipt')
                packet=replace(packet,attack_id=frame[2])
                if coordinate_packets:
                    runtime.data['physical_receipts'].append(dict(owner=frame[1],identity=frame[2],time=t,target=packet.target,credit=packet.credit,outcome=int(packet.outcome)))
        return old_publish(manager,packet,t)
    def landing(manager,event,t,boss):
        child=runtime.child_targets.get(id(event))
        if child is not None and child[0] is event:
            actor=registry_for(manager,boss).view(ActorKind.BODY,'__enemy__')
            runtime.data['child_landings'].append(dict(owner=event.caster,time=t,name=event.skill_name,group_identity=child[3].identity,target=actor.handle,damage=event.damage))
        with runtime.delivery(manager,event):return old_landing(manager,event,t,boss)
    def add(manager,boss,event,label,t):
        with runtime.delivery(manager,event):return old_add(manager,boss,event,label,t)
    def notify(manager,event,t,caster,*args,**kwargs):
        targets=kwargs.get('attack_targets')
        if targets is not None:
            owned=pool(manager,'dispatching_attack_groups').get(targets.key)
            if owned is None or owned.result is not targets:raise ValueError('Matched targets require an owned sealed group')
            context=(manager,targets.targets,targets.key)
            runtime.data['notifications'].append(dict(event=event,owner=caster,time=t,key=targets.key,targets=targets.targets))
        else:context=runtime.contexts[-1] if runtime.contexts and inherits_target(event) else None
        runtime.contexts.append(context)
        try:return old_notify(manager,event,t,caster,*args,**kwargs)
        finally:assert runtime.contexts.pop() is context
    def resolve(manager,target,caster):
        context=runtime.contexts[-1] if runtime.contexts else None
        if context and context[0] is manager and isinstance(target,str) and target in CURRENT_TARGETS:return runtime.labels(manager,context[1])
        return old_resolve(manager,target,caster)
    def register(manager,handler):
        old_register(manager,handler);previous=manager._damage_handler
        for effect,_ in manager._effects:
            if any(t.startswith('multi_hit:') for t in effect.get('trigger',{}).get('timing',[])):
                if effect.get('target') not in ('self','target') or effect.get('trigger',{}).get('condition') or effect.get('type') not in ('buff','damage') or effect.get('type')=='damage' and effect.get('stat')!='bonus_damage':raise ValueError('Unsupported multi_hit child contract')
        runtime.data['managers'].append(manager)
        def damage(effect,caster,t,*args,**kwargs):
            context=runtime.contexts[-1] if runtime.contexts else None
            selected=context if context and context[0] is manager and isinstance(effect.get('target'),str) and effect['target'] in CURRENT_TARGETS else None
            item=(selected,caster,effect.get('name'));runtime.damage_contexts.append(item)
            try:return previous(effect,caster,t,*args,**kwargs)
            finally:assert runtime.damage_contexts.pop() is item
        manager._damage_handler=damage
        runtime.restores.append((manager,damage,previous))
    def hit(*args,**kwargs):
        event=old_hit(*args,**kwargs);item=runtime.damage_contexts[-1] if runtime.damage_contexts else None
        if item and item[0] and event.caster==item[1] and event.skill_name==item[2]:
            manager,handles,key=item[0];event=replace(event,to=tuple(runtime.labels(manager,handles,live=False)))
            runtime.child_targets[id(event)]=(event,manager,handles,key)
            runtime.data['children'].append(dict(owner=event.caster,time=event.t,name=event.skill_name,damage=event.damage,group_identity=key.identity,targets=handles,to=event.to))
        return event
    rewritten=rewrite_reference(old_sim,LandScope(),dict(land=1),compose=True)
    try:
        with patch.object(timeline.CharState,'_fire',runtime.wrap_fire(timeline.CharState._fire)),patch.object(timeline.CharState,'_charge_fire',runtime.wrap_fire(timeline.CharState._charge_fire)),patch.object(timeline,'BossScript',Boss),patch.object(timeline,'HitEvent',hit),patch.object(manager_type,'register_damage_handler',register),patch.object(manager_type,'notify',notify),patch.object(manager_type,'_resolve_target',resolve),patch.object(manager_type,'publish_landing',landing),patch.object(manager_type,'land_add_with_impact',add),patch.object(impact_runtime,'publish_impact',publish),patch.dict(old_sim.__globals__,{'_nikke_shot_land_scope':runtime.packet_scope}),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):
            yield runtime.data
            if runtime.pending or runtime.shots or runtime.child_targets or runtime.active or runtime.deliveries or runtime.contexts or runtime.damage_contexts or runtime.visibility:raise ValueError('Shot producer state leaked')
    finally:
        for shot in list(runtime.shots.values()):runtime.abort(shot)
        runtime.child_targets.clear()
        for manager,wrapped,previous in reversed(runtime.restores):
            if manager._damage_handler is wrapped:manager._damage_handler=previous
