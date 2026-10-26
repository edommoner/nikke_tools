"""Scoped typed-world extension around the actual native battle scheduler.

The normal damage handler owns scalar math, named hits and gauge. Its produced
packet lands on live typed targets; the later body landing is explicitly skipped.
This is an opt-in declared model, not public full-catalog admission.
"""
import ast
from contextlib import contextmanager,nullcontext
from functools import wraps
from unittest.mock import patch
from destructible_world_runtime import DestructibleWorld
from destructible_attack_runtime import projectiles
from destructible_skill_specs import FIELDS
from impact_specs import ActorKind
from effect_runtime import state
from enemy_recipient_specs import CURRENT_TARGETS
from reference_rewrite import rewrite_reference

class TypedLandings(ast.NodeTransformer):
    def __init__(self,*,typed_aim=False):
        self.typed_aim=typed_aim;self.counts=dict(land=0)
        if typed_aim:self.counts['aim_name']=0
    def visit_Compare(self,node):
        self.generic_visit(node)
        if self.typed_aim and ast.unparse(node)=="e['at'] not in boss.target_kinds":
            self.counts['aim_name']+=1
            guard=ast.parse("not _nikke_typed_aim_name(boss,e['at'])",mode='eval').body
            return ast.copy_location(ast.BoolOp(op=ast.And(),values=[node,guard]),node)
        return node
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='_land':
            guard=ast.parse('if _nikke_skip_typed_body_landing(ev):\n return').body[0]
            index=1 if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str) else 0
            node.body.insert(index,ast.copy_location(guard,node.body[index]));self.counts['land']+=1
        return node

