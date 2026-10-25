import copy,random,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_coordinate_sampling_cases import fixtures
from portable_coordinate_sampling_contracts import verify
from world_coordinate_sampling_native import observe,common_sampling_policy
class ReferenceTests(unittest.TestCase):
    def test_native_integer_draws_are_replayed_without_double_counting_points(self):
        saved=random.getstate();original=random.Random.getrandbits;draws=[]
        try:
            with common_sampling_policy([],draws):
                random.seed(7);random.sample(range(5),2);state=random.getstate()[1]
            self.assertIs(random.Random.getrandbits,original)
            self.assertTrue(draws);self.assertTrue(all(r['kind']=='native-bits' for r in draws))
            native=dict(reference_kind='deterministic-common-cpu',sampled_points=[],physical_pellets=[],sampled_draws=draws,physical_rng=dict(index=state[-1],state=list(state[:-1])))
            self.assertTrue(verify(dict(seed=7,name='test/selector-only'),native)['verified'])
            bad=copy.deepcopy(native);bad['sampled_draws'][0]['value']^=1
            with self.assertRaises(AssertionError):verify(dict(seed=7,name='test/selector-only'),bad)
        finally:random.setstate(saved)

    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers=[observe(c)[0] for c in cls.cases]
    def test_canonical_sampled_battles_and_exact_physical_rng_state(self):
        self.assertEqual(len(self.cases),11)
        for c,n in zip(self.cases,self.answers,strict=True):self.assertTrue(verify(c,n)['verified'])
        self.assertEqual(self.cases,self.before)
    def test_passive_sample_capture_preserves_full_battle_and_packets(self):
        from world_coordinate_physical_native import observe as physical
        with common_sampling_policy():base=physical(self.cases[3])
        self.assertEqual({k:self.answers[3][k] for k in base if k!='scope'},{k:v for k,v in base.items() if k!='scope'})
    def test_patch_and_process_rng_are_restored(self):
        from calculator import aim,timeline
        before=(aim.Shape.dist,timeline.simulate,timeline.sample_landing,random.getstate());observe(self.cases[0]);self.assertEqual(before,(aim.Shape.dist,timeline.simulate,timeline.sample_landing,random.getstate()))
    def test_critical_override_and_rng_corruption_rejected(self):
        bad=copy.deepcopy(self.answers[0]);bad['physical_rng']['index']^=1
        with self.assertRaises(AssertionError):verify(self.cases[0],bad)
        bad=copy.deepcopy(self.answers[6]);p=next(r for r in bad['physical_pellets'] if len(r['packets'])>1);p['packets'][1]['is_crit']=not p['packets'][0]['is_crit']
        with self.assertRaises(AssertionError):verify(self.cases[6],bad)
if __name__=='__main__':unittest.main()
