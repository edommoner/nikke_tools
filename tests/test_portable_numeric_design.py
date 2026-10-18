from fractions import Fraction
import math
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]


class NumericIntervalCertificateTests(unittest.TestCase):
    def test_ln2_constant_is_enclosed_by_independent_rational_bounds(self):
        source=(ROOT/'gpu/core_probability.slang').read_text()
        limbs={int(i):int(v,0) for i,v in re.findall(r'ln2\.lo\.limb\[(\d+)\] = (0x[0-9a-f]+|[0-9]+)',source)}
        integer=sum(v<<(32*i) for i,v in limbs.items())
        lower=Fraction(integer,2**128);upper=Fraction(integer+1,2**128)
        # ln(2)=2*atanh(1/3), with exact rational bounds, not host libm.
        series=2*sum((Fraction(1,(2*k+1)*3**(2*k+1)) for k in range(128)),Fraction())
        tail=Fraction(2,257*3**257)*Fraction(9,8)
        self.assertLessEqual(lower,series)
        self.assertLess(series+tail,upper)

    def test_truncation_remainders_and_binary_exponent_are_bounded(self):
        self.assertLess(Fraction(2,129*3**129)*Fraction(9,8),Fraction(1,2**128))
        self.assertLess(Fraction(1,math.factorial(48)),Fraction(1,2**128))
        source=(ROOT/'gpu/core_probability.slang').read_text()
        limbs={int(i):int(v,0) for i,v in re.findall(r'y\.lo\.limb\[(\d+)\] = (0x[0-9a-f]+|[0-9]+)',source)}
        self.assertEqual(sum(v<<(32*i) for i,v in limbs.items()),Fraction(2.55)*2**128)
        self.assertNotEqual(Fraction(2.55),Fraction(51,20))


if __name__=='__main__':unittest.main()
