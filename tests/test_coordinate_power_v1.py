import sys,unittest,math,hashlib,importlib.util
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_power_v1 as p
import portable_coordinate_quadrature_v1 as q
from coordinate_power_accuracy import audit,mpfr
s=importlib.util.spec_from_file_location('power_adapter',ROOT/'research/verify-coordinate-power-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class PowerTests(unittest.TestCase):
    def test_generator_binds_and_reuses_certified_algorithm(self):
        p.check_schema(ROOT);self.assertEqual(hashlib.sha256((ROOT/'gpu/core_probability.slang').read_bytes()).hexdigest(),p.SOURCE_SHA256)
    def test_mpfr_independent_directed_reference(self):self.assertTrue(audit(ROOT,128)['accuracy_verified'])
    def test_exact_cases_and_underflow(self):
        for x,y,answer in [(.25,.5,.5),(.5,2.,.25),(1.,65536.,1.),(0.,2.55,0.),(.5,65536.,0.)]:self.assertEqual(p.evaluate(p.bits(x),p.bits(y)),p.bits(answer))
        self.assertEqual(p.evaluate(1,p.ONE),1);self.assertEqual(p.evaluate(1<<63,p.ONE),0)
    def test_exponent_representation_and_scale_bound(self):
        for y in [p.MIN_EXPONENT,p.MIN_EXPONENT+1,p.MAX_EXPONENT-1,p.MAX_EXPONENT]:self.assertEqual((Fraction(p.number(y))*p.Q).denominator,1)
        self.assertLess(1074*Fraction(p.LN2+1,p.Q)*65536,(1<<27)*Fraction(p.LN2,p.Q))
    def test_reject_domain_without_fallback(self):
        for x,y in [(p.ONE+1,p.ONE),(p.bits(-.5),p.ONE),(p.ONE,0),(p.ONE,p.MIN_EXPONENT-1),(p.ONE,p.MAX_EXPONENT+1)]:
            with self.assertRaises(ValueError):p.evaluate(x,y)
    def test_static_packing_no_pow_and_whole_output_check(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No power packing')),patch.object(math,'pow',side_effect=AssertionError('No host power packing')):rows,raw=a.prepare()
        self.assertEqual((len(rows),len(raw)),(909,4+909*8*4));w=[0,0x43505631,*a.words64(p.bits(.5)),0,0,0,0];a.compare(w,(p.bits(.25),p.bits(.5)))
        for at in [0,2,3,7]:
            changed=list(w);changed[at]^=1
            with self.assertRaises(AssertionError):a.compare(changed,(p.bits(.25),p.bits(.5)))
    def test_quadrature_source_symmetry_and_rational_root_brackets(self):
        q.check_schema(ROOT);nodes=q.nodes();self.assertEqual(len(nodes),10)
        def legendre(x):
            a,b=Fraction(1),x
            for k in range(2,11):a,b=b,((2*k-1)*x*b-(k-1)*a)/k
            return b
        for i,(x,w) in enumerate(nodes):
            self.assertEqual(nodes[9-i],(x^(1<<63),w));self.assertGreater(p.number(w),0)
            low=Fraction(math.nextafter(p.number(x),-math.inf));high=Fraction(math.nextafter(p.number(x),math.inf))
            self.assertLess(legendre(low)*legendre(high),0)
    def test_quadrature_integrates_all_monomials_through_degree19(self):
        for k in range(20):
            observed=sum((Fraction(p.number(w))*Fraction(p.number(x))**k for x,w in q.nodes()),Fraction())
            exact=Fraction(0) if k&1 else Fraction(2,k+1)
            self.assertLess(abs(observed-exact),Fraction(1,10**15),(k,observed-exact))
if __name__=='__main__':unittest.main()
