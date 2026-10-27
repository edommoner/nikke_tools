"""Logical geometry preserves actual enemy identity and existing shot semantics."""
import copy,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from coordinate_logical_actor_geometry import normalize,LogicalGeometry,live_for_handle,logical_actor_geometry
from impact_specs import ActorHandle,ActorKind
from world_actor_runtime import ActorRegistry
from portable_logical_geometry_cases import fixtures
from world_logical_geometry_native import observe
from portable_logical_geometry_contracts import verify

class LogicalActorGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={c['contract']['scenario']:c for c in fixtures()}
        cls.observed={}
        for label in ('four-live','part-not-enemy','retirement'):
            n,t=observe(cls.cases[label]);verify(cls.cases[label],n);cls.observed[label]=n

    def test_literal_shapes_are_bounded_strict_and_copied(self):
        spec=[dict(label='enemy',shape=dict(x=0.,y=0.,r=10.))];before=copy.deepcopy(spec);parsed=normalize(spec)
        self.assertEqual(spec,before);parsed[0]['shape']['r']=99;self.assertEqual(spec,before)
        invalid=[[],spec*128,spec*2,[dict(label='__portable_logical_geometry_0',shape=spec[0]['shape'])],[dict(spec[0],other=True)],[dict(label='a',shape=dict(x=0,y=0,r=True))],[dict(label='a',shape=dict(x=float('nan'),y=0,r=1))],[dict(label='a',shape=dict(x=0,y=0,r=1,w=1,h=1))]]
        for value in invalid:
            with self.subTest(value=value),self.assertRaises(ValueError):normalize(value)

    def test_generation_and_kind_filter_cannot_retarget_same_label(self):
        registry=ActorRegistry();registry.bind(ActorKind.ADD,'same',lambda:(2,True,None),identity=4);row=SimpleNamespace(id='same')
        self.assertEqual(live_for_handle(registry,[row],ActorHandle(ActorKind.ADD,4,1)),[])
        self.assertEqual(live_for_handle(registry,[row],ActorHandle(ActorKind.ADD,4,2)),[row])
        self.assertEqual(live_for_handle(registry,[row],ActorHandle(ActorKind.BODY,0,1)),[])

    def test_packet_mutation_is_scoped_and_restored_even_after_failure(self):
        runtime=LogicalGeometry([dict(label='a',shape=dict(x=0,y=0,r=1))]);runtime.boss=object();manager=object()
        event=SimpleNamespace(target='__portable_logical_geometry_0',to=None,rule=None,split=False,caster='owner',damage=7)
        handle=ActorHandle(ActorKind.ADD,0,1);runtime.pending[id(event)]=(event,manager,handle,'a')
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with runtime.land(manager,runtime.boss,event,0.):
                self.assertEqual((event.target,event.to),('',('a',)));raise RuntimeError('injected')
        self.assertEqual((event.target,event.to),('__portable_logical_geometry_0',None));self.assertFalse(runtime.pending);self.assertFalse(runtime.routing)

    def test_nonprojected_pellet_keeps_exact_original_fallback(self):
        runtime=LogicalGeometry([dict(label='a',shape=dict(x=0,y=0,r=1))]);sentinel=object();called=[]
        def fallback(*args):called.append(args);return sentinel
        def rewritten(*args):raise AssertionError('Unprojected original must not enter logical channels')
        pellet=runtime.pellet(rewritten,fallback);args=(object(),None,0.,object(),{}, {},{},False,lambda x:x,{})
        self.assertIs(pellet(*args),sentinel)
        runtime.frames.append(dict(normal=False));self.assertIs(pellet(*args),sentinel)
        self.assertEqual(called,[args,args]);self.assertFalse(runtime.data['pellets'])

    def test_original_four_enemy_skill_really_fires_without_extra_effects(self):
        n=self.observed['four-live'];self.assertTrue(n['notices']);self.assertEqual(n['original_input_identity']['added_effects'],0)
        self.assertTrue(all(len(g['targets'])==4 for g in n['groups']));self.assertTrue(n['battle']['add_total']>0)
        bad=copy.deepcopy(n);bad['notices']=[]
        with self.assertRaises(AssertionError):verify(self.cases['four-live'],bad)

    def test_real_part_cannot_supply_fourth_logical_enemy(self):
        n=self.observed['part-not-enemy'];self.assertFalse(n['notices']);self.assertTrue(any(e['target']=='real-part' for e in n['battle']['hits']))
        self.assertTrue(all(len(g['targets'])<=3 for g in n['groups']))

    def test_retired_adds_do_not_receive_original_group_children(self):
        n=self.observed['retirement'];self.assertEqual(n['battle']['add_total'],3)
        self.assertTrue(n['child_landings']);self.assertTrue(all(h['target'][0]==0 for h in n['child_landings']))

    def test_scope_restores_canonical_aliases_and_deterministic_results(self):
        from calculator import timeline
        from runner import sim
        before=(timeline.simulate,sim.simulate,timeline.BossScript,timeline.CharState._coord_pellet,timeline.CharState._fire)
        again,_=observe(self.cases['four-live']);self.assertEqual(again,self.observed['four-live'])
        self.assertEqual(before,(timeline.simulate,sim.simulate,timeline.BossScript,timeline.CharState._coord_pellet,timeline.CharState._fire))

    def test_unknown_or_part_binding_fails_before_a_live_frame_and_restores_aliases(self):
        from calculator import timeline
        from runner import sim
        before=(timeline.simulate,sim.simulate,timeline.BossScript)
        bad=copy.deepcopy(self.cases['part-not-enemy']);bad['logical_geometry'][0]['label']='real-part'
        with self.assertRaisesRegex(ValueError,'configured ADD'):observe(bad)
        self.assertEqual(before,(timeline.simulate,sim.simulate,timeline.BossScript))

    def test_native_reference_is_not_registered_as_a_gpu_suite(self):
        import nikke_gpu
        from portable_reference import REFERENCES
        self.assertIn('logical-actor-geometry-common',REFERENCES)
        self.assertNotIn('logical-actor-geometry-common',nikke_gpu.SUITES)
        result=verify(self.cases['four-live'],self.observed['four-live'])
        self.assertFalse(result['gpu_supported']);self.assertFalse(result['gpu_wire_connected']);self.assertTrue(result['reference_model_gap'])

if __name__=='__main__':unittest.main()
