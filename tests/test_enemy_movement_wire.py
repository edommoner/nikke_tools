"""Whole original movement input, no baked state, disjoint runtime ownership."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_enemy_movement_cases import fixtures
from portable_enemy_movement_wire import compile_battle,check_schema,INPUT,OUTPUT,OUT,END,FRAMES,SEGMENTS,CAPACITY,FRAME_WORDS,SEGMENT_WORDS,BASE,MAP
from portable_coordinate_original_cases import prepare_case
from portable_logical_geometry_wire import compile_logical_geometry
from portable_specs import LIMITS as L,FIELDS as F

class MovementWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures()
    def test_original_effects_and_all_world_owners_are_preserved_without_time_or_position_history(self):
        check_schema(ROOT)
        for row in self.cases:
            case,p=prepare_case(row);before=copy.deepcopy(p)
            w,m,bindings,scene=compile_battle(p,row['logical_geometry'],row['enemy_movement'])
            self.assertEqual(p,before);self.assertEqual(len(w),INPUT)
            self.assertEqual(len(m['binding_source_indices']),len(p['effects']))
            self.assertEqual(w[BASE+3],len(p['effects']));self.assertEqual(w[BASE+4],len(bindings))
            expected=[i for i,e in enumerate(p['effects']) if e['effect'].get('stat') in ('force_move','enemy_movement_disable')]
            self.assertEqual(sorted(d['source_row'] for d in m['enemy_movement']['domains']),expected)
            for d in m['enemy_movement']['domains']:
                at=L['DEFINITION_BASE']+d['row']*L['DEFINITION_WORDS']
                self.assertEqual((w[at+F['KIND']],w[at+F['STAT']],w[BASE+MAP+d['row']]),(0,0,d['kind']))
            self.assertFalse(m['enemy_movement']['gpu_admitted'])
        self.assertLessEqual(END,OUTPUT);self.assertEqual(OUT+SEGMENTS,OUT+FRAMES+CAPACITY*FRAME_WORDS)
        self.assertEqual(END,OUT+SEGMENTS+CAPACITY*SEGMENT_WORDS)
    def test_default_compiler_remains_closed_and_declared_policy_cannot_change_original_duration(self):
        row=self.cases[0];case,p=prepare_case(row)
        with self.assertRaises(ValueError):compile_logical_geometry(p,row['logical_geometry'])
        for key,value in [('duration',6.),('target','all_enemies'),('max_stack',2)]:
            changed=copy.deepcopy(p)
            effect=next(e['effect'] for e in changed['effects'] if e['effect'].get('stat')=='enemy_movement_disable');effect[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):compile_battle(changed,row['logical_geometry'],row['enemy_movement'])
    def test_exact_source_inverse_retains_every_original_byte_and_rejects_unreviewed_changes(self):
        from portable_enemy_movement_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-enemy-movement-source-delta.json').read_text());out=project_sources(ROOT)
        for name,row in data['files'].items():
            self.assertEqual(hashlib.sha256(out[name].encode()).hexdigest(),row['before_sha256'])
            with self.subTest(name=name),self.assertRaises(ValueError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// changed'})
    def test_movement_output_requires_all_state_frames_segments_and_padding(self):
        s=importlib.util.spec_from_file_location('movement_output_suite',ROOT/'research/verify-enemy-movement.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        from types import SimpleNamespace
        import struct
        frame=dict(label='add',actor=[5,'add',1],alive=True,time=1.,position=[20.,0.],
            segments=[dict(start=0.,end=1.,disabled=False,forced=False,before=[0.,0.],after=[20.,0.])])
        native=dict(enemy_movement=dict(frames=[frame]));domain=(None,None,[SimpleNamespace(label='body'),SimpleNamespace(label='add')])
        block=[0]*OUTPUT;block[OUT:OUT+3]=[m.MAGIC,1,1]
        def number(at,value):block[at:at+2]=struct.unpack('<II',struct.pack('<d',value))
        state=OUT+m.STATE+m.STATE_WORDS;block[state]=1;block[state+1]=1;block[state+8]=1
        number(state+2,1.);number(state+4,20.)
        at=OUT+FRAMES;block[at:at+5]=[1,1,1,0,1];number(at+6,1.);number(at+8,20.)
        at=OUT+SEGMENTS;block[at:at+3]=[1,1,0];number(at+6,1.);number(at+12,20.)
        clean=m.compare_movement(block,domain,native);self.assertFalse(any(clean[OUT:END]));self.assertTrue(any(block[OUT:END]))
        for at in (state,state+4,OUT+FRAMES+4,OUT+FRAMES+8,OUT+SEGMENTS+2,OUT+SEGMENTS+12,END-1):
            broken=block.copy();broken[at]^=1
            with self.subTest(word=at),self.assertRaises(AssertionError):m.compare_movement(broken,domain,native)

    def test_shared_native_uses_every_frame_and_preserves_whole_battle_comparer(self):
        s=importlib.util.spec_from_file_location('movement_wire_suite',ROOT/'research/verify-enemy-movement.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        entries,data=m.prepare();self.assertEqual(len(entries),15);self.assertEqual(len(data),4+15*INPUT*4)
        self.assertEqual(len(entries[0][2][0]['effects']),69)
        self.assertEqual(entries[0][2][0]['duration'],30)

if __name__=='__main__':unittest.main()
