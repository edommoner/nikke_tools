"""Preserve canonical modulo correction, compensated sum and degenerate arcs."""
import array,importlib.util,math,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('arc_scalar_test',ROOT/'research/verify-coordinate-arc-scalar-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class ArcScalarTests(unittest.TestCase):
    def test_packing_does_not_evaluate_arc_math(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No native packing')),patch.object(a.aim,'_arc',side_effect=AssertionError('No geometry packing')):
            entries,raw=a.prepare()
        self.assertEqual(len(raw),4+len(entries)*2056*4)
        self.assertEqual(sum(d is None for _,_,d in entries),8)
    def test_tiny_negative_modulo_and_zero_width_arc_are_preserved(self):
        self.assertEqual(a.native_reference((1,-1e-300,0.,[]))['scalar'],math.tau)
        self.assertEqual(a.native_reference((2,-1e-300,1e-300,[]))['intervals'],[(math.tau,math.tau)])
        self.assertEqual(a.native_reference((4,.3,0.,[(math.tau,math.tau)]))['intervals'],[])
    def test_compensated_native_measure_differs_from_naive_accumulation(self):
        name,op,x,y,arcs=next(row for row in a.fixtures() if row[0]=='measure/compensated')
        naive=0.
        for start,end in arcs:naive+=end-start
        self.assertNotEqual(naive,a.native_reference((op,x,y,arcs))['scalar'])
    def test_generated_zero_width_cover_splits_subtraction_but_not_intersection(self):
        self.assertEqual(a.native_reference((8,1.,1e-300,[(0.,2.)]))['intervals'],[(0.,1.),(1.,2.)])
        self.assertEqual(a.native_reference((9,1.,1e-300,[(0.,2.)]))['intervals'],[])
    def test_reserved_opcode_negative_case_is_disjoint_from_all_positive_operations(self):
        rows,_=a.prepare();positive={w[2] for _,w,d in rows if d is not None}
        self.assertEqual(positive,{1,2,3,4,8,9})
        rejected=next(w for name,w,d in rows if name=='reject/coordinate-arc-scalar-op')
        self.assertNotIn(rejected[2],positive)
    def test_probe_reuses_existing_sum_without_copying_or_changing_it(self):
        shader=(ROOT/'gpu/coordinate_arc_scalar_probe.slang').read_text();shared=(ROOT/'gpu/coordinate_arc_scalar.slang').read_text()
        self.assertIn('#include "event_runtime.slang"',shader)
        self.assertIn('addSum(sum,',shared);self.assertNotIn('sum.correction =',shared)
    def test_full_output_scalar_interval_and_padding_mutations_are_detected(self):
        domain=(2,-1e-300,1e-300,[]);e=a.native_reference(domain);words=[0]*4104;words[:3]=[0,0x43415331,len(e['intervals'])];words[4:6]=a.bits(e['scalar'])
        for i,(s,t) in enumerate(e['intervals']):words[8+i*4:12+i*4]=a.bits(s)+a.bits(t)
        a.compare(array.array('I',words),domain)
        for at in [0,2,4,8,4103]:
            changed=list(words);changed[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(array.array('I',changed),domain)
if __name__=='__main__':unittest.main()
