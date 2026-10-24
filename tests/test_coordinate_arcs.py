"""Canonical angular topology, full capacity and exact saved words."""
import array,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('arc_test_adapter',ROOT/'research/verify-coordinate-arcs-short.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class ArcTests(unittest.TestCase):
    def test_static_input_does_not_compute_geometry_or_sets(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No native packing')),patch.object(a.aim,'_union',side_effect=AssertionError('No sets packing')):
            entries,raw=a.prepare()
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(135,126))
        self.assertEqual(len(raw),4+135*4104*4)

    def test_touching_intervals_merge_but_intersection_is_empty(self):
        self.assertEqual(a.native_reference((1,[(0.,1.)],[(1.,2.)]))['intervals'],[(0.,2.)])
        self.assertEqual(a.native_reference((2,[(0.,1.)],[(1.,2.)]))['intervals'],[])
        self.assertEqual(a.native_reference((3,[(0.,3.)],[(1.,2.)]))['intervals'],[(0.,1.),(2.,3.)])

    def test_union_and_subtraction_retain_1024_intervals(self):
        for name,op,left,right in a.fixtures():
            if (name,op) in [('capacity-1024/1',1),('capacity-subtract-1024/3',3)]:
                self.assertEqual(len(a.native_reference((op,left,right))['intervals']),1024)

    def test_whole_buffer_including_unused_tail_is_compared(self):
        domain=(3,[(0.,3.)],[(1.,2.)]);words=[0]*4100;values=a.native_reference(domain)['intervals'];words[:3]=[0,0x43415243,len(values)]
        for i,(start,end) in enumerate(values):words[4+i*4:8+i*4]=a.bits(start)+a.bits(end)
        a.compare(array.array('I',words),domain)
        for offset in [0,2,4,4099]:
            changed=list(words);changed[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(AssertionError):a.compare(array.array('I',changed),domain)


if __name__=='__main__':unittest.main()
