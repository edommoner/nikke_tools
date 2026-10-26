"""Ownership is explicit, exact-generation and isolated from physical handles."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from coordinate_typed_actor_policy import FIELD_MODE,normalize,validate_effects,validate_bindings
from coordinate_typed_owner_runtime import owner_for,BODY
from destructible_world_runtime import DestructibleWorld
from impact_specs import ActorHandle,ActorKind,Impact

class TypedOwnerTests(unittest.TestCase):
    def test_exact_live_dead_and_stale_owner_identity(self):
        node=[dict(id='shield',after=['start','shield'],until=dict(time=.1),repeat=2)];binding=[dict(node='shield',kind=3,identity=10,capacity=1,owner=[0,0,1],label='typed')]
        w=DestructibleWorld(node,binding);w.advance(0);actor=w.targets.rows[0].handle
        self.assertEqual(owner_for(w,actor),BODY);self.assertEqual(actor,ActorHandle(ActorKind.HP_SHIELD,10,1))
        w.targets.rows[0].alive=False;self.assertEqual(owner_for(w,actor),BODY)
        w.advance(.1)
        if w.targets.rows[0].handle.generation==actor.generation:w.advance(.2)
        with self.assertRaisesRegex(ValueError,'Stale'):owner_for(w,actor)
    def test_unowned_and_add_owned_are_not_invented_as_body(self):
        policy=dict(mode=FIELD_MODE);normalize(policy)
        for owner in (None,[5,0,1],[0,0,2]):
            b=[dict(kind=3,owner=owner)]
            with self.assertRaises(ValueError):validate_bindings(policy,b)
        with self.assertRaises(ValueError):normalize(dict(mode=FIELD_MODE,owner_fallback='body'))
        validate_effects([dict(type='buff',target='target')],policy)
    def test_ally_lists_do_not_alias_current_enemy_fields(self):
        from coordinate_typed_actor_policy import MODE
        validate_effects([dict(type='buff',target=['self','named-ally'])],dict(mode=MODE))
        with self.assertRaisesRegex(ValueError,'ownership policy'):
            validate_effects([dict(type='buff',target=['self','target'])],dict(mode=MODE))
    def test_owner_scope_restores_global_and_instance_methods_on_error(self):
        import enemy_recipient_runtime as recipients
        from types import SimpleNamespace
        from coordinate_typed_owner_runtime import OwnerQueries
        w=DestructibleWorld([dict(id='a')],[dict(node='a',kind=3,identity=10,capacity=1,owner=[0,0,1],label='typed')]);w.advance(0)
        actor=w.targets.rows[0].handle;original=recipients.logical_enemy;method=lambda caster:True
        manager=SimpleNamespace(context_target_is_add=method);queries=OwnerQueries(dict(worlds=[w]))
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with queries.scope():
                queries.attach(manager);self.assertEqual(recipients.logical_enemy(actor),BODY)
                self.assertEqual(w.targets.rows[0].handle,actor);raise RuntimeError('injected')
        self.assertIs(recipients.logical_enemy,original);self.assertIs(manager.context_target_is_add,method)
    def test_previous_gpu_wire_rejects_owner_fields(self):
        from portable_coordinate_typed_owner_cases import fixtures,prepare
        from portable_coordinate_typed_input import compile_coordinate_typed
        c,p=prepare(fixtures()[1])
        with self.assertRaisesRegex(ValueError,'new shared GPU consumer'):
            compile_coordinate_typed(p,c['typed_bindings'],probe_kind=3,geometry=c['typed_geometry'],coordinate_weapon_targets=True,coordinate_typed_aim=True,coordinate_typed_actors=True)

if __name__=='__main__':unittest.main()
