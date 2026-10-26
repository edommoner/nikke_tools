"""Declared BODY ownership for logical queries; physical events stay untouched."""
from contextlib import contextmanager
from unittest.mock import patch
from impact_specs import ActorHandle,ActorKind
from enemy_recipient_specs import logical_enemy

BODY=ActorHandle(ActorKind.BODY,0,1)
TYPED=frozenset((ActorKind.PROJECTILE,ActorKind.HP_SHIELD,ActorKind.HIT_SHIELD))

def owner_for(world,actor,policy=None):
    if actor.kind not in TYPED:return logical_enemy(actor)
    snapshot=world.registry.exact(actor)
    from coordinate_typed_actor_policy import FIELD_MODE,LOGICAL_FIELD_MODE
    if policy is None or policy=={'mode':FIELD_MODE}:
        if snapshot.parent!=BODY:raise ValueError('Typed field requires its declared BODY owner')
        return snapshot.parent
    if policy!={'mode':LOGICAL_FIELD_MODE}:raise ValueError('Unknown typed owner policy')
    parent=snapshot.parent
    if parent is None or parent.kind not in (ActorKind.BODY,ActorKind.ADD):raise ValueError('Typed field requires a direct logical owner')
    if parent.kind==ActorKind.BODY and parent!=BODY:raise ValueError('Invalid BODY owner generation')
    # Query the exact configured generation, including a dead same-generation
    # owner. Never resolve by label/root or silently follow a respawned ADD.
    return world.registry.exact(parent).handle

def attach_logical_registry(manager,world):
    """Use the owning battle's providers for logical and physical generations."""
    from world_actor_runtime import registry_for
    registry=registry_for(manager,world.clock)
    if world.registry is registry:return
    for (kind,label),(identity,provider) in world.registry.bindings.items():
        if kind not in TYPED:raise ValueError('Expected a typed-only registry before attachment')
        registry.bind(kind,label,provider,identity=identity)
    world.registry=registry

class OwnerQueries:
    def __init__(self,data,policy=None):self.data=data;self.policy=policy;self.predicate_restores=[];data['coordinate_typed_owner_queries']=[]
    def project(self,actor,role):
        if actor.kind not in TYPED:return logical_enemy(actor)
        if not self.data['worlds']:raise ValueError('Typed owner query requires its own world')
        world=self.data['worlds'][-1];owner=owner_for(world,actor,self.policy)
        self.data['coordinate_typed_owner_queries'].append(dict(time=world.last,physical=[int(actor.kind),actor.identity,actor.generation],logical=[int(owner.kind),owner.identity,owner.generation],role=role))
        return owner
    def attach(self,manager):
        from effect_runtime import state
        missing=object();previous=manager.__dict__.get('context_target_is_add',missing);original=manager.context_target_is_add
        def predicate(caster):
            frames=state(manager).event_stack;target=frames[-1].target if frames else None
            if target is not None and target.kind in TYPED:return self.project(target,'target-is-add').kind==ActorKind.ADD
            return original(caster)
        manager.context_target_is_add=predicate;self.predicate_restores.append((manager,previous,missing))
    @contextmanager
    def scope(self):
        import enemy_recipient_runtime
        try:
            with patch.object(enemy_recipient_runtime,'logical_enemy',lambda actor:self.project(actor,'logical-recipient')):yield
        finally:
            for manager,previous,missing in reversed(self.predicate_restores):
                if previous is missing:manager.__dict__.pop('context_target_is_add',None)
                else:manager.context_target_is_add=previous