@contextmanager
def typed_battle(bindings,*,max_attacks=128,modifier_model=False,shield_owner=None,hit_shields=False,weapon_shields=False,skill_shields=False,body_lifesteal=False,body_accumulation=False,typed_geometry=None,coordinate_weapon_targets=False,typed_aim_policy=None,typed_actor_policy=None):
    from calculator import timeline,buff_manager
    from runner import sim
    if type(max_attacks) is not int or not 1<=max_attacks<=128:raise ValueError('Invalid typed battle observation capacity')
    if type(modifier_model) is not bool:raise ValueError('Explicit modifier model boolean required')
    if type(coordinate_weapon_targets) is not bool or coordinate_weapon_targets and (not modifier_model or typed_geometry is None or weapon_shields or shield_owner is not None):raise ValueError('Coordinate weapon targets require their own explicit geometry/modifier policy')
    if type(hit_shields) is not bool or hit_shields and shield_owner is None:raise ValueError('Hit shields require an explicit shield owner and boolean policy')
    if type(weapon_shields) is not bool or weapon_shields and shield_owner is None:raise ValueError('Weapon shields require an explicit shield owner and boolean policy')
    if type(skill_shields) is not bool or skill_shields and shield_owner is None:raise ValueError('Skill shields require an explicit shield owner and boolean policy')
    if type(body_lifesteal) is not bool or body_lifesteal and not (weapon_shields and skill_shields and shield_owner is not None):raise ValueError('Body lifesteal requires explicit weapon/skill shield policies')
    if type(body_accumulation) is not bool or body_accumulation and not body_lifesteal:raise ValueError('Body accumulation requires explicit body lifesteal policy')
    if shield_owner is not None:
        from destructible_shield_policy import validate_owner
        validate_owner(shield_owner)
        if not modifier_model:raise ValueError('Shield interception requires the declared modifier model')
    if typed_geometry is not None:
        from portable_typed_geometry_specs import normalize
        if not bindings or any(b['kind']!=bindings[0]['kind'] for b in bindings):raise ValueError('Typed point geometry requires one explicit actor kind')
        normalize(typed_geometry,len(bindings),int(bindings[0]['kind']))
    old_simulate=timeline.simulate;old_alias=sim.simulate
    if old_simulate is not old_alias:raise ValueError('Native battle aliases differ before typed extension')
    old_boss=timeline.BossScript;old_register=buff_manager.BuffManager.register_damage_handler;old_hit=timeline.HitEvent
    old_scalar=timeline.calc_damage
    data=dict(worlds=[],managers=[],activations=[],attacks=[],finished=[]);active=[];marked={};restores=[]
    from destructible_weapon_runtime import WeaponShots
    weapons=WeaponShots(timeline,data,shield_owner,hit_shields,body_lifesteal=body_lifesteal,body_accumulation=body_accumulation) if weapon_shields else None
    from coordinate_typed_weapon_runtime import CoordinateWeaponShots
    coordinate_weapons=CoordinateWeaponShots(timeline,data,typed_geometry) if coordinate_weapon_targets else None
    if typed_aim_policy is not None and not coordinate_weapon_targets:raise ValueError('Typed aim requires the declared coordinate weapon producer')
    from coordinate_typed_aim_runtime import TypedCoordinateAim
    if typed_actor_policy is not None and typed_aim_policy is None:raise ValueError('Typed actor policy requires frame aim')
    aims=TypedCoordinateAim(data,typed_geometry,typed_aim_policy,actor_policy=typed_actor_policy) if typed_aim_policy is not None else None
    from coordinate_typed_actor_policy import owns_fields,validate_bindings
    validate_bindings(typed_actor_policy,bindings)
    from coordinate_typed_owner_runtime import OwnerQueries
    owner_queries=OwnerQueries(data,typed_actor_policy) if owns_fields(typed_actor_policy) else None
    class Boss(old_boss):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self._nikke_typed_world=DestructibleWorld.from_clock(self,bindings);data['worlds'].append(self._nikke_typed_world)
            if aims is not None:aims.validate_namespace(self)
        def begin_frame(self,t,enemy):
            if aims is not None:aims.restore(self,t,enemy)
            result=super().begin_frame(t,enemy);self._nikke_typed_world.synchronize(t)
            if aims is not None:aims.capture(self,t,enemy)
            return result
        def aim_target(self,camera,layer2):
            target=super().aim_target(camera,layer2)
            return aims.choose(self,target) if aims is not None else target
        def finish(self,t):
            result=super().finish(t);self._nikke_typed_world.synchronize(t,finished=True);data['finished'].append(float(t));return result
    def register(manager,handler):
        old_register(manager,handler);previous=manager._damage_handler
        if not data['worlds']:raise ValueError('Typed battle requires the scheduler before damage registration')
        if modifier_model:
            from destructible_damage_policy import modifier_axis
            for effect,_ in manager._effects:modifier_axis(effect)
        if weapons is not None:weapons.validate_effects(manager)
        if aims is not None:aims.validate_effects(manager)
        if owner_queries is not None:
            from coordinate_typed_actor_policy import LOGICAL_FIELD_MODE
            if typed_actor_policy=={'mode':LOGICAL_FIELD_MODE}:
                from coordinate_typed_owner_runtime import attach_logical_registry
                attach_logical_registry(manager,data['worlds'][-1])
            owner_queries.attach(manager)
        if skill_shields:
            clock=data['worlds'][-1].clock
            if clock.has_summons or any(r.p.kind in ('parts','interrupt') for r in clock._runs) or data['worlds'][-1].enemy.get('coord') is not None or data['worlds'][-1].enemy.get('has_parts'):
                raise ValueError('Declared skill shield policy requires a plain single boss')
            from destructible_skill_shield_policy import skill
            from damage_accum_runtime import STATS
            for effect,caster in manager._effects:
                if effect.get('stat')=='lifesteal_pct' and not body_lifesteal or effect.get('stat') in STATS and not body_accumulation:raise ValueError('Skill shield post-landing consumer is not declared')
                if effect.get('type')=='damage':
                    if body_accumulation and effect.get('stat')=='accum_split_damage':
                        from destructible_skill_shield_policy import accumulation_skill
                        accumulation_skill(effect)
                    else:skill(effect,manager._char[caster],allow_split=body_accumulation)
        data['managers'].append(manager)
        world=data['worlds'][-1];resolver=manager._resolve_target;missing=object();old_instance=manager.__dict__.get('_resolve_target',missing)
        condition_ok=manager._condition_ok;old_condition=manager.__dict__.get('_condition_ok',missing)
        def typed_context():
            frames=state(manager).event_stack;target=frames[-1].target if frames else None
            return target is not None and target.kind in (ActorKind.PROJECTILE,ActorKind.HP_SHIELD,ActorKind.HIT_SHIELD)
        def resolve_target(target,caster,*args,**kwargs):
            if target=='typed_point':
                if typed_geometry is None:raise ValueError('Typed point selector requires explicit shapes')
                from typed_geometry_reference import select_for_caster
                got=select_for_caster(world,typed_geometry,int(world.bindings[0].handle.kind),manager,caster)
                return [] if got is None else [world.bindings[got[0]].label]
            if target=='all_projectiles':return [world.bindings[i].label for i in world.targets.select([ActorKind.PROJECTILE])]
            if isinstance(target,str) and target in CURRENT_TARGETS and typed_context() and typed_actor_policy is None:raise ValueError('Typed enemy recipient requires an explicit actor policy')
            return resolver(target,caster,*args,**kwargs)
        def conditions(values,caster,t,eff=None):
            if typed_context() and owner_queries is None and any(isinstance(value,str) and (value in ('target_is_boss','target_is_add','target_stunned','not_target_stunned') or value.startswith(('target_state:','not_target_state:','target_stack_above:','target_stack_below:'))) for value in values):
                raise ValueError('Typed logical target condition requires an explicit actor policy')
            return condition_ok(values,caster,t,eff)
        @wraps(previous)
        def damage(effect,caster,t,*args,**kwargs):
            if '_portable_observer_row' in effect and (effect.get('target') in ('all_projectiles','typed_point') or shield_owner is not None and effect.get('target')=='boss'):
                row=effect['_portable_observer_row']
                if type(row) is not int or not 0<=row<len(manager._effects) or manager._effects[row][0] is not effect:raise ValueError('Typed observer annotation must identify its exact registered definition')
                effect={k:v for k,v in effect.items() if k!='_portable_observer_row'}
            context=None
            if body_accumulation and effect.get('stat')=='accum_split_damage':
                from destructible_skill_shield_policy import accumulation_skill
                accumulation_skill(effect)
                active.append(None)
                try:return previous(effect,caster,t,*args,**kwargs)
                finally:assert active.pop() is None
            if effect.get('target')=='typed_point':
                if typed_geometry is None:raise ValueError('Typed point damage requires explicit geometry')
                from destructible_skill_specs import coefficient
                coefficient(dict(effect,target='all_projectiles'),manager._char[caster])
                if world.last!=t or world.finished:raise ValueError('Typed point damage left its owning battle frame')
                from typed_geometry_reference import select_for_caster
                selected=select_for_caster(world,typed_geometry,int(world.bindings[0].handle.kind),manager,caster)
                if selected is None:return
                context=dict(manager=manager,world=world,effect=effect,caster=caster,time=t,kind=selected[1].kind,selected=selected)
            elif effect.get('target')=='all_projectiles':
                if set(effect)-FIELDS or effect.get('type')!='damage' or effect.get('stat')!='damage':raise ValueError('Typed battle currently requires a plain projectile skill')
                if world.last!=t or world.finished:raise ValueError('Projectile skill is outside the owning battle frame')
                data['activations'].append(dict(name=effect.get('name'),caster=caster,time=t))
                if not world.targets.select([ActorKind.PROJECTILE]):return
                context=dict(manager=manager,world=world,effect=effect,caster=caster,time=t,kind=ActorKind.PROJECTILE)
            elif shield_owner is not None and (effect.get('target')=='boss' or skill_shields):
                # Select before entering the ordinary handler. Neither damage
                # resolution nor synchronous children may retarget this packet.
                from destructible_shield_policy import select
                from destructible_skill_specs import coefficient
                if skill_shields:
                    from destructible_skill_shield_policy import skill
                    skill(effect,manager._char[caster],allow_split=body_accumulation)
                else:coefficient(dict(effect,target='all_projectiles'),manager._char[caster])
                selected=select(world,shield_owner,hit_shields=hit_shields)
                if selected is not None:
                    context=dict(manager=manager,world=world,effect=effect,caster=caster,time=t,kind=selected[1].kind,selected=selected)
            active.append(context)
            try:return previous(dict(effect,target='boss') if context is not None and not skill_shields else effect,caster,t,*args,**kwargs)
            finally:assert active.pop() is context
        manager._damage_handler=damage;manager._resolve_target=resolve_target;manager._condition_ok=conditions
        restores.append((manager,damage,previous,old_instance,old_condition,missing))
    def scalar(*args,**kwargs):
        # Passive sampled observers inspect this wrapper at the caller boundary.
        buffs=kwargs.get('buffs',args[1] if len(args)>1 else {})
        if not active and weapons is not None:return weapons.scalar(old_scalar,*args,**kwargs)
        if not active and coordinate_weapons is not None:return coordinate_weapons.scalar(old_scalar,*args,**kwargs)
        context=active[-1] if active else None
        if context is None:return old_scalar(*args,**kwargs)
        from destructible_damage_policy import calculate
        hit=kwargs.get('hit_type',args[3] if len(args)>3 else None)
        if not isinstance(hit,dict) or hit.get('coeff') is None:raise ValueError('Typed handler must expose its sampled coefficient')
        context['coefficient']=float(hit['coeff'])
        # Hit shields consume packet credit, never HP damage. Retain the normal
        # scalar in Impact for diagnostics/counters without applying HP factors.
        return calculate(*args,**kwargs,kind=ActorKind.BODY if context['kind']==ActorKind.HIT_SHIELD else context['kind'])
    def deliver_event(event,context):
        if context is None:return event
        if event.caster!=context['caster'] or event.t!=context['time']:raise ValueError('Typed packet owner/time mismatch')
        physical=context.get('coordinate_weapon',False);attacks=data['coordinate_weapon_attacks'] if physical else data['attacks']
        if len(attacks)>=(2**23-1 if physical else max_attacks):raise ValueError('Typed battle attack observation capacity exceeded')
        identity=(2**23 if physical else 0)+len(attacks)+1;marked[id(event)]=event
        record=dict(attack_id=identity,name=context['name'] if 'name' in context else context['effect'].get('name'),caster=event.caster,time=event.t,damage=float(event.damage),receipts=(),completed=False)
        if context.get('quantity_only'):record['quantity_only']=True
        if 'family' in context:record.update(family=context['family'],hit_tag=context['hit_tag'],weapon_mode_skill=context['weapon_mode_skill'])
        if modifier_model:record['coefficient']=context['coefficient']
        if physical:record.update({k:context[k] for k in ('shot_identity','extra','critical')})
        attacks.append(record)
        if context['kind']==ActorKind.PROJECTILE and 'selected' not in context:
            record['receipts']=projectiles(context['world'],context['manager'],event.caster,1,2,float(event.damage),1.,identity)
        else:
            from destructible_impact_runtime import deliver
            from impact_specs import Impact
            slot,handle=context['selected'];world=context['world']
            if world.last!=event.t or world.finished:raise ValueError('Shield packet left its owning frame')
            record['receipts']=((slot,handle,deliver(world,context['manager'],slot,Impact(event.caster,handle,context.get('family',1),2,float(event.damage),1.,identity))),)
        record['completed']=True
        return event
    def packet(*args,**kwargs):
        event=old_hit(*args,**kwargs);context=active[-1] if active else None
        if not active and weapons is not None:context=weapons.take(event)
        if not active and coordinate_weapons is not None:
            context=coordinate_weapons.take(event)
            if context is not None:return event
        return deliver_event(event,context)
    def skip(event):
        if marked.get(id(event)) is event:return True
        if coordinate_weapons is not None:
            context=coordinate_weapons.landing(event)
            if context is not None:deliver_event(event,context);return True
        if body_accumulation and event.hit_tag=='accum_split_damage':
            from destructible_shield_policy import select
            world=data['worlds'][-1];selected=select(world,shield_owner,hit_shields=hit_shields)
            if selected is not None:
                context=dict(manager=data['managers'][-1],world=world,caster=event.caster,time=event.t,kind=selected[1].kind,selected=selected,coefficient=0.,name=event.skill_name,quantity_only=True)
                deliver_event(event,context);return True
        return False
    counts=dict(land=1);globals_patch={'_nikke_skip_typed_body_landing':skip}
    if aims is not None:counts['aim_name']=1;globals_patch['_nikke_typed_aim_name']=aims.accepts_name
    rewritten=rewrite_reference(old_simulate,TypedLandings(typed_aim=aims is not None),counts,compose=True)
    from destructible_damage_policy import manager_type
    manager_scope=patch.object(timeline,'BuffManager',manager_type(timeline.BuffManager)) if modifier_model else nullcontext()
    scalar_scope=patch.object(timeline,'calc_damage',scalar) if modifier_model else nullcontext()
    try:
        with owner_queries.scope() if owner_queries is not None else nullcontext(),manager_scope,scalar_scope,weapons.scope() if weapons is not None else nullcontext(),coordinate_weapons.scope() if coordinate_weapons is not None else nullcontext(),patch.object(timeline,'BossScript',Boss),patch.object(buff_manager.BuffManager,'register_damage_handler',register),patch.object(timeline,'HitEvent',packet),patch.dict(old_simulate.__globals__,globals_patch),patch.object(timeline,'simulate',rewritten),patch.object(sim,'simulate',rewritten):yield data
    finally:
        for manager,wrapper,previous,old_instance,old_condition,missing in reversed(restores):
            if manager._damage_handler is wrapper:manager._damage_handler=previous
            if old_instance is missing:manager.__dict__.pop('_resolve_target',None)
            else:manager._resolve_target=old_instance
            if old_condition is missing:manager.__dict__.pop('_condition_ok',None)
            else:manager._condition_ok=old_condition
        if active:raise ValueError('Typed handler context leaked after battle')
