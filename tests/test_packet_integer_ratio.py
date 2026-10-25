import importlib.util,math,sys,unittest
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('ratio_adapter',ROOT/'research/verify-packet-ratio-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class RatioTests(unittest.TestCase):
    def test_python_exact_ratio_agrees_with_independent_decimal_rounding(self):
        with localcontext() as ctx:
            ctx.prec=200
            for _,n,d in a.fixtures():self.assertEqual(float(Fraction(n,d)),float(Decimal(n)/Decimal(d)))
    def test_converting_integer_before_division_really_changes_results(self):
        examples=[]
        for d in [3,5,7]:
            for offset in range(1,50):
                n=2**53+offset
                if float(n)/d!=float(Fraction(n,d)):examples.append((n,d))
        self.assertTrue(examples);self.assertEqual({d for _,d in examples},{3,5,7})
    def test_every_bounded_divisor_zero_fraction_high128_and_ties_are_present(self):
        rows=a.fixtures();self.assertEqual({d for _,n,d in rows},set(range(1,1025)));self.assertTrue(any(n==2**128-1 for _,n,d in rows));self.assertTrue(any(0<n<d for _,n,d in rows))
        self.assertEqual(float(Fraction(2**53+1,1)),float(2**53));self.assertEqual(float(Fraction(2**53+3,1)),float(2**53+4))
    def test_authored_integer_wire_and_complete_output_corruption(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle packing')):rows,raw=a.prepare()
        self.assertEqual(len(raw),4+len(rows)*8*4)
        domain=(2**128-1,7);e=a.native_reference(domain);b=[0,a.MAGIC,7,0,*e['bits'],0,0];a.compare(b,domain)
        for at in range(8):
            c=list(b);c[at]^=1
            with self.assertRaises(AssertionError):a.compare(c,domain)
if __name__=='__main__':unittest.main()
