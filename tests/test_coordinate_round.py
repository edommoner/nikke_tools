"""Independent exact rational derivation of decimal-six keys and sign handling."""
import importlib.util,sys,unittest,math
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('round_adapter',ROOT/'research/verify-coordinate-round-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class RoundTests(unittest.TestCase):
    def test_all_finite_inputs_match_independent_rational_oracle(self):
        for name,value in a.fixtures():
            x=a.number(value);numerator,denominator=x.as_integer_ratio();q=round(Fraction(numerator*1_000_000,denominator));exact=float(Fraction(q,1_000_000))
            if exact==0:exact=math.copysign(exact,x)
            with self.subTest(name=name):self.assertEqual(a.bits(exact),a.native_reference(value)['rounded_bits'])
    def test_scale_then_round_is_not_an_equivalent_algorithm(self):
        failures=[]
        for _,value in a.fixtures():
            x=a.number(value)
            if abs(x)<2**33 and round(x*1e6)/1e6!=round(x,6):failures.append(x)
        self.assertGreater(len(failures),10)
        self.assertEqual(round(1/128,6),.007812);self.assertEqual(round(3/128,6),.023438)
    def test_zero_sign_is_preserved_in_rounding_but_normalized_in_keys(self):
        for x in [-0.,-1e-300,-4.9e-7]:
            r=a.native_reference(a.bits(x));self.assertEqual(r['rounded_bits'],1<<63);self.assertEqual(r['key_bits'],0)
    def test_rejection_status_uses_shared_transport_contract(self):
        a.validate_rejection([64,0,0,0,0,0],'reject/round-six/nonfinite')
        with self.assertRaises(AssertionError):a.validate_rejection([1,0,0,0,0,0],'reject/round-six/nonfinite')

    def test_comparison_covers_every_output_word(self):
        rows,raw=a.prepare();self.assertEqual(len(raw),4+len(rows)*16)
        for name,w,v in rows[:50]:
            r=a.native_reference(v);x=r['rounded_bits'];k=r['key_bits'];block=[0,x&0xffffffff,x>>32,k&0xffffffff,k>>32,0x43523631];a.compare(block,v)
            for at in range(6):
                changed=list(block);changed[at]^=1
                with self.assertRaises(AssertionError):a.compare(changed,v)
if __name__=='__main__':unittest.main()
