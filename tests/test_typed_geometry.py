"""Live point selection uses the existing clock and deterministic shape reference."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_typed_geometry_specs import pack,normalize,WORDS
from destructible_world_runtime import DestructibleWorld
from typed_geometry_reference import select
from impact_specs import ActorHandle,ActorKind,HitFamily,HitOutcome,Impact
class TypedGeometryTests(unittest.TestCase):
    def world(self,*,repeat=0):
        return DestructibleWorld([dict(id='world',after=['start','world'] if repeat else ['start'],until=dict(time=1),repeat=repeat)],[dict(node='world',kind=2,identity=i,capacity=1000.) for i in (10,11)])
    def geometry(self):return dict(point=[0.,0.],shapes=[dict(x=0.,y=0.,r=10.,z=2.),dict(x=0.,y=0.,r=10.,z=1.)])
    def test_live_damage_expiry_and_generation_change(self):
        world=self.world(repeat=2);g=self.geometry();self.assertIsNone(select(world,g,2));world.advance(0.);self.assertEqual(select(world,g,2),(0,ActorHandle(2,10,1)))
        world.hit(0,Impact('a',ActorHandle(2,10),HitFamily.SKILL,HitOutcome.DAMAGING,1000.));self.assertEqual(select(world,g,2),(1,ActorHandle(2,11,1)))
        world.advance(1.);self.assertEqual(select(world,g,2),(0,ActorHandle(2,10,2)))
        world.finish(2.);self.assertIsNone(select(world,g,2))
    def test_rotation_growth_and_stable_binding_tie(self):
        world=self.world();world.advance(0.);g=self.geometry();g['shapes'][0]=dict(x=2.,y=0.,w=8.,h=2.,rot=90.,z=2.)
        self.assertEqual(select(world,g,2)[0],1);g['grow']=1.;self.assertEqual(select(world,g,2)[0],0)
        g['shapes']=[dict(x=0.,y=0.,r=1.,z=1.)]*2;self.assertEqual(select(world,g,2)[0],1)
    def test_input_is_literal_and_rejects_unknown_or_invalid_fields(self):
        spec=self.geometry();before=copy.deepcopy(spec);words,meta=pack(spec,2,2);self.assertEqual(spec,before);self.assertEqual(len(words),WORDS);self.assertEqual(words[:4],[0x54474731,1,2,2])
        for change in (dict(point=[True,0.]),dict(grow=-1.),dict(point=[float('nan'),0.]),dict(shapes=[]),dict(schedule=[])):
            with self.subTest(change=change),self.assertRaises(ValueError):pack(dict(spec,**change),2,2)
        for kind in (True,0,4):
            with self.assertRaises(ValueError):normalize(spec,2,kind)
        for shape in (dict(x=0.,y=0.,r=-1.),dict(x=0.,y=0.,r=1.,w=1.),dict(x=0.,y=0.,w=1.,h=0.),dict(x=0.,y=0.,r=1.,future=1)):
            bad=copy.deepcopy(spec);bad['shapes'][0]=shape
            with self.subTest(shape=shape),self.assertRaises(ValueError):pack(bad,2,2)
if __name__=='__main__':unittest.main()
