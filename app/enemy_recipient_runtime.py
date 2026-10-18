"""Generation-aware CPU reference for sparse enemy effect recipients.

Canonical names remain unchanged. The extra immutable key belongs to the
actual carrier; refresh matching and query plans must use the same generation.
"""
import ast
from functools import wraps
from effect_runtime import CATALOG,Handler,pool,state
from enemy_recipient_specs import EnemyRecipient,EnemyRecipients,logical_enemy,CURRENT_TARGETS
from impact_specs import ActorKind
from reference_rewrite import rewrite_reference,compile_reference_helper
from world_actor_runtime import registry_for


def dynamic_registry(manager):
    cached=getattr(state(manager),'world_actor_registry',None)
    return cached[1] if cached is not None and getattr(cached[0],'has_summons',False) else None


def snapshot(manager,label):
    registry=dynamic_registry(manager)
    if registry is None:return None
    from calculator.buff_manager import _is_enemy
    if not _is_enemy(label):return None
    return registry.view(ActorKind.BODY if label=='__enemy__' else ActorKind.ADD,label)


def key_for(manager,targets,*,use_activation=True):
    if targets is None or dynamic_registry(manager) is None:return None
    stack=getattr(state(manager),'enemy_activation_stack',())
    if use_activation and stack and tuple(targets)==tuple(b.label for b in stack[-1].bindings):return stack[-1]
    result=[];seen=set()
    for label in targets:
        actor=snapshot(manager,label)
        if actor is not None and (label,actor.handle) not in seen:
            seen.add((label,actor.handle));result.append(EnemyRecipient(label,actor.handle))
    return EnemyRecipients(tuple(result)) if result else None


def refresh_matches(manager,carrier,targets):
    if carrier.effect.get('type')!='buff' or carrier.effect.get('stat')=='target_hit_counter' or dynamic_registry(manager) is None:return True
    return getattr(carrier,'enemy_recipient_key',None)==key_for(manager,targets)


def prepare(manager,effect,caster,t,carrier,initialized=False):
    if carrier is None or effect.get('type')!='buff' or effect.get('stat')=='target_hit_counter' or dynamic_registry(manager) is None:return
    # Stack initialization targets an existing carrier; it does not retarget it.
    if initialized and hasattr(carrier,'enemy_recipient_key'):return
    key=key_for(manager,carrier.target_chars)
    if key is None:return
    carrier.enemy_recipient_key=key
    pool(manager,'enemy_recipient_fields')[carrier.uid]=carrier


def visible(manager,carrier,target):
    key=getattr(carrier,'enemy_recipient_key',None)
    if key is None:return True
    actor=key.actor_for(target)
    if actor is None:return True # Existing canonical recipient routing decides.
    stack=getattr(state(manager),'enemy_query_stack',())
    query=stack[-1][1] if stack and stack[-1][0]==target else snapshot(manager,target)
    return query is not None and query.alive and query.handle==actor


def observe_generation(manager,label,actor):
    runtime=state(manager)
    if not hasattr(runtime,'enemy_query_generations'):runtime.enemy_query_generations={}
    stamp=(actor.handle,actor.alive)
    if runtime.enemy_query_generations.get(label)!=stamp:
        manager._invalidate_buffs_cache();runtime.enemy_query_generations[label]=stamp


def current_label(manager):
    runtime=state(manager);queries=getattr(runtime,'enemy_query_stack',())
    if queries:return queries[-1][0]
    frames=runtime.event_stack
    if frames and frames[-1].target is not None:
        actor=logical_enemy(frames[-1].target);registry=dynamic_registry(manager)
        if registry is not None:return registry.exact(actor).label
    caster=frames[-1].caster if frames else manager.squad_names[0]
    return manager._resolve_enemies('target',caster)[0]


