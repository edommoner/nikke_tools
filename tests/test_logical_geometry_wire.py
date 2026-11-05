"""Real roster lowering and hostile raw descriptors; never CPU-authored hits."""
import copy,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from calculator.boss_pattern import validate as patterns
from portable_actor_specs import compile_registry
from portable_logical_geometry_cases import fixtures
from portable_logical_geometry_wire import LAYOUT,pack,validate,compile_logical_geometry,check_schema,input_regions

class LogicalGeometryWire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[]
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle in input lowering')):
            for case in fixtures():
                prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
                prepared['enemy'].update(coord=copy.deepcopy(case['coord']),patterns=copy.deepcopy(case['patterns']))
                cls.rows.append((case,prepared,compile_logical_geometry(prepared,case['logical_geometry'])))

    def test_shader_schema_and_six_complete_original_rosters(self):
        check_schema(ROOT)
        self.assertEqual(len(self.rows),6)
        for case,prepared,(words,meta,bindings,scene) in self.rows:
            with self.subTest(case=case['name']):
                self.assertEqual(len(words),115680)
                self.assertEqual(len(prepared['effects']),68)
                self.assertEqual(meta['coordinate_original_input']['prepared_definitions'],68)
                self.assertFalse(meta['logical_actor_geometry_wire']['gpu_wire_connected'])
                result=validate(words[LAYOUT['BASE']:],words[:LAYOUT['BASE']],bindings)
                self.assertEqual(result['colliders'],case['contract']['count'])
                self.assertFalse(result['health_copied'])

    def test_input_ownership_and_original_coordinate_bytes(self):
        from portable_arena_specs import audit_regions
        from portable_coordinate_roster_input import compile_coordinate_battle
        audit=audit_regions(input_regions(),115680,1769856)
        self.assertTrue(audit['address_plan_verified'])
        self.assertEqual(sum(r.words for r in input_regions()),115680)
        for case,prepared,(words,_,bindings,_) in self.rows:
            before=copy.deepcopy(prepared)
            with patch.object(timeline,'simulate',side_effect=AssertionError('No simulated wire')):
                original,_,_,_=compile_coordinate_battle(prepared)
            self.assertEqual(words[:LAYOUT['BASE']],original)
            self.assertEqual(prepared,before)

    def test_part_and_body_never_enter_logical_map(self):
        case,_,(words,_,bindings,scene)=next(r for r in self.rows if r[0]['contract']['part'])
        bank=words[LAYOUT['BASE']:]
        self.assertTrue(scene['rows'])
        for slot,binding in enumerate(bindings):
            self.assertEqual(bool(bank[LAYOUT['MAP_BASE']+slot]),int(binding.kind)==5)

    def test_corrupt_identity_map_shape_and_reserved_fail_closed(self):
        _,_,(words,_,bindings,_)=self.rows[0];base=words[:LAYOUT['BASE']];bank=words[LAYOUT['BASE']:]
        for at in (0,1,3,4,32,33,34,35,36,37,38,39,58,4096,4097,4224,5711):
            bad=list(bank);bad[at]^=1
            with self.subTest(at=at),self.assertRaises(ValueError):validate(bad,base,bindings)
        for payload in ([True]+bank[1:],bank[:-1],bank+[0],[-1]+bank[1:]):
            with self.assertRaises(ValueError):validate(payload,base,bindings)
        for pair in ((0x7ff00000,0),(0x7ff80000,0)):
            bad=list(bank);bad[40:42]=[pair[1],pair[0]]
            with self.assertRaises(ValueError):validate(bad,base,bindings)

    def test_registry_owner_and_duplicate_slot_rejected(self):
        _,_,(words,_,bindings,_)=self.rows[0];bank=words[LAYOUT['BASE']:];base=words[:LAYOUT['BASE']]
        from portable_specs import LIMITS as L
        bad=list(base);bad[L['WORLD_ACTOR_BINDING_BASE']+bank[32]*8+3]^=1
        with self.assertRaises(ValueError):validate(bank,bad,bindings)
        bad=list(base);bad[L['WORLD_ACTOR_INPUT_BASE']+1]-=1
        with self.assertRaises(ValueError):validate(bank,bad,bindings)
        bad=list(bank);bad[64]=bad[32]
        with self.assertRaises(ValueError):validate(bad,base,bindings)

    def test_unknown_body_part_and_overall_actor_capacity_rejected(self):
        case,_,(_,_,bindings,_)=self.rows[3]
        for label in ('absent','__enemy__','real-part'):
            spec=copy.deepcopy(case['logical_geometry']);spec[0]['label']=label
            with self.subTest(label=label),self.assertRaises(ValueError):pack(spec,bindings)
        excessive=[dict(id='wave',kind='summon',spec=dict(count=127,hp=10)),dict(id='part',kind='parts',targets=[dict(name='part',hp=10,x=0,y=0,r=1)])]
        with self.assertRaisesRegex(ValueError,'capacity'):compile_registry(patterns(excessive,coord=True),pools=True)

    def test_full_actor_capacity_and_reverse_binding_order(self):
        _,bindings=compile_registry(patterns([dict(id='wave',kind='summon',spec=dict(count=127,hp=10))],coord=True),pools=True)
        spec=[dict(label=b.label,shape=dict(x=0.,y=0.,r=1.)) for b in reversed(bindings[1:])]
        bank=pack(spec,bindings)
        self.assertEqual(bank[2:4],[127,128])
        self.assertEqual(bank[LAYOUT['MAP_BASE']+1:LAYOUT['MAP_BASE']+128],list(range(127,0,-1)))

    def test_no_mutation_and_shared_rotation_bytes(self):
        from portable_coordinate_matrix_specs import coefficients
        from portable_coordinate_scene_specs import bits
        from types import SimpleNamespace
        case,_,(_,_,bindings,_)=self.rows[0];spec=copy.deepcopy(case['logical_geometry'])
        spec[0]['shape']=dict(x=3.,y=-4.,r=0.,w=10.,h=20.,rot=37.,z=2.)
        before=copy.deepcopy(spec);bank=pack(spec,bindings)
        self.assertEqual(spec,before)
        co,si=coefficients(SimpleNamespace(rot=37.,is_circle=False))
        self.assertEqual(bank[54:58],bits(co)+bits(si))

if __name__=='__main__':unittest.main()
