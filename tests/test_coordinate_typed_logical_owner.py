"""Exact logical ownership is independent of physical target and aim lifetime."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from coordinate_typed_actor_policy import LOGICAL_FIELD_MODE,FIELD_MODE,normalize,validate_bindings
from coordinate_typed_owner_runtime import owner_for,OwnerQueries
from destructible_world_runtime import DestructibleWorld
from impact_specs import ActorHandle,ActorKind
from world_actor_runtime import ActorRegistry

POLICY={'mode':LOGICAL_FIELD_MODE}

class LogicalOwnerTests(unittest.TestCase):
    def world(self,owner=(5,1,1)):
        state=dict(generation=1,alive=True);registry=ActorRegistry()
        registry.bind(ActorKind.BODY,'__enemy__',lambda:(1,True,None),identity=0)
        registry.bind(ActorKind.ADD,'__enemy__:add',lambda:(state['generation'],state['alive'],None),identity=1)
        w=DestructibleWorld([dict(id='typed')],[dict(node='typed',kind=3,identity=10,capacity=1,owner=list(owner),label='shield')],registry)
        w.advance(0);return w,w.targets.rows[0].handle,state
    def test_exact_add_and_dead_same_generation_preserve_physical_identity(self):
        w,physical,state=self.world();expected=ActorHandle(5,1,1)
        self.assertEqual(owner_for(w,physical,POLICY),expected)
        state['alive']=False;w.targets.rows[0].alive=False
        self.assertEqual(owner_for(w,physical,POLICY),expected)
        self.assertEqual(w.targets.rows[0].handle,physical)
        with self.assertRaisesRegex(ValueError,'BODY owner'):owner_for(w,physical)
    def test_respawned_add_does_not_retarget_old_owner(self):
        w,physical,state=self.world();state['generation']=2
        with self.assertRaisesRegex(ValueError,'Stale'):owner_for(w,physical,POLICY)
        self.assertEqual(w.targets.rows[0].owner,ActorHandle(5,1,1))
    def test_unknown_and_unspawned_add_rejected_without_body_fallback(self):
        w,physical,state=self.world((5,7,1))
        with self.assertRaisesRegex(ValueError,'Unknown'):owner_for(w,physical,POLICY)
        w,physical,state=self.world();state['generation']=0
        with self.assertRaisesRegex(ValueError,'not spawned'):owner_for(w,physical,POLICY)
    def test_policy_is_explicit_and_validates_full_handle(self):
        normalize(POLICY)
        for owner in ([5,1,1],[0,0,1]):validate_bindings(POLICY,[dict(kind=3,owner=owner)])
        for owner in (None,[1,0,1],[2,10,1],[0,1,1],[0,0,2],[5,True,1],[5,1,0]):
            with self.assertRaises(ValueError):validate_bindings(POLICY,[dict(kind=3,owner=owner)])
        with self.assertRaises(ValueError):validate_bindings({'mode':FIELD_MODE},[dict(kind=3,owner=[5,1,1])])
    def test_recipient_and_predicate_use_same_owner_and_restore(self):
        import enemy_recipient_runtime as recipients
        w,physical,state=self.world();query=OwnerQueries(dict(worlds=[w]),POLICY)
        manager=SimpleNamespace(context_target_is_add=lambda caster:False)
        from effect_runtime import state as runtime
        runtime(manager).event_stack.append(SimpleNamespace(target=physical))
        original=recipients.logical_enemy;previous=manager.context_target_is_add
        with self.assertRaisesRegex(RuntimeError,'stop'):
            with query.scope():
                query.attach(manager);self.assertTrue(manager.context_target_is_add('caster'))
                self.assertEqual(recipients.logical_enemy(physical),ActorHandle(5,1,1));raise RuntimeError('stop')
        self.assertIs(recipients.logical_enemy,original);self.assertIs(manager.context_target_is_add,previous)
        self.assertEqual({r['role'] for r in query.data['coordinate_typed_owner_queries']},{'target-is-add','logical-recipient'})
    def test_shared_battle_registry_retains_live_providers_and_exact_generation(self):
        from coordinate_typed_owner_runtime import attach_logical_registry
        from world_actor_runtime import registry_for
        state=dict(generation=1,alive=True);manager=SimpleNamespace()
        w=DestructibleWorld([dict(id='typed')],[dict(node='typed',kind=3,identity=10,capacity=1,owner=[5,1,1],label='shield')])
        w.advance(0);physical=w.targets.rows[0].handle
        registry=registry_for(manager,w.clock)
        registry.bind(ActorKind.ADD,'__enemy__:add',lambda:(state['generation'],state['alive'],None),identity=1)
        attach_logical_registry(manager,w);self.assertIs(w.registry,registry)
        self.assertEqual(owner_for(w,physical,POLICY),ActorHandle(5,1,1))
        attach_logical_registry(manager,w) # Idempotent, never duplicate providers.
        state['generation']=2
        with self.assertRaisesRegex(ValueError,'Stale'):owner_for(w,physical,POLICY)
        self.assertEqual(w.registry.exact(physical).handle,physical)
    def test_old_gpu_consumer_cannot_accept_logical_policy(self):
        from portable_coordinate_typed_input import compile_coordinate_typed
        with self.assertRaisesRegex(ValueError,'new shared GPU consumer'):
            compile_coordinate_typed(dict(typed_actor_policy=POLICY),coordinate_typed_owners=True)

if __name__=='__main__':unittest.main()