def resolve_for_effect(manager,effect,target,caster):
    registry=dynamic_registry(manager);frames=state(manager).event_stack
    if effect.get('type')=='buff' and effect.get('stat')!='target_hit_counter' and registry is not None and target in CURRENT_TARGETS and frames and frames[-1].target is not None:
        return [registry.exact(logical_enemy(frames[-1].target)).label]
    return manager._resolve_target(target,caster)


def resolve_mutation(manager,effect,caster):
    target=effect.get('target','self');frames=state(manager).event_stack
    if target in CURRENT_TARGETS and frames and frames[-1].target is not None:
        registry=dynamic_registry(manager)
        if registry is not None:return [registry.exact(logical_enemy(frames[-1].target)).label]
    return manager._resolve_target(target,caster)


def mutation_targets(manager,carrier,targets):
    matched=[label for label in targets if label in (carrier.target_chars or ())]
    return [label for label in matched if visible(manager,carrier,label)] if getattr(carrier,'enemy_recipient_key',None) is not None else matched


class MutationBindings(ast.NodeTransformer):
    def __init__(self):self.counts=dict(resolve=0,scoped_remove=0,debuff_stack=0,cleanse=0,extend=0)
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and node.func.attr=='_resolve_target' and len(node.args)==2 and ast.unparse(node.args[0])=="eff.get('target', 'self')":
            self.counts['resolve']+=1
            return ast.copy_location(ast.parse('self.resolve_enemy_mutation(eff,caster)',mode='eval').body,node)
        if ast.unparse(node)=='extend_targets.intersection(set(ab.target_chars or []))':
            self.counts['extend']+=1
            return ast.copy_location(ast.parse('self.enemy_mutation_targets(ab,extend_targets)',mode='eval').body,node)
        return node
    def visit_ListComp(self,node):
        self.generic_visit(node)
        if ast.unparse(node.generators[0].iter)=='self._by_name(target_name)':
            assert len(node.generators[0].ifs)==1 and ast.unparse(node.generators[0].ifs[0])=='scope & set(ab.target_chars or [])'
            node.generators[0].ifs=[ast.parse('self.enemy_mutation_targets(ab,scope)',mode='eval').body];self.counts['scoped_remove']+=1
        if len(node.generators)==1 and isinstance(node.elt,ast.Name) and node.elt.id=='tc' and ast.unparse(node.generators[0].iter)=='target_chars' and len(node.generators[0].ifs)==1:
            self.counts['debuff_stack']+=1
            return ast.copy_location(ast.parse('self.enemy_mutation_targets(ab,target_chars)',mode='eval').body,node)
        return node
    def visit_If(self,node):
        self.generic_visit(node)
        if ast.unparse(node.test)=='tc not in (ab.target_chars or [])':
            self.counts['cleanse']+=1
            node.test=ast.BoolOp(op=ast.Or(),values=[node.test,ast.parse('not self.enemy_field_visible(ab,tc)',mode='eval').body])
        return node


class ImmuneBindings(ast.NodeTransformer):
    def __init__(self):self.counts=dict(visible=0)
    def visit_If(self,node):
        self.generic_visit(node)
        if ast.unparse(node.test)=='char_name in (ab.target_chars or [])':
            self.counts['visible']+=1
            node.test=ast.BoolOp(op=ast.And(),values=[node.test,ast.parse('self.enemy_field_visible(ab,char_name)',mode='eval').body])
        return node


def apply_receivers(manager,effect,targets,callback,*context):
    """Snapshot logical receivers after one activation gate and budget charge.

    Each receiver has an independent carrier. Child events finish before the
    next receiver; their changes must not re-resolve the original target set.
    Ally/bullet routing and target counters retain their own carrier contracts.
    """
    if effect.get('type')!='buff' or effect.get('stat')=='target_hit_counter' or not targets or dynamic_registry(manager) is None:return callback(effect,targets,*context)
    key=key_for(manager,targets,use_activation=False)
    if key is None:return callback(effect,targets,*context)
    # The immutable snapshot already resolved every known enemy; do not query
    # their providers again merely to detect a mixed target list.
    if set(targets)!={b.label for b in key.bindings}:
        raise ValueError('Mixed ally/enemy field fanout requires an explicit policy')
    runtime=state(manager)
    if not hasattr(runtime,'enemy_activation_stack'):runtime.enemy_activation_stack=[]
    for binding in key.bindings:
        runtime.enemy_activation_stack.append(EnemyRecipients((binding,)))
        try:callback(effect,[binding.label],*context)
        finally:runtime.enemy_activation_stack.pop()


