import sys,unittest,importlib.util,math
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_landing_v1 as l
import portable_coordinate_numeric_v1 as n
from portable_coordinate_landing_cases import fixtures
from coordinate_landing_reference import landing
from coordinate_power_accuracy import mpfr
s=importlib.util.spec_from_file_location('landing_adapter',ROOT/'research/verify-coordinate-landing-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class LandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=dict(fixtures());cls.results={name:landing(case) for name,case in cls.cases.items()}
    def test_schema_capacity_accounts_for_all_breaks_without_clipping(self):
        l.check_schema(ROOT);l.check_arc_references(ROOT);l.check_prepared_arcs(ROOT);self.assertEqual(l.CUTS,127*(16+24)+16+2);self.assertEqual(l.PREP_OFFSET,l.CUT_OFFSET+2*l.CUTS);self.assertEqual(l.OUTPUT,l.PREP_OFFSET+l.SHAPES*l.PREP_WORDS)
        e=self.results['maximum-target-count'];self.assertEqual(len(e['front']),127);self.assertEqual(e['near_count'],127);self.assertTrue(all(value==0 for value in e['front'][1:]))
        source=(ROOT/'gpu/coordinate_landing_v1.slang').read_text()
        self.assertNotIn('cuts[CL_CUTS]',source)
        self.assertIn('output+CL_CUT_OFFSET+index*2',source)
    def test_analytic_center_core_and_target_probabilities(self):
        for k in [.5,1.,2.,2.55,4.,2.**-16,65536.]:
            e=self.results['center-core/'+str(k)];self.assertEqual(n.bits(e['core_open']),mpfr(n.bits(.5),n.bits(k)));self.assertEqual(e['core_open'],e['core_under']);self.assertEqual(e['nodes'],0)
        e=self.results['center-target'];self.assertLess(abs(e['front'][0]-n.number(mpfr(n.bits(.5),n.bits(2.55)))),1e-15)
        self.assertEqual(self.results['covered-core']['core_open'],0.);self.assertEqual(self.results['full-cover']['front'],[1.])
        self.assertEqual(self.results['full-cover']['core_under'],1.);self.assertEqual(self.results['full-cover']['core_open'],0.)
    def test_probability_bounds_occlusion_and_reach(self):
        for name,e in self.results.items():
            self.assertTrue(all(0<=v<=1 for v in [*e['front'],*e['reach'],e['core_open'],e['core_under']]),name)
            self.assertLessEqual(sum(e['front'])+e['core_open'],1+1e-14,name)
            self.assertLessEqual(e['core_open'],e['core_under']+1e-14,name)
            if self.cases[name]['grow']>0:
                self.assertTrue(all(front<=reach+1e-14 for front,reach in zip(e['front'],e['reach'])),name)
        f,r=(self.results[name] for name in ('depth-forward','depth-reversed'))
        self.assertNotAlmostEqual(f['front'][0],r['front'][1],places=8)
        self.assertAlmostEqual(f['core_open'],r['core_open'],places=14)
    def test_partition_order_and_grow_are_observed(self):
        for name,e in self.results.items():
            self.assertEqual(e['cuts'],sorted(set(e['cuts'])),name)
            self.assertEqual(e['nodes']%10,0,name)
        self.assertGreater(len(self.results['rectangle/grow-0.5']['cuts']),len(self.results['rectangle/grow-0.0']['cuts']))
        # More cuts change the quadrature approximation slightly even for
        # front probability; forcing identical values would alter the model.
        self.assertNotEqual(self.results['rectangle/grow-0.5']['front'],self.results['rectangle/grow-0.0']['front'])
    def test_historical_native_model_fidelity_on_authored_worlds(self):
        import engine_worker
        from calculator.aim import Shape,landing as native
        for name,case in self.cases.items():
            convert=lambda s:Shape(x=s[1],y=s[2],r=s[3],w=s[4],h=s[5],rot=s[6])
            e=self.results[name];old=native(*case['aim'],case['radius'],[convert(s) for s in case['targets']],convert(case['core']) if case['core'] else None,case['grow'],case['k'])
            for actual,expected in zip([*e['front'],*e['reach'],e['core_open'],e['core_under']],[*old.front,*old.reach,old.core_open,old.core_under]):self.assertLess(abs(actual-expected),1e-12,name)
    def test_packing_has_no_probability_evaluation_and_negative_k_is_invalid(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No landing packing')):rows,raw=a.prepare()
        self.assertEqual((len(rows),len(raw)),(40,4+40*l.INPUT*4));self.assertEqual(sum(d is None for _,_,d in rows),14)
        bad=dict(self.cases['empty'],k=0.)
        with self.assertRaises(ValueError):landing(bad)
        low=next(w for name,w,d in rows if name=='reject/coordinate-landing/k-low');self.assertLess(n.number(low[12]|low[13]<<32),n.number(l.CONSTANTS['MIN_K']))
    def test_full_output_cuts_and_padding_are_compared(self):
        domain=self.cases['depth-forward'];w,e=a.expected(domain);a.compare(w,domain)
        for at in [0,4,6,8,9,10,12,13,16,270,l.CUT_OFFSET,l.OUTPUT-1]:
            other=list(w);other[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(other,domain)
if __name__=='__main__':unittest.main()
