"""Frozen allocation arithmetic and boundaries, independent of battle scheduling."""
import importlib.util,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from incoming_weighted_allocation import allocate
spec=importlib.util.spec_from_file_location('weighted_adapter',ROOT/'research/verify-weighted-incoming.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class WeightedIncoming(unittest.TestCase):
    def test_five_bodies_without_cover_and_survivor_normalization(self):
        self.assertEqual(allocate(100.,31,0,8.,3.,262.,False)['shares'],[40.,15.,15.,15.,15.,0.])
        # A dead caster has no body or orphan cover, not a phantom weight8.
        self.assertEqual(allocate(99.,30,0,8.,3.,262.,False)['shares'],[0.,24.75,24.75,24.75,24.75,0.])
        self.assertEqual(allocate(99.,1,0,8.,3.,262.,False)['shares'],[99.,0.,0.,0.,0.,0.])

    def test_cover_is_separate_receiver_and_explicit_weight_not_magic_constant(self):
        r=allocate(282.,31,2,8.,3.,262.,True)
        self.assertEqual(r['active_mask'],63);self.assertEqual(r['total'],282.)
        self.assertEqual(r['shares'],[282.*(3./282.),282.*(3./282.),282.*(8./282.),282.*(3./282.),282.*(3./282.),282.*(262./282.)])
        r=allocate(12.,31,2,1.,1.,1.,True)
        self.assertEqual(r['shares'],[2.]*6)
        with self.assertRaises(ValueError):allocate(10.,1,1,8.,3.,262.,True)

    def test_divide_before_multiply_no_floor_no_integer_or_residual_adjustment(self):
        r=allocate(1e308,31,0,8.,3.,262.,False)
        self.assertEqual(r['status'],0);self.assertTrue(all(math.isfinite(x) for x in r['shares']))
        r=allocate(1.,31,0,8.,3.,262.,False)
        self.assertEqual(r['shares'],[.4,.15,.15,.15,.15,0.])
        self.assertEqual(allocate(5e-324,31,0,8.,3.,262.,False)['shares'],[0.]*6)
        self.assertEqual(allocate(0.,31,0,8.,3.,262.,True)['shares'],[0.]*6)
        r=allocate(100.,31,0,1e308,1e308,1e308,True)
        self.assertEqual(r,dict(status=16,active_mask=63,total=None,shares=None))

    def test_invalid_boundary_types_and_nonfinite_are_rejected(self):
        args=[1.,31,0,8.,3.,262.,False]
        for at,value in [(0,-1.),(0,True),(0,math.nan),(1,True),(1,0),(1,32),(2,True),(2,5),(3,0.),(4,-1.),(5,math.inf),(6,1)]:
            bad=list(args);bad[at]=value
            with self.assertRaises(ValueError):allocate(*bad)

    def test_every_live_mask_slot_cover_and_extreme_has_a_strict_full_word_oracle(self):
        rows,data=adapter.prepare();valid=[d[0] for _,_,d in rows if d is not None]
        self.assertEqual(len(valid),1179);self.assertEqual(len(rows),1192)
        self.assertEqual(len(data),4+16*4*len(rows))
        self.assertEqual({c['args'][1] for c in valid},set(range(1,32)))
        for _,_,domain in rows:
            if domain is None:continue
            n=adapter.native_reference(domain)
            block=[0,adapter.MAGIC,n['status'],n['active_mask'],*adapter.words([n['total'],*n['shares']] if n['status']==0 else [0.]*7),0,0]
            adapter.compare(block,domain)
        domain=rows[0][2];n=adapter.native_reference(domain)
        good=[0,adapter.MAGIC,0,n['active_mask'],*adapter.words([n['total'],*n['shares']]),0,0]
        for at in (2,3,4,6,16,19):
            bad=list(good);bad[at]^=1
            with self.assertRaises(AssertionError):adapter.compare(bad,domain)

if __name__=='__main__':unittest.main()