class ActivationBindings(ast.NodeTransformer):
    def __init__(self):self.counts=dict(direct_refresh=0,named_refresh=0,resolve=0,fanout=0)
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name!='_activate':return node
        # Keep all trigger, condition, max-trigger and harmful-target gates in
        # the original prefix. Reuse its unchanged carrier executor per target.
        at=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='max_stack')
        tail=node.body[at:]
        helper=ast.parse('''
def _apply_enemy_carrier(self,eff,targets,caster,t,suppress_event,expires,raw_target,lazy):
    pass
''').body[0]
        helper.body=tail;self.executor=helper
        node.body=node.body[:at]+ast.parse('return self.apply_enemy_receivers(eff,targets,self._apply_enemy_carrier,caster,t,suppress_event,expires,raw_target,lazy)').body
        self.counts['fanout']+=1
        return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and node.func.attr=='_resolve_target' and len(node.args)==2 and isinstance(node.args[0],ast.Name) and node.args[0].id=='raw_target':
            self.counts['resolve']+=1
            node.func.attr='resolve_enemy_field_target';node.args.insert(0,ast.Name(id='eff',ctx=ast.Load()))
        return node
    def visit_If(self,node):
        self.generic_visit(node)
        text=ast.unparse(node.test)
        if text=='ab.effect is eff and ab.caster == caster':
            node.test=ast.BoolOp(op=ast.And(),values=[node.test,ast.parse('self.enemy_refresh_matches(ab,targets)',mode='eval').body]);self.counts['direct_refresh']+=1
        elif text.startswith('ab.caster == caster and other is not eff') and 'ab.target_chars == targets' in text:
            node.test=ast.BoolOp(op=ast.And(),values=[node.test,ast.parse('self.enemy_refresh_matches(ab,targets)',mode='eval').body]);self.counts['named_refresh']+=1
        return node


class QueryBindings(ast.NodeTransformer):
    def __init__(self):self.counts=dict(plan_filter=0)
    def visit_ListComp(self,node):
        self.generic_visit(node)
        if len(node.generators)==1 and ast.unparse(node.generators[0].iter)=='self._active':
            node.generators[0].ifs.append(ast.parse('self.enemy_field_visible(ab,target)',mode='eval').body);self.counts['plan_filter']+=1
        return node


class BindWorld(ast.NodeTransformer):
    def __init__(self):self.counts=dict(world_binding=0)
    def visit_Assign(self,node):
        self.generic_visit(node)
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='BossScript':
            assert len(node.targets)==1 and ast.unparse(node.targets[0])=='boss'
            self.counts['world_binding']+=1
            return [node,ast.copy_location(ast.parse('bm.bind_enemy_fields_world(boss)').body[0],node)]
        return node


