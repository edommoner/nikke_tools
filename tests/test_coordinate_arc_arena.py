"""Resource views preserve canonical capacity, inputs and complete comparisons."""
import array,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_coordinate_arc_arena as arena
s=importlib.util.spec_from_file_location('test_arc_arena_adapter',ROOT/'research/verify-coordinate-arc-arena-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ArcArenaTests(unittest.TestCase):
    def test_generated_bodies_are_current(self):
        arena.check(ROOT)
        self.assertEqual((arena.CAPACITY,arena.SLOTS,arena.ROW_WORDS,arena.WORDS),(1024,8,4098,32786))

    def test_unknown_local_lifetime_fails_closed(self):
        source='void coordinateArcShift(CoordinateArcSet a,out CoordinateArcSet value){CoordinateArcSet unreviewed;}'
        with self.assertRaisesRegex(ValueError,'Unreviewed arena lifetime'):arena.transform(source,'coordinateArcShift')

    def test_canonical_arithmetic_is_not_reimplemented(self):
        source=(ROOT/'gpu/coordinate_arc_sets.slang').read_text()
        body=arena.transform(source,'coordinateArcSubtract')
        self.assertIn('if(!arcArenaDistinct(a,b,value))return;',body)
        self.assertNotIn('CoordinateArcSet',body)
        self.assertIn('cur=d;',body)
        # Changed canonical arithmetic must change the generated body.
        changed=source.replace('cur=d;','cur=e;')
        self.assertNotEqual(arena.transform(changed,'coordinateArcSubtract'),body)

    def test_all_old_inputs_and_native_references_are_retained(self):
        with patch.object(a.parent,'native_reference',side_effect=AssertionError('No native while packing')):
            entries,raw=a.prepare()
        old,oldraw=a.parent.prepare()
        self.assertEqual(entries[:135],old)
        self.assertEqual(raw[4:4+135*4104*4],oldraw[4:])
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(140,131))
        for (_,_,domain),(_,_,previous) in zip(entries,old):
            if domain is not None:self.assertEqual(a.native_reference(domain),a.parent.native_reference(previous))

    def test_all_scratch_and_logical_words_are_compared(self):
        domain=(1,[],[]);words=[0]*a.OUTPUT_WORDS;words[1]=0x43415243
        a.compare(array.array('I',words),domain)
        for at in [0,4099,4100,4101,a.OUTPUT_WORDS-1]:
            changed=list(words);changed[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(changed,domain)

    def test_guard_words_observe_errors_and_preserve_adjacent_values(self):
        for mode in range(1,6):
            domain=dict(storage_guard=mode);words=a.diagnostic_words(mode)
            a.compare(words,domain)
            for at in [3,4,5,6,7,8,a.OUTPUT_WORDS-1]:
                changed=list(words);changed[at]^=1
                with self.subTest(mode=mode,at=at),self.assertRaises(AssertionError):a.compare(changed,domain)

    def test_rejections_clear_entire_scratch(self):
        words=[64]+[0]*(a.OUTPUT_WORDS-1)
        a.validate_rejection(words,'reject/coordinate-arcs-magic')
        words[-1]=1
        with self.assertRaises(AssertionError):a.validate_rejection(words,'reject/coordinate-arcs-magic')

if __name__=='__main__':unittest.main()
