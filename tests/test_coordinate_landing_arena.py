"""Full landing inputs and complete readbacks survive resource-view lowering."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_coordinate_arc_arena as arena
s=importlib.util.spec_from_file_location('test_landing_arena_adapter',ROOT/'research/verify-coordinate-landing-arena-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class LandingArenaTests(unittest.TestCase):
    def test_inputs_and_domains_are_identical(self):
        entries,raw=a.prepare();old,previous=a.parent.prepare()
        self.assertEqual(entries,old);self.assertEqual(raw,previous)
        self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(40,26))

    def test_full_capacities_and_explicit_live_slots(self):
        arena.check(ROOT)
        self.assertEqual((arena.landing.TARGETS,arena.landing.CUTS,arena.CAPACITY),(127,5098,1024))
        output=(ROOT/'gpu/coordinate_landing_arena_ops.slang').read_text()
        self.assertNotIn('CoordinateArcSet',output)
        self.assertIn('arcArenaView(output,CL_OUTPUT,0U)',output)
        self.assertIn('arcArenaView(output,CL_OUTPUT,1U)',output)
        self.assertIn('arcArenaView(output,CL_OUTPUT,2U)',output)
        self.assertIn('arena_coordinatePreparedAssign(arcs,shifted)',output)
        self.assertIn('arena_coordinatePreparedAssign(value,next)',output)

    def test_complete_scratch_is_compared(self):
        entries,_=a.prepare();domain=next(d for n,w,d in entries if n.endswith('/center-target'))
        words,reference=a.expected(domain)
        self.assertEqual(a.compare(words,domain),reference)
        for at in [0,a.parent.OUTPUT_WORDS-1,a.parent.OUTPUT_WORDS,a.OUTPUT_WORDS-1]:
            changed=list(words);changed[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(changed,domain)

    def test_rejection_has_no_temporary_values(self):
        words=[64]+[0]*(a.OUTPUT_WORDS-1);a.validate_rejection(words,'reject/coordinate-landing/magic')
        words[-1]=1
        with self.assertRaises(AssertionError):a.validate_rejection(words,'reject/coordinate-landing/magic')

if __name__=='__main__':unittest.main()