def install():
    if 'enemy_recipients' in CATALOG.handlers:return
    from calculator import buff_manager,timeline
    from runner import sim
    manager=buff_manager.BuffManager
    manager.enemy_refresh_matches=refresh_matches;manager.enemy_field_visible=visible;manager.resolve_enemy_field_target=resolve_for_effect
    manager.resolve_enemy_mutation=resolve_mutation;manager.enemy_mutation_targets=mutation_targets
    manager._dispatch_instant=rewrite_reference(manager._dispatch_instant,MutationBindings(),dict(resolve=5,scoped_remove=1,debuff_stack=1,cleanse=1,extend=1),compose=True)
    manager._has_immune=rewrite_reference(manager._has_immune,ImmuneBindings(),dict(visible=1))
    manager.apply_enemy_receivers=apply_receivers
    original_activate=manager._activate;transform=ActivationBindings()
    manager._activate=rewrite_reference(original_activate,transform,dict(direct_refresh=1,named_refresh=1,resolve=3,fanout=1),compose=True)
    manager._apply_enemy_carrier=compile_reference_helper(original_activate,transform.executor)
    manager._build_plan=rewrite_reference(manager._build_plan,QueryBindings(),dict(plan_filter=1))
    manager.bind_enemy_fields_world=lambda self,boss:registry_for(self,boss)
    assert timeline.simulate is sim.simulate
    timeline.simulate=sim.simulate=rewrite_reference(timeline.simulate,BindWorld(),dict(world_binding=1),compose=True)
    original_buffs=manager.get_buffs
    original_has=manager._has_target_state;original_stack=manager._target_stack;original_enemy_has=manager.enemy_has_state;original_reset=manager.reset
    original_stunned=manager.is_stunned;original_compute_stunned=manager._compute_is_stunned
    @wraps(original_buffs)
    def buffs(self,caster,target,t,exclude_names=frozenset()):
        runtime=state(self)
        if not runtime.resources.get('enemy_recipient_fields'):return original_buffs(self,caster,target,t,exclude_names)
        actor=snapshot(self,target)
        if actor is None:return original_buffs(self,caster,target,t,exclude_names)
        if not hasattr(runtime,'enemy_query_stack'):runtime.enemy_query_stack=[]
        observe_generation(self,target,actor)
        runtime.enemy_query_stack.append((target,actor))
        try:return original_buffs(self,caster,target,t,exclude_names)
        finally:runtime.enemy_query_stack.pop()
    @wraps(original_enemy_has)
    def enemy_has(self,label,name):
        if dynamic_registry(self) is None:return original_enemy_has(self,label,name)
        return any(label in (ab.target_chars or ()) and visible(self,ab,label) for ab in self._by_name(name))
    @wraps(original_has)
    def has(self,name):return enemy_has(self,current_label(self),name) if dynamic_registry(self) is not None else original_has(self,name)
    @wraps(original_stack)
    def stack(self,name):
        if dynamic_registry(self) is None:return original_stack(self,name)
        label=current_label(self)
        return max((ab.stack for ab in self._by_name(name) if label in (ab.target_chars or ()) and visible(self,ab,label)),default=0)
    @wraps(original_stunned)
    def stunned(self,label):
        if state(self).resources.get('enemy_recipient_fields'):
            actor=snapshot(self,label)
            if actor is not None:observe_generation(self,label,actor)
        return original_stunned(self,label)
    @wraps(original_compute_stunned)
    def compute_stunned(self,label):
        if dynamic_registry(self) is None or snapshot(self,label) is None:return original_compute_stunned(self,label)
        active=[ab for ab in self._active if label in (ab.target_chars or ()) and visible(self,ab,label)]
        return not any(ab.effect.get('stat')=='stun_immune' for ab in active) and any(ab.effect.get('stat')=='stun' for ab in active)
    @wraps(original_reset)
    def reset(self,*args,**kwargs):
        result=original_reset(self,*args,**kwargs);pool(self,'enemy_recipient_fields').clear();runtime=state(self);runtime.enemy_query_stack=[];runtime.enemy_query_generations={};runtime.enemy_activation_stack=[];return result
    manager.get_buffs=buffs;manager._has_target_state=has;manager._target_stack=stack;manager.enemy_has_state=enemy_has;manager.reset=reset
    manager.is_stunned=stunned;manager._compute_is_stunned=compute_stunned
    CATALOG.register('enemy_recipients',Handler(prepare_activation=prepare,resource_kind='enemy_recipient_fields'))
