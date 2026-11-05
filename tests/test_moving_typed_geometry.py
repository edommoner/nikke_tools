"""Physical attachment visibility uses existing generation/liveness and phase."""
import copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace as S
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from coordinate_moving_typed_geometry import MovingTypedGeometry,normalize,moving_typed_geometry
from impact_specs import ActorHandle,ActorKind
from world_actor_runtime import ActorRegistry

class MovingTypedTests(unittest.TestCase):
    def fixture(self):
        clock=S();manager=S();state=dict(gen=1,alive=True);registry=ActorRegistry()
        registry.bind(ActorKind.ADD,'add',lambda:(state['gen'],state['alive'],None),identity=1)
        geometry=S(boss=clock,bindings={'add':S(identity=1)})
        motion=S(spec=dict(actors=[dict(label='add')]),geometry=geometry,last_time=2.,manager=manager,
            initial={'add':dict(x=-200.,y=5.)},states={'add':dict(handle=ActorHandle(5,1,1),position=[-100.,15.])})
        world=S(clock=clock,last=2.,bindings=[S(label='attached',owner=ActorHandle(5,1,1)),S(label='body',owner=ActorHandle(0,0,1))])
        spec=dict(mode='visible-with-moving-owner-v1',bindings=[dict(typed_label='attached',actor_label='add')])
        return MovingTypedGeometry(motion,spec),world,state,registry,spec
    def test_translation_uses_exact_current_owner_and_preserves_literal_input_and_body(self):
        runtime,world,_,registry,_=self.fixture();shape=dict(x=-190.,y=7.,r=20.)
        runtime.validate_world(world)
        with patch('coordinate_moving_typed_geometry.registry_for',return_value=registry):
            result=runtime.position(world,0,shape)
            self.assertEqual((result['x'],result['y']),(-90.,17.));self.assertEqual(shape,dict(x=-190.,y=7.,r=20.))
            self.assertIs(runtime.position(world,1,shape),shape)
    def test_dead_unspawned_future_and_stale_owners_are_hidden_without_retargeting(self):
        for variant in ('dead','unspawned','future','stale'):
            with self.subTest(variant=variant):
                runtime,world,state,registry,_=self.fixture()
                if variant=='dead':state['alive']=False
                if variant=='unspawned':runtime.motion.states.clear()
                if variant=='future':world.bindings[0].owner=ActorHandle(5,1,2)
                if variant=='stale':state['gen']=2;runtime.motion.states['add']['handle']=ActorHandle(5,1,2)
                old=world.bindings[0].owner
                with patch('coordinate_moving_typed_geometry.registry_for',return_value=registry):self.assertIsNone(runtime.position(world,0,dict(x=0.,y=0.)))
                self.assertEqual(world.bindings[0].owner,old);self.assertFalse(runtime.data['queries'][-1]['visible'])
    def test_capture_before_movement_or_from_another_generation_is_rejected(self):
        for variant in ('time','generation'):
            runtime,world,state,registry,_=self.fixture()
            if variant=='time':world.last=3.
            else:state['gen']=2
            with self.subTest(variant=variant),patch('coordinate_moving_typed_geometry.registry_for',return_value=registry),self.assertRaises(ValueError):runtime.position(world,0,dict(x=0.,y=0.))
    def test_binding_owner_clock_and_explicit_attachment_cannot_change(self):
        for variant in ('owner','clock','unknown','omitted'):
            runtime,world,_,_,_=self.fixture()
            if variant=='owner':world.bindings[0].owner=ActorHandle(5,2,1)
            if variant=='clock':world.clock=S()
            if variant=='unknown':world.bindings[0].label='unknown'
            if variant=='omitted':world.bindings[1].owner=ActorHandle(5,1,1)
            with self.subTest(variant=variant),self.assertRaises(ValueError):runtime.validate_world(world)
    def test_coordinate_overflow_is_not_silently_clamped(self):
        runtime,world,_,registry,_=self.fixture();runtime.motion.initial['add']['x']=-1e308;runtime.motion.states['add']['position'][0]=1e308
        with patch('coordinate_moving_typed_geometry.registry_for',return_value=registry),self.assertRaisesRegex(ValueError,'overflow'):runtime.position(world,0,dict(x=1e308,y=0.))
    def test_original_whole_rosters_and_all_six_worlds_are_retained(self):
        from portable_moving_typed_cases import fixtures,prepare
        rows=fixtures();self.assertEqual(len(rows),6);self.assertEqual(len({r['name'] for r in rows}),6)
        for row in rows:
            c,p=prepare(row)
            self.assertEqual(c['duration'],30);self.assertTrue(c['sampled_groups']);self.assertIn(len(p['effects']),(69,71))
            self.assertEqual(c['effects'],[r['effect'] for r in p['effects']]);self.assertEqual(len(c['typed_bindings']),2)
    def test_scoped_hooks_are_restored_when_work_raises(self):
        import coordinate_typed_geometry_runtime as geometry
        from coordinate_typed_weapon_runtime import CoordinateWeaponShots
        from coordinate_typed_aim_runtime import TypedCoordinateAim
        from calculator import timeline
        from portable_moving_typed_cases import fixtures
        row=fixtures()[0];before=(geometry.live_rows,TypedCoordinateAim.capture,CoordinateWeaponShots.take,timeline.simulate)
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with moving_typed_geometry(row['logical_geometry'],row['enemy_movement'],row['typed_attachment']):raise RuntimeError('injected')
        self.assertEqual(before,(geometry.live_rows,TypedCoordinateAim.capture,CoordinateWeaponShots.take,timeline.simulate))

if __name__=='__main__':unittest.main()
