"""Live point selection uses the existing clock and deterministic shape reference."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_typed_geometry_specs import pack,normalize,WORDS
from destructible_world_runtime import DestructibleWorld
from typed_geometry_reference import select,select_for_caster,caster_aim
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
    def test_live_source_has_no_literal_or_precomputed_schedule(self):
        g=self.geometry();g.pop('point');g['point_source']='caster_aim';words,_=pack(g,2,2)
        self.assertEqual(words[4:8],[0]*4);self.assertEqual(words[11],1)
        for change in (dict(point=[0.,0.]),dict(point_source='unknown'),dict(point_source=True)):
            with self.subTest(change=change),self.assertRaises(ValueError):pack(dict(g,**change),2,2)
        w=self.world();w.advance(0.)
        with self.assertRaises(ValueError):select(w,g,2)
        with self.assertRaises(ValueError):select(w,self.geometry(),2,point=[0.,0.])
    def test_live_aim_matches_canonical_char_state_and_current_bank(self):
        from types import SimpleNamespace
        from calculator import timeline
        g=self.geometry();g.pop('point');g['point_source']='caster_aim'
        g['shapes']=[dict(x=-20.,y=0.,r=3.),dict(x=20.,y=0.,r=3.)]
        w=self.world();w.advance(0.);geom=SimpleNamespace(auto_aim=(-20.,0.))
        bm=SimpleNamespace(state=dict(enemy={timeline.GEOM_KEY:geom},aim={}))
        cs=SimpleNamespace(name='owner')
        self.assertEqual(caster_aim(bm,'owner'),timeline.CharState._aim_point(cs,bm,geom))
        self.assertEqual(select_for_caster(w,g,2,bm,'owner')[0],0);self.assertEqual(bm.state['aim'],{})
        bm.state['aim']['owner']=((20.,0.),'right')
        self.assertEqual(caster_aim(bm,'owner'),timeline.CharState._aim_point(cs,bm,geom))
        self.assertEqual(select_for_caster(w,g,2,bm,'owner')[0],1)
        self.assertEqual(bm.state['aim']['owner'],((20.,0.),'right'))
    def test_live_aim_requires_geometry_and_finite_actual_point(self):
        from types import SimpleNamespace
        from calculator import timeline
        g=self.geometry();g.pop('point');g['point_source']='caster_aim';w=self.world();w.advance(0.)
        bm=SimpleNamespace(state=dict(enemy={},aim={}))
        with self.assertRaises(ValueError):select_for_caster(w,g,2,bm,'owner')
        bm.state['enemy'][timeline.GEOM_KEY]=SimpleNamespace(auto_aim=(float('nan'),0.))
        with self.assertRaises(ValueError):select_for_caster(w,g,2,bm,'owner')
    def test_declared_aim_overlay_preserves_originals_and_other_operations(self):
        from portable_declared_aim_controls import apply
        chars=[dict(name='owner',control=dict(priority=3),skill_levels={'1':10},_weapon={'magazine':20})]
        before=copy.deepcopy(chars);aim={'owner':[dict(at='right',priority=100)]}
        result=apply(chars,aim);self.assertEqual(chars,before);self.assertEqual(result[0]['control'],dict(priority=3,aim=aim['owner']))
        self.assertEqual(result[0]['skill_levels'],before[0]['skill_levels']);self.assertEqual(result[0]['_weapon'],before[0]['_weapon'])
        result[0]['control']['aim'][0]['at']='elsewhere';self.assertEqual(aim['owner'][0]['at'],'right')
        for invalid in ({},{'absent':[dict(at='right')]},{'owner':[]},{'owner':True},{'owner':[dict(at='right',future=True)]}):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):apply(chars,invalid)
if __name__=='__main__':unittest.main()
