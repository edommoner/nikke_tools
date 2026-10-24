import copy,importlib.util,math,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_area_specs import LAYOUT as A,compile_area
from portable_coordinate_scene_specs import LAYOUT as C
s=importlib.util.spec_from_file_location('area_test',ROOT/'research/verify-coordinate-area-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class CoordinateAreaTests(unittest.TestCase):
    def test_all_native_shape_and_lifecycle_contracts(self):
        for c in a.fixtures():a.native_reference((c,))
    def test_static_compiler_only_folds_authored_rotation(self):
        from calculator import timeline,aim
        import struct
        case=a.fixtures()[0];before=copy.deepcopy(case)
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle in input')),patch.object(aim.Shape,'dist',side_effect=AssertionError('No CPU distances in input')),patch.object(aim.Shape,'contains',side_effect=AssertionError('No CPU target selection in input')):
            words,meta,bindings,desc=a.compile_case(case)
        self.assertEqual(case,before);self.assertEqual(len(words),108640)
        def value(at):return struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
        for i,row in enumerate(desc['rows']):
            at=A['BASE_INPUT']+A['HEADER']+row['slot']*8;shape=row['shape'];self.assertEqual(value(at+2),math.cos(math.radians(shape.rot)));self.assertEqual(value(at+4),math.sin(math.radians(shape.rot)))
            self.assertEqual(value(a.parent.parent.BASE_INPUT+C['ROW_BASE']+i*C['ROW_WORDS']+16),0)
    def test_native_focus_policy_is_lowered_and_conflicts_are_rejected(self):
        c=next(c for c in a.fixtures() if c['name']=='coordinate-area/layer2-center');w,_,_,_=a.compile_case(c)
        from portable_specs import LIMITS as L
        self.assertEqual(w[L['WORLD_META_BASE']+4],0x46414331)
        c['environment']['focus_aim_layer2']=False
        with self.assertRaisesRegex(ValueError,'Conflicting focus'):a.compile_case(c)
    def test_input_pack_has_all_positive_contracts_and_explicit_rejections(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No native oracle in pack')):entries,raw=a.prepare()
        self.assertEqual(len(entries),52);self.assertEqual(sum(d is not None for _,_,d in entries),42);self.assertEqual(len(raw),4+52*a.INPUT_WORDS*4)
if __name__=='__main__':unittest.main()
