import array,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('shape_test',ROOT/'research/verify-coordinate-shape-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class CoordinateShapeTests(unittest.TestCase):
    def test_original_shape_boundaries_and_rotation(self):
        rows=a.fixtures();actual=[a.native_reference((c,)) for c in rows]
        self.assertTrue(actual[16]['contains']);self.assertFalse(actual[31]['contains'])
        self.assertTrue(actual[46]['contains']);self.assertFalse(actual[61]['contains'])
    def test_static_input_and_whole_buffer_comparator(self):
        from calculator.aim import Shape
        with patch.object(Shape,'dist',side_effect=AssertionError('No CPU distance in input')),patch.object(Shape,'contains',side_effect=AssertionError('No CPU selection in input')):entries,raw=a.prepare()
        self.assertEqual(len(entries),158);self.assertEqual(len(raw),4+158*24*4)
        d=entries[0][2];e=a.native_reference(d);v=e['distance_bits'];b=array.array('I',[0,0x43534831,v&0xffffffff,v>>32,int(e['contains']),0,0,0]);a.compare(b,d);b[-1]=1
        with self.assertRaises(AssertionError):a.compare(b,d)
if __name__=='__main__':unittest.main()
