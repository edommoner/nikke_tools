import importlib.util,math,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_coordinate_sample_v1 as sample
from portable_coordinate_sample_cases import fixtures
n=sample.n
spec=importlib.util.spec_from_file_location('sample_adapter',ROOT/'research/verify-coordinate-sample-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class SampleTests(unittest.TestCase):
    def test_shared_recipe_schema_and_protected_numeric_algorithms(self):sample.check_schema(ROOT)
    def test_mt_random53_exactly_matches_cpython_random_and_entire_state(self):
        for seed in (0,1,19,2**32+1,2**64-1):
            x=random.Random(seed);y=random.Random(seed)
            for _ in range(1300):self.assertEqual(sample.random53(x),n.bits(y.random()))
            self.assertEqual(x.getstate(),y.getstate())
    def test_angle_draw_count_no_early_exit_at_zero_radius_and_twist(self):
        for angle,words in [(False,2),(True,4)]:
            r=a.Stream(19)
            for _ in range(623):r.getrandbits(32)
            sample.sample(0.,0.,0.,r,angle=angle)
            self.assertEqual(r.draws,623+words);self.assertEqual(r.getstate()[1][-1],623+words-624)
    def test_native_sample_call_contract_and_centered_no_angle_compatibility(self):
        import engine_worker
        from calculator import aim
        for angle in (False,True):
            # Independent host implementation remains a reference for draw order.
            x=random.Random(19);y=random.Random(19);sample.sample(1.,-2.,16.,x,angle=angle);aim.sample(1.,-2.,16.,y,angle=angle);self.assertEqual(x.getstate(),y.getstate())
        self.assertEqual(sample.point(n.bits(1.),n.bits(-0.),n.bits(16.),n.bits(2.55),0),(n.bits(1.),n.bits(-0.)))
    def test_no_host_transcendentals_and_independent_high_precision_radius(self):
        from decimal import Decimal,localcontext
        with patch.object(math,'pow',side_effect=AssertionError('Host pow forbidden')),patch.object(math,'sin',side_effect=AssertionError('Host sin forbidden')),patch.object(math,'cos',side_effect=AssertionError('Host cos forbidden')):
            for u in (2.**-53,.125,.5,1.-2.**-53):
                x,y=sample.point(0,0,n.bits(16.),n.bits(2.55),n.bits(u))
                with localcontext() as ctx:
                    ctx.prec=160;inverse=Decimal.from_float(1./2.55);want=float(Decimal.from_float(u).__pow__(inverse))
                self.assertEqual(x,n.bits(16.*want));self.assertEqual(y,0)
    def test_domain_rejection_before_rng_draw_and_output_overflow(self):
        r=a.Stream(19)
        with self.assertRaises(ValueError):sample.sample(float('nan'),0.,1.,r)
        self.assertEqual(r.draws,0)
        for u,v in [(n.ONE,None),(n.SIGN,None),(n.bits(.5),n.ONE)]:
            with self.assertRaises(ValueError):sample.point(0,0,n.ONE,n.ONE,u,v)
        with self.assertRaises(ValueError):sample.point(n.bits(1.7e308),0,n.bits(1.7e308),n.ONE,n.bits(.9))
    def test_wire_is_authored_not_random_or_answer_table(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle packing')),patch.object(random.Random,'random',side_effect=AssertionError('No RNG packing')),patch.object(random.Random,'getrandbits',side_effect=AssertionError('No RNG packing')):rows,raw=a.prepare()
        self.assertEqual(len(raw),4+len(rows)*24*4);self.assertEqual(sum(d is not None for _,_,d in rows),len(fixtures()))
    def test_complete_state_unused_output_and_trace_corruption_are_rejected(self):
        c=fixtures()[0];e=a.native_reference(c);a.compare(e['words'],c)
        for at in [0,16,24,647,656,668,1023]:
            b=list(e['words']);b[at]^=1
            with self.assertRaises(AssertionError):a.compare(b,c)
if __name__=='__main__':unittest.main()
