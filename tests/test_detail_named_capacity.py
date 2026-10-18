import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('named_capacity_test',ROOT/'scripts/verify-named-capacity-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class NamedCapacityTests(unittest.TestCase):
    def test_every_boundary_in_all_eight_words_and_pinned_cpu_reference(self):
        self.assertEqual(v.g.EXTEND_MASK+v.g.MASK_WORDS,v.g.EW)
        self.assertLessEqual(v.g.REDUCER_MASK+v.g.MASK_WORDS,v.g.EXTEND_MASK)
        stats={n:{'atk':100000,'def':20000,'hp':1000000} for n in v.v.NAMES}
        cases=list(v.primitives());self.assertEqual(len(cases),32)
        for name,p,script,expected in cases:
            with self.subTest(name=name):
                cpu,_=v.v.oracle.oracle(p,script,[31784,0],stats)
                self.assertEqual([q[0] for q in cpu],expected)
    def test_257_named_states_reject_without_index_error(self):
        _,p,_,_=list(v.primitives())[-1]
        effects=copy.deepcopy(p['_raw_effects'])
        effects[0][0]['trigger']['condition'].append('gauge_above:extra-state:1')
        with self.assertRaises(v.g.UnsupportedDetail):v.g.compile_effects(copy.deepcopy(p['chars']),effects)
    def test_all_boundary_queries_match_independent_cpu_on_native(self):
        device=v.Cuda()
        try:rows=v.verify_primitives(device,'native')
        finally:device.close()
        self.assertEqual(len(rows),32);self.assertTrue(all(r['passed'] for r in rows))
if __name__=='__main__':unittest.main()
